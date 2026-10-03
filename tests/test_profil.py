"""Filtrage par profil (§13) : `scripts/modules.py` et `obsia.local.yml`.

Sans `obsia.local.yml`, rien n'est filtré : c'est l'état du dépôt de
distribution, et celui sous lequel la CI vérifie le coffre. Avec un profil,
seuls les modules retenus restent actifs — plus, toujours, les modules
essentiels et ce que les retenus déclarent dans `requiert`.

Ce que ces tests protègent : un profil qui écarte un module ne doit pas
laisser un agent ou un skill citer un fichier absent du coffre.

Le filtrage ne s'applique qu'à ce qui n'est pas versionné — le prompt système
et `AGENTS.md`. Les index versionnés (`IA/system/*-index.md`, `IA/README.md`)
ne se réduisent jamais au profil : c'est `test_regenerate_index.py` qui le
garantit.

Chaque test écrit dans un coffre temporaire ; le coffre réel n'est jamais lu.
"""

import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))        # `scripts/` n'est pas un paquet

from generer_prompt import (           # noqa: E402
    collecter,
    filtrer_par_profil,
    reduire_aux_actifs,
)
from modules import (                   # noqa: E402
    ecrire_profil,
    lire_modules,
    lire_profil,
    modules_actifs,
    modules_inconnus,
    resoudre_dependances,
    signaler_modules_inconnus,
)

# Le catalogue de référence des tests :
#
#   noyau            essentiel
#   construction     requiert noyau
#   conteneurs       (rien)
#   administration-homelab  requiert conteneurs
#   exemple-cite     requiert un module qui n'existe pas
MODULES = {
    "noyau": "essentiel: true",
    "construction": "essentiel: false\nrequiert:\n  - noyau",
    "conteneurs": "essentiel: false",
    "administration-homelab": "essentiel: false\nrequiert:\n  - conteneurs",
    "exemple-cite": "essentiel: false\nrequiert:\n  - absent-du-catalogue",
}

AGENTS = {
    "a-construction": "module: construction\n"
                      "skills:\n  - s-construction\n  - s-conteneurs\n"
                      "mcp:\n  - bruno",
    "a-administration": "module: administration-homelab",
}

# s-admin est en forme dossier : le filtrage doit voir les deux formes.
SKILLS_PLATS = {
    "s-construction": "module: construction",
    "s-conteneurs": "module: conteneurs",
}
SKILL_DOSSIER = ("s-admin", "module: administration-homelab")


class BaseCoffreProfil(unittest.TestCase):
    """Un coffre temporaire peuplé du catalogue de référence."""

    def setUp(self):
        self.racine = Path(tempfile.mkdtemp(prefix="obsia-test-profil-"))
        self.addCleanup(shutil.rmtree, self.racine, ignore_errors=True)

        for nom, reste in MODULES.items():
            self.ecrire(f"IA/system/modules/{nom}.md",
                        f"---\nschema: 1\nkind: module\nname: {nom}\n"
                        f"description: Module {nom}.\n{reste}\n---\n")

        for nom, reste in AGENTS.items():
            self.ecrire(f"IA/agents/{nom}.md",
                        f"---\nschema: 1\nkind: agent\nname: {nom}\n"
                        f"description: Agent {nom}.\n{reste}\n---\n")

        for nom, reste in SKILLS_PLATS.items():
            self.ecrire(f"IA/skills/{nom}.md",
                        f"---\nschema: 1\nkind: skill\nname: {nom}\n"
                        f"description: Skill {nom}.\n{reste}\n---\n")

        nom, reste = SKILL_DOSSIER
        self.ecrire(f"IA/skills/{nom}/{nom}.md",
                    f"---\nschema: 1\nkind: skill\nname: {nom}\n"
                    f"description: Skill {nom}.\n{reste}\n---\n")

    def ecrire(self, relatif: str, contenu: str) -> Path:
        chemin = self.racine / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")
        return chemin

    def ecrire_profil_brut(self, contenu: str) -> Path:
        """Un `obsia.local.yml` écrit à la main, comme un humain le retoucherait."""
        return self.ecrire("obsia.local.yml", contenu)

    def noms(self, entrees) -> list[str]:
        return sorted(e["name"] for e in entrees)

    def agents(self) -> list[dict]:
        with redirect_stderr(StringIO()):
            return collecter(self.racine / "IA" / "agents", "agent")

    def skills(self) -> list[dict]:
        with redirect_stderr(StringIO()):
            return collecter(self.racine / "IA" / "skills", "skill")


class TestCatalogueDeReference(BaseCoffreProfil):
    """Le décor des tests : s'il bouge, les tests suivants ne veulent rien dire."""

    def test_tout_est_lu(self):
        self.assertEqual(sorted(m["name"] for m in lire_modules(self.racine)),
                         sorted(MODULES))
        self.assertEqual(self.noms(self.agents()), sorted(AGENTS))
        self.assertEqual(self.noms(self.skills()),
                         sorted(list(SKILLS_PLATS) + [SKILL_DOSSIER[0]]))

    def test_les_essentiels_viennent_en_tete(self):
        """L'ordre du catalogue : les essentiels d'abord, puis par nom."""
        self.assertEqual([m["name"] for m in lire_modules(self.racine)],
                         ["noyau", "administration-homelab", "construction",
                          "conteneurs", "exemple-cite"])


class TestSansProfil(BaseCoffreProfil):
    """Pas de profil = catalogue complet. C'est l'état de la CI."""

    def test_lire_profil_rend_none(self):
        self.assertIsNone(lire_profil(self.racine))

    def test_modules_actifs_rend_none(self):
        self.assertIsNone(modules_actifs(self.racine))

    def test_rien_nest_filtre(self):
        agents, skills = self.agents(), self.skills()

        filtres_agents, filtres_skills = filtrer_par_profil(
            self.racine, agents, skills)

        self.assertEqual(self.noms(filtres_agents), self.noms(agents))
        self.assertEqual(self.noms(filtres_skills), self.noms(skills))


class TestResolution(BaseCoffreProfil):
    """`resoudre_dependances` : la fermeture sur `requiert`, plus les essentiels."""

    def test_ajoute_toujours_les_essentiels(self):
        resolu = resoudre_dependances(lire_modules(self.racine), [])

        self.assertEqual(resolu, {"noyau"})

    def test_ferme_la_selection_sur_requiert(self):
        resolu = resoudre_dependances(
            lire_modules(self.racine), {"administration-homelab"})

        self.assertEqual(resolu, {"noyau", "administration-homelab", "conteneurs"})

    def test_ferme_en_profondeur(self):
        """Les dépendances des dépendances sont ajoutées aussi."""
        modules = [
            {"name": "a", "essentiel": False, "requiert": ["b"]},
            {"name": "b", "essentiel": False, "requiert": ["c"]},
            {"name": "c", "essentiel": False, "requiert": []},
        ]

        self.assertEqual(resoudre_dependances(modules, {"a"}), {"a", "b", "c"})

    def test_une_dependance_inconnue_est_ignoree(self):
        """Le nom absent du catalogue n'est pas inventé : il est écarté."""
        resolu = resoudre_dependances(
            lire_modules(self.racine), {"exemple-cite"})

        self.assertEqual(resolu, {"noyau", "exemple-cite"})

    def test_un_module_inconnu_dans_le_profil_est_signale_sans_etre_fatal(self):
        """Un nom hors catalogue avertit, mais ne fait pas échouer la génération.

        Le nom reste sans effet — rien ne le déclare — et n'est pas une erreur :
        un profil peut citer un module qu'une version ultérieure apportera.
        Sans le signal, un profil fautif (« constructionn ») resterait muet.
        """
        self.ecrire_profil_brut("schema: 1\nmodules:\n  - pas-au-catalogue\n")
        err = StringIO()

        with redirect_stderr(err):
            actifs = modules_actifs(self.racine)

        self.assertEqual(actifs, {"noyau", "pas-au-catalogue"})
        self.assertIn("pas-au-catalogue", err.getvalue())


class TestModulesInconnus(BaseCoffreProfil):
    """§13 : un profil qui cite un module absent du catalogue doit se voir."""

    def test_le_nom_hors_catalogue_est_signale(self):
        err = StringIO()

        with redirect_stderr(err):
            signaler_modules_inconnus(lire_modules(self.racine),
                                      {"construction", "pas-au-catalogue"})

        self.assertIn("pas-au-catalogue", err.getvalue())
        self.assertNotIn("construction", err.getvalue().split("—")[0])

    def test_un_profil_hors_catalogue_est_signale_un_par_un(self):
        err = StringIO()

        with redirect_stderr(err):
            signaler_modules_inconnus(lire_modules(self.racine),
                                      {"inconnu-a", "inconnu-b"})

        sortie = err.getvalue()
        self.assertIn("inconnu-a", sortie)
        self.assertIn("inconnu-b", sortie)
        self.assertEqual(sortie.count("Modules inconnus"), 1)

    def test_aucun_nom_hors_catalogue_n_ecrit_rien(self):
        """Pas de faux positif : un profil juste reste silencieux."""
        err = StringIO()

        with redirect_stderr(err):
            signaler_modules_inconnus(lire_modules(self.racine),
                                      {"construction", "conteneurs"})

        self.assertEqual(err.getvalue(), "")

    def test_le_catalogue_est_rappele(self):
        """L'avertissement nomme les noms connus : on corrige sans relire l'index."""
        err = StringIO()

        with redirect_stderr(err):
            signaler_modules_inconnus(lire_modules(self.racine), {"inconnu"})

        self.assertIn("construction", err.getvalue())

    def test_un_module_essentiel_n_inverse_rien(self):
        """Le noyau est dans le catalogue : rien à signaler."""
        err = StringIO()

        with redirect_stderr(err):
            signaler_modules_inconnus(lire_modules(self.racine), {"noyau"})

        self.assertEqual(err.getvalue(), "")

    def test_modules_inconnus_ne_rend_que_les_inconnus(self):
        modules = lire_modules(self.racine)

        self.assertEqual(modules_inconnus(modules, {"construction", "absent"}),
                         {"absent"})
        self.assertEqual(modules_inconnus(modules, {"construction"}), set())


class TestAvecProfil(BaseCoffreProfil):
    """Un profil présent : les modules retenus décident de l'index."""

    def test_modules_actifs(self):
        self.ecrire_profil_brut(
            "schema: 1\nmodules:\n  - administration-homelab\n")

        self.assertEqual(modules_actifs(self.racine),
                         {"noyau", "administration-homelab", "conteneurs"})

    def test_profil_vide_ne_garde_que_lessentiel(self):
        self.ecrire_profil_brut("schema: 1\nmode: en-place\n")

        self.assertEqual(modules_actifs(self.racine), {"noyau"})

    def test_filtre_ecarte_les_modules_non_retenus(self):
        """Un module écarté disparaît de l'index, et ses dépendances restent."""
        self.ecrire_profil_brut(
            "schema: 1\nmodules:\n  - administration-homelab\n")

        agents, skills = filtrer_par_profil(self.racine, self.agents(),
                                            self.skills())

        self.assertEqual(self.noms(agents), ["a-administration"])
        self.assertEqual(self.noms(skills), ["s-admin", "s-conteneurs"])

    def test_filtre_garde_le_module_retenu_et_ses_dependances(self):
        self.ecrire_profil_brut("schema: 1\nmodules:\n  - construction\n")

        agents, skills = filtrer_par_profil(self.racine, self.agents(),
                                            self.skills())

        self.assertEqual(self.noms(agents), ["a-construction"])
        self.assertEqual(self.noms(skills), ["s-construction"])

    def test_les_deux_formes_de_skill_sont_filtrees_pareil(self):
        """Forme plate et forme dossier tombent sous le même filtre."""
        self.ecrire_profil_brut("schema: 1\nmodules:\n  - conteneurs\n")

        (skills,) = filtrer_par_profil(self.racine, self.skills())

        self.assertEqual(self.noms(skills), ["s-conteneurs"])


class TestMCPDeclareSansModule(BaseCoffreProfil):
    """Caractérisation : un MCP sans `module:` disparaît dès qu'un profil existe.

    Le §13 exige un `module:` sur toute fiche — les fiches réelles en ont un.
    Mais rien ne le vérifie : la fiche se tait, et le serveur MCP sort de
    l'index sans un mot. C'est le comportement actuel ; le test le fige pour
    qu'un changement soit vu.
    """

    def test_le_mcp_sans_module_est_ecarte_avec_un_profil(self):
        self.ecrire("IA/MCP/bruno.md",
                    "---\nschema: 1\nkind: mcp\nname: bruno\n"
                    "description: Sans module déclaré.\n---\n")
        with redirect_stderr(StringIO()):
            mcp = collecter(self.racine / "IA" / "MCP", "mcp")
        self.ecrire_profil_brut("schema: 1\nmodules:\n  - construction\n")

        (filtres,) = filtrer_par_profil(self.racine, mcp)

        self.assertEqual(filtres, [])

    def test_le_mcp_sans_module_survit_sans_profil(self):
        self.ecrire("IA/MCP/bruno.md",
                    "---\nschema: 1\nkind: mcp\nname: bruno\n"
                    "description: Sans module déclaré.\n---\n")
        with redirect_stderr(StringIO()):
            mcp = collecter(self.racine / "IA" / "MCP", "mcp")

        (filtres,) = filtrer_par_profil(self.racine, mcp)

        self.assertEqual(self.noms(filtres), ["bruno"])


class TestReduireAuxActifs(BaseCoffreProfil):
    """Un skill ou un MCP écarté ne doit pas rester cité par un agent retenu."""

    def test_retire_les_skills_absents_de_lindex(self):
        agents = [{"name": "a", "skills": ["s-construction", "s-conteneurs"],
                   "mcp": []}]

        reduire_aux_actifs(agents, [{"name": "s-construction"}], set())

        self.assertEqual(agents[0]["skills"], ["s-construction"])

    def test_retire_les_mcp_absents_de_lindex(self):
        agents = [{"name": "a", "skills": [], "mcp": ["bruno", "inconnu"]}]

        reduire_aux_actifs(agents, [], {"bruno"})

        self.assertEqual(agents[0]["mcp"], ["bruno"])

    def test_garde_ce_qui_est_dans_lindex(self):
        agents = [{"name": "a", "skills": ["s-construction", "s-conteneurs"],
                   "mcp": ["bruno"]}]

        reduire_aux_actifs(agents, [{"name": "s-construction"},
                                    {"name": "s-conteneurs"}], {"bruno"})

        self.assertEqual(sorted(agents[0]["skills"]),
                         ["s-construction", "s-conteneurs"])
        self.assertEqual(agents[0]["mcp"], ["bruno"])

    def test_un_agent_sans_skill_ni_mcp_traverse_sans_bruit(self):
        agents = [{"name": "a", "skills": [], "mcp": []}]

        reduire_aux_actifs(agents, [], set())

        self.assertEqual(agents, [{"name": "a", "skills": [], "mcp": []}])

    def test_apres_filtrage_par_profil(self):
        """Le cas d'usage réel : le profil écarte un skill, l'agent suit."""
        self.ecrire_profil_brut("schema: 1\nmodules:\n  - construction\n")
        agents, skills = filtrer_par_profil(self.racine, self.agents(),
                                            self.skills())

        reduire_aux_actifs(agents, skills, set())

        a_construction = [a for a in agents
                          if a["name"] == "a-construction"][0]
        self.assertEqual(a_construction["skills"], ["s-construction"])

    def test_ne_touche_pas_aux_fichiers(self):
        """Réduire l'index est une vue : le skill écarté reste sur le disque."""
        chemin = self.racine / "IA" / "skills" / "s-conteneurs.md"
        avant = chemin.read_bytes()
        self.ecrire_profil_brut("schema: 1\nmodules:\n  - construction\n")
        agents, skills = filtrer_par_profil(self.racine, self.agents(),
                                            self.skills())

        reduire_aux_actifs(agents, skills, set())

        self.assertEqual(chemin.read_bytes(), avant)


class TestAllerRetourDuProfil(BaseCoffreProfil):
    """Ce que `installer.py` écrit, `generer_prompt.py` doit le relire."""

    def test_profil_ecrit_puis_relu(self):
        chemin = ecrire_profil(
            self.racine, {"administration-homelab", "construction"},
            systeme={"distribution": "debian", "gestionnaire_paquets": "apt"},
            mode="en-place", coffre_parent="..")

        self.assertEqual(chemin, self.racine / "obsia.local.yml")

        profil = lire_profil(self.racine)
        # Ordre du catalogue : les essentiels d'abord, puis par nom.
        self.assertEqual(profil["modules"],
                         ["administration-homelab", "construction"])
        self.assertEqual(profil["mode"], "en-place")
        self.assertEqual(profil["coffre_parent"], "..")
        self.assertEqual(profil["distribution"], "debian")
        self.assertEqual(profil["schema"], 1)

    def test_le_profil_ecrit_gouverne_bien_les_modules_actifs(self):
        ecrire_profil(self.racine, {"construction"}, systeme={}, mode="en-place")

        self.assertEqual(modules_actifs(self.racine), {"noyau", "construction"})

    def test_un_profil_sans_module_reste_relisible(self):
        """`modules:` sans élément vaut liste vide, pas clé manquante."""
        ecrire_profil(self.racine, set(), systeme={}, mode="en-place")

        self.assertEqual(lire_profil(self.racine)["modules"], [])
        self.assertEqual(modules_actifs(self.racine), {"noyau"})


if __name__ == "__main__":
    unittest.main()
