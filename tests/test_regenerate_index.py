"""Les index versionnés ne dépendent pas du profil (§13).

`scripts/regenerate_index.py` produit cinq fichiers **versionnés** :
`IA/system/agents-index.md`, `skills-index.md`, `taches-index.md`,
`modules-index.md` et `IA/README.md`. Ils décrivent le catalogue entier,
jamais un coffre réduit. Deux machines qui ont le même dépôt doivent obtenir
les mêmes octets — avec ou sans `obsia.local.yml`.

Ce que ces tests protègent : qu'un profil ne se glisse pas dans un fichier
suivi par git. Sinon la CI, qui n'a pas de profil, voit un index périmé ; et
la machine qui a réduit son coffre ne peut plus rien committer sans mentir sur
son contenu. Le profil ne réduit que ce qui n'est pas versionné — le prompt
système et `AGENTS.md`.

Chaque test écrit dans un coffre temporaire ; le coffre réel n'est jamais lu.
"""

import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))        # `scripts/` n'est pas un paquet

import regenerate_index as RI           # noqa: E402
from generer_prompt import collecter, filtrer_par_profil   # noqa: E402

# Le petit catalogue du décor — deux modules, dont un seul est retenu plus bas.
MODULES = {
    "noyau": "essentiel: true",
    "construction": "essentiel: false\nrequiert:\n  - noyau",
}
AGENTS = {
    "a-noyau": "module: noyau\nskills:\n  - s-noyau\nmcp:\n  - bruno",
    "a-construction": "module: construction\nskills:\n  - s-construction",
}
SKILLS = {
    "s-noyau": "module: noyau",
    "s-construction": "module: construction",
}

#: Les cinq fichiers versionnés, dans l'ordre où l'index les décrit.
INDEX = (
    "IA/system/agents-index.md",
    "IA/system/skills-index.md",
    "IA/system/taches-index.md",
    "IA/system/modules-index.md",
    "IA/README.md",
)

#: Un profil qui ne retient que `noyau` : il écarte `construction`, son agent,
#: son skill, et laisse `bruno` (un MCP n'appartient à aucun module).
PROFIL = "schema: 1\nmode: en place\nmodules:\n  - noyau\n"


class BaseCoffreIndex(unittest.TestCase):
    """Un coffre temporaire qui contient de quoi produire les cinq index."""

    def setUp(self):
        self.racine = Path(tempfile.mkdtemp(prefix="obsia-test-index-"))
        self.addCleanup(shutil.rmtree, self.racine, ignore_errors=True)

        self._argv = list(sys.argv)
        self._racine = RI.RACINE
        self.addCleanup(self._restaurer)

        for nom, reste in MODULES.items():
            self.ecrire(f"IA/system/modules/{nom}.md",
                        f"---\nschema: 1\nkind: module\nname: {nom}\n"
                        f"description: Module {nom}.\n{reste}\n---\n")
        for nom, reste in AGENTS.items():
            self.ecrire(f"IA/agents/{nom}.md",
                        f"---\nschema: 1\nkind: agent\nname: {nom}\n"
                        f"description: Agent {nom}.\n{reste}\n---\n")
        for nom, reste in SKILLS.items():
            self.ecrire(f"IA/skills/{nom}.md",
                        f"---\nschema: 1\nkind: skill\nname: {nom}\n"
                        f"description: Skill {nom}.\n{reste}\n---\n")
        self.ecrire("IA/MCP/bruno.md",
                    "---\nschema: 1\nkind: mcp\nname: bruno\n"
                    "description: MCP bruno.\n---\n")
        self.ecrire("IA/tâches/revue.md",
                    "---\nschema: 1\nkind: tâche\nname: revue\n"
                    "description: Tâche revue.\n---\n")

    def _restaurer(self):
        RI.RACINE = self._racine
        sys.argv = self._argv

    def ecrire(self, relatif: str, contenu: str) -> Path:
        chemin = self.racine / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")
        return chemin

    def generer(self, verifier: bool = False) -> tuple[int, str]:
        """Lance `regenerate_index.py` sur le coffre temporaire, en mémoire."""
        RI.RACINE = self.racine
        sys.argv = ["regenerate_index.py"] + (["--verifier"] if verifier else [])
        err = StringIO()
        with redirect_stderr(err):
            code = RI.main()
        return code, err.getvalue()

    def lire_index(self) -> dict[str, str]:
        return {rel: (self.racine / rel).read_text(encoding="utf-8")
                for rel in INDEX}


class TestProfilIgnoreParLesIndex(BaseCoffreIndex):
    """Le cœur : le profil ne change pas un octet des cinq index."""

    def test_le_profil_ecarte_bien_des_declarations(self):
        """Contrôle du décor : sans filtrage effectif, le test suivant serait creux."""
        self.ecrire("obsia.local.yml", PROFIL)
        err = StringIO()
        with redirect_stderr(err):
            agents = collecter(self.racine / "IA" / "agents", "agent")
            skills = collecter(self.racine / "IA" / "skills", "skill")
            filtres_agents, filtres_skills = filtrer_par_profil(
                self.racine, agents, skills)

        self.assertEqual(sorted(a["name"] for a in filtres_agents), ["a-noyau"])
        self.assertEqual(sorted(s["name"] for s in filtres_skills), ["s-noyau"])

    def test_les_cinq_index_sont_identiques_avec_et_sans_profil(self):
        self.generer()
        sans_profil = self.lire_index()
        self.assertTrue(all(sans_profil.values()),
                        "les index doivent exister et ne pas être vides")

        self.ecrire("obsia.local.yml", PROFIL)
        code, _ = self.generer()
        self.assertEqual(code, 0)
        avec_profil = self.lire_index()

        self.assertEqual(avec_profil, sans_profil)

    def test_le_module_ecarte_par_le_profil_reste_dans_l_index(self):
        """L'index versionné montre tout le catalogue, profil ou pas."""
        self.ecrire("obsia.local.yml", PROFIL)
        self.generer()

        modules_index = self.racine / "IA/system/modules-index.md"
        contenu = modules_index.read_text(encoding="utf-8")

        self.assertIn("[construction](modules/construction.md)", contenu)
        self.assertIn("[noyau](modules/noyau.md)", contenu)

    def test_la_colonne_retenu_ici_a_disparu(self):
        """Une colonne « retenu ici » serait la dépendance à la machine, en dur."""
        self.ecrire("obsia.local.yml", PROFIL)
        self.generer()

        contenu = (self.racine / "IA/system/modules-index.md").read_text(
            encoding="utf-8")

        self.assertNotIn("| Retenu ici |", contenu)


class TestControleAvecProfil(BaseCoffreIndex):
    """`--verifier` est d'accord avec lui-même, profil présent ou non."""

    def test_verifier_ne_signale_rien_apres_generation(self):
        self.ecrire("obsia.local.yml", PROFIL)
        self.generer()

        code, _ = self.generer(verifier=True)

        self.assertEqual(code, 0)

    def test_verifier_detecte_un_index_perime_meme_avec_un_profil(self):
        self.ecrire("obsia.local.yml", PROFIL)
        self.generer()
        (self.racine / "IA/README.md").unlink()

        code, err = self.generer(verifier=True)

        self.assertEqual(code, 1)
        self.assertIn("IA/README.md", err)


class TestLigneDeCommande(BaseCoffreIndex):
    """`--help` affiche l'usage sans rien écrire ; un drapeau inconnu est refusé.

    Même incident que `regenerate_sommaire.py`, corrigé par la PR #179 : le
    script lisait `sys.argv` à la main, donc `--help` — ou une simple faute de
    frappe — passait pour une absence d'option et les cinq index étaient
    réécrits dans l'arbre de travail.
    """

    def executer(self, argv: list[str]) -> tuple[int, str, str]:
        """Lance `main(argv)` et rend `(code, sortie, erreurs)`.

        `argparse` rend la main par `SystemExit` (0 pour `--help`, 2 pour un
        argument refusé) ; un lancement normal retourne un entier.
        """
        RI.RACINE = self.racine
        sortie, erreurs = StringIO(), StringIO()
        with redirect_stdout(sortie), redirect_stderr(erreurs):
            try:
                code = RI.main(argv)
            except SystemExit as sortie_forcee:
                code = sortie_forcee.code
        return code, sortie.getvalue(), erreurs.getvalue()

    def index_ecrits(self) -> list[str]:
        """Les index présents sur le disque après un lancement."""
        return [rel for rel in INDEX if (self.racine / rel).is_file()]

    def test_help_affiche_l_usage_et_n_ecrit_aucun_index(self):
        code, sortie, _ = self.executer(["--help"])

        self.assertEqual(code, 0)
        self.assertIn("usage", sortie.lower())
        self.assertEqual(self.index_ecrits(), [])

    def test_h_court_affiche_l_usage_et_n_ecrit_aucun_index(self):
        code, sortie, _ = self.executer(["-h"])

        self.assertEqual(code, 0)
        self.assertIn("usage", sortie.lower())
        self.assertEqual(self.index_ecrits(), [])

    def test_un_drapeau_inconnu_est_refuse_et_n_ecrit_aucun_index(self):
        """Une faute de frappe ne doit plus réécrire les cinq index."""
        code, _, erreurs = self.executer(["--verfier"])

        self.assertNotEqual(code, 0)
        self.assertIn("--verfier", erreurs)
        self.assertEqual(self.index_ecrits(), [])

    def test_verifier_n_ecrit_rien_meme_quand_un_index_est_perime(self):
        """`--verifier` est un constat, jamais une écriture."""
        self.generer()                                   # index à jour...
        (self.racine / "IA/README.md").unlink()          # ... puis un manquant

        code, _, erreurs = self.executer(["--verifier"])

        self.assertEqual(code, 1)
        self.assertIn("IA/README.md", erreurs)
        self.assertFalse((self.racine / "IA/README.md").exists(),
                         "« --verifier » ne doit pas réécrire l'index manquant")

    def test_sans_option_les_cinq_index_sont_bien_ecrits(self):
        """Témoin : le même décor, sans option, écrit — sinon rien n'est prouvé."""
        code, _, _ = self.executer([])

        self.assertEqual(code, 0)
        self.assertEqual(self.index_ecrits(), list(INDEX))

    def test_l_option_racine_vise_un_autre_coffre(self):
        """`--racine` l'emporte sur la racine du script.

        C'est la couture dont `verifier_coffre.verifier_derives()` a besoin pour
        juger un coffre qui n'est pas celui du produit ; sans elle, le contrôle
        jugeait toujours les index de la machine, quel que soit `--coffre`.
        """
        pas_nous = self.racine.parent / "pas-nous"
        RI.RACINE = pas_nous
        sortie, erreurs = StringIO(), StringIO()
        with redirect_stdout(sortie), redirect_stderr(erreurs):
            code = RI.main(["--racine", str(self.racine)])

        self.assertEqual(code, 0, erreurs.getvalue())
        self.assertEqual(self.index_ecrits(), list(INDEX))
        self.assertFalse(pas_nous.exists(),
                         "rien ne doit atterrir dans la racine du script")


class PremierePhrase(unittest.TestCase):
    """L'index compact ne montre que la première phrase d'une description."""

    def test_coupe_au_premier_point_suivi_d_un_blanc(self):
        self.assertEqual(RI.premiere_phrase("Faire A — `x.md`. À charger quand B."),
                         "Faire A — `x.md`.")

    def test_ne_coupe_pas_dans_un_nom_de_fichier(self):
        self.assertEqual(RI.premiere_phrase("Écrire `docs/PLAN.md` vite. Puis."),
                         "Écrire `docs/PLAN.md` vite.")

    def test_description_sans_point_rendue_entiere(self):
        self.assertEqual(RI.premiere_phrase("  Faire A  "), "Faire A")

    def test_une_abreviation_ne_coupe_pas(self):
        for abrev in ("p. ex.", "cf.", "etc.", "c.-à-d."):
            with self.subTest(abreviation=abrev):
                self.assertEqual(
                    RI.premiere_phrase("Faire A, %s B, vite. Puis C." % abrev),
                    "Faire A, %s B, vite." % abrev)

    def test_un_mot_qui_finit_comme_une_abreviation_coupe(self):
        # « index. » finit par « ex. » : ce n'est pas l'abréviation.
        self.assertEqual(RI.premiere_phrase("Lire l'index. Puis C."),
                         "Lire l'index.")

    def test_aucune_description_versionnee_n_est_amputee(self):
        racine = Path(__file__).resolve().parent.parent
        for chemin in sorted((racine / "IA" / "skills").rglob("*.md")):
            fm = RI.lire_frontmatter(chemin)
            if not fm or fm.get("kind") != "skill":
                continue
            with self.subTest(skill=fm.get("name")):
                phrase = RI.premiere_phrase(fm.get("description", ""))
                self.assertFalse(RI.finit_par_abreviation(phrase),
                                 "première phrase coupée sur une abréviation")
