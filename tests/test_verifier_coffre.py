"""Contrôles de `scripts/verifier_coffre.py` (§5, §10.2, §13).

Le vérificateur travaille sur un état global : `RACINE`, `erreurs`,
`avertissements`. Chaque test installe donc son propre coffre temporaire et
des listes neuves, puis remet l'état d'origine — un test ne doit pas dépendre
de celui qui l'a précédé, ni laisser une trace derrière lui.
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

import verifier_coffre as VC            # noqa: E402

DEFAUT = {"schema": "1", "read_only": "false", "module": "noyau"}


class BaseVerificateur(unittest.TestCase):
    """Un coffre temporaire, et l'état global du vérificateur mis de côté."""

    def setUp(self):
        self.racine = Path(tempfile.mkdtemp(prefix="obsia-test-verif-"))
        self.addCleanup(shutil.rmtree, self.racine, ignore_errors=True)

        self._racine_avant = VC.RACINE
        self._erreurs_avant = list(VC.erreurs)
        self._avertissements_avant = list(VC.avertissements)
        self.addCleanup(self.restaurer)

        VC.RACINE = self.racine
        VC.erreurs.clear()
        VC.avertissements.clear()

    def restaurer(self):
        VC.RACINE = self._racine_avant
        VC.erreurs[:] = self._erreurs_avant
        VC.avertissements[:] = self._avertissements_avant

    def ecrire(self, relatif: str, contenu: str) -> Path:
        chemin = self.racine / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")
        return chemin

    def fiche(self, genre: str, nom: str, champs: dict, corps: str = "") -> dict:
        """Écrit une fiche valide et la relit comme le fait le vérificateur."""
        dossier = "IA/%ss" % genre
        valeurs = dict(DEFAUT)
        valeurs.update(champs)
        if genre == "skill":
            valeurs.setdefault("type", "core")
        if genre == "agent":
            valeurs["read_only"] = "true"
        lignes = ["schema: 1", "kind: %s" % genre, "name: %s" % nom,
                  "description: %s" % valeurs.pop("description", "Fiche de test."),
                  "read_only: %s" % valeurs.pop("read_only")]
        for cle, valeur in valeurs.items():
            if cle == "schema":
                continue
            if isinstance(valeur, list):
                lignes.append("%s:" % cle)
                lignes += ["  - %s" % v for v in valeur]
            else:
                lignes.append("%s: %s" % (cle, valeur))
        contenu = "---\n%s\n---\n\n%s\n" % ("\n".join(lignes), corps)
        return VC.verifier_fichier(self.ecrire("%s/%s.md" % (dossier, nom), contenu),
                                   genre)

    def fiche_mcp(self, nom: str, champs: dict) -> list[dict]:
        """Écrit une fiche de IA/MCP/ et la relit par `verifier_mcp`."""
        valeurs = {"schema": "1", "kind": "mcp", "name": nom,
                   "description": "Serveur de test.", "type": "stdio",
                   "transport": "http", "permission": "normal"}
        valeurs.update(champs)
        lignes = ["%s: %s" % (c, v) for c, v in valeurs.items() if v is not None]
        self.ecrire("IA/MCP/%s.md" % nom,
                    "---\n%s\n---\n\n%s\n" % ("\n".join(lignes), "Corps."))
        return VC.verifier_mcp(self.racine / "IA" / "MCP")

    def modules_a_la_main(self, *noms: str) -> list[dict]:
        """Les modules minimal dont `verifier_appartenance` a besoin."""
        return [{"name": n, "essentiel": n == "noyau",
                 "_chemin": "IA/system/modules/%s.md" % n} for n in noms]

    def executer(self) -> int:
        """Lance le vérificateur entier, comme la CI : c'est lui qu'on juge."""
        avant_derives, avant_argv = VC.verifier_derives, sys.argv
        self.addCleanup(setattr, VC, "verifier_derives", avant_derives)
        self.addCleanup(setattr, sys, "argv", avant_argv)
        VC.verifier_derives = lambda: None   # pas de dépôt git dans ce coffre
        sys.argv = ["verifier_coffre.py", "--silencieux"]
        # Le rapport final part sur stderr, même en silencieux : le compte rendu
        # du test n'a pas à le porter, les messages sont dans `VC.erreurs`.
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            return VC.main()

    def erreurs_texte(self) -> str:
        return "\n".join(VC.erreurs)

    def avertissements_texte(self) -> str:
        return "\n".join(VC.avertissements)


class TestConsigneSkill(BaseVerificateur):
    """§10.2 : « charger `X` » doit être vu quelle que soit la casse.

    Le verbe peut ouvrir une phrase — c'est même sa place la plus naturelle
    dans une procédure : « Charger `x`. ». Un motif qui n'accepte que la
    minuscule laisse alors passer exactement les consignes les mieux écrites.
    """

    def decor(self, renvoi: str) -> tuple[list, list]:
        """Un agent qui déclare `a-verifie`, et un skill qui renvoie ailleurs."""
        agent = self.fiche("agent", "agent-verif", {"skills": ["a-verifie"]})
        skills = [
            self.fiche("skill", "a-verifie", {"type": "core"}, "## Procédure\n\n%s\n" % renvoi),
            self.fiche("skill", "b-vise", {"type": "outil", "module": "construction"},
                       "## Procédure\n\nRien.\n"),
        ]
        return [agent], skills

    def test_consigne_en_debut_de_phrase(self):
        """« Charger `b-vise` » ouvre la phrase : c'est le cas à ne pas rater."""
        agents, skills = self.decor("Charger `b-vise` pour la suite.")

        VC.verifier_portee_des_renvois(agents, skills)

        self.assertEqual(len(VC.avertissements), 1, VC.avertissements)
        self.assertIn("b-vise", VC.avertissements[0])
        self.assertIn("agent-verif", VC.avertissements[0])

    def test_consigne_en_minuscule(self):
        """Le cas déjà couvert : il ne doit pas régresser."""
        agents, skills = self.decor("charger `b-vise` pour la suite.")

        VC.verifier_portee_des_renvois(agents, skills)

        self.assertEqual(len(VC.avertissements), 1, VC.avertissements)

    def test_consigne_formule_avec_cest(self):
        agents, skills = self.decor("C'est `b-vise` qu'il faut lire.")

        VC.verifier_portee_des_renvois(agents, skills)

        self.assertEqual(len(VC.avertissements), 1, VC.avertissements)

    def test_consigne_formule_avec_releve_de(self):
        agents, skills = self.decor("Relève de `b-vise`, pas de cet agent.")

        VC.verifier_portee_des_renvois(agents, skills)

        self.assertEqual(len(VC.avertissements), 1, VC.avertissements)

    def test_renvoi_vers_soi_meme_ne_dit_rien(self):
        """Un skill qui se nomme lui-même n'est pas une consigne inapplicable."""
        agents, skills = self.decor("Charger `a-verifie` de nouveau.")

        VC.verifier_portee_des_renvois(agents, skills)

        self.assertEqual(VC.avertissements, [])

    def test_une_simple_mention_ne_declenche_rien(self):
        """Le contrôle repose sur le verbe : le citer sans verbe ne compte pas."""
        agents, skills = self.decor("Voir aussi `b-vise`, sans obligation.")

        VC.verifier_portee_des_renvois(agents, skills)

        self.assertEqual(VC.avertissements, [])


MODULE_NOYAU = """---
schema: 1
kind: module
name: noyau
description: Le socle.
essentiel: true
---

## Ce que ce module apporte

Rien de plus, ici.
"""


class TestFicheMcpSansModule(BaseVerificateur):
    """§5 et §13 : `module` est obligatoire, fiches de IA/MCP/ comprises.

    Un MCP sans module n'est rattachable à rien : `generer_prompt.py` l'écarte
    dès qu'un profil existe, sans le dire. Le contrôle doit exister côté
    vérificateur, sinon la fiche fautive ne se voit qu'en musique de fond.
    """

    def decor(self, module: str | None) -> None:
        """Le même coffre, à une ligne près : celle du `module` de la fiche MCP."""
        self.ecrire("IA/system/modules/noyau.md", MODULE_NOYAU)
        self.fiche("agent", "agent-verif", {})
        self.fiche("skill", "a-verifie", {"type": "core"})
        self.fiche_mcp("bruno", {} if module is None else {"module": module})

    def test_une_fiche_mcp_sans_module_est_refusee(self):
        self.decor(module=None)

        code = self.executer()

        self.assertEqual(code, 1)
        self.assertIn("MCP/bruno.md", self.erreurs_texte())
        self.assertIn("ne déclare aucun `module`", self.erreurs_texte())

    def test_la_meme_fiche_avec_un_module_passe(self):
        """Le témoin : sans la ligne fautive, ce contrôle ne dit plus rien."""
        self.decor(module="noyau")

        self.executer()

        self.assertNotIn("ne déclare aucun `module`", self.erreurs_texte())

    def test_un_module_inexistant_est_refuse_aussi(self):
        self.decor(module="absent-du-catalogue")

        self.executer()

        self.assertIn("module inexistant", self.erreurs_texte())

    def test_le_controle_vient_de_verifier_appartenance(self):
        """Le nommer, c'est garantir qu'il n'est pas court-circuité ailleurs."""
        self.decor(module=None)
        modules = [{"name": "noyau", "essentiel": True,
                    "_chemin": "IA/system/modules/noyau.md"}]
        mcp = VC.verifier_mcp(self.racine / "IA" / "MCP")

        VC.verifier_appartenance(modules, [], [], mcp, [])

        self.assertTrue(VC.erreurs, "aucune erreur levée pour une fiche sans module")


class TestProfilFautif(BaseVerificateur):
    """§13 : le vérificateur signale lui aussi un profil qui cite l'inconnu.

    Avertissement, jamais erreur : la CI n'a pas de profil, et un nom hors
    catalogue ne rend pas le coffre incohérent — seulement plus maigre que
    voulu. Le dire, c'est éviter de chercher ailleurs pourquoi l'installation
    est amputée.
    """

    def decor(self, profil: str | None) -> None:
        self.ecrire("IA/system/modules/noyau.md", MODULE_NOYAU)
        self.fiche("agent", "agent-verif", {"skills": ["a-verifie"]})
        self.fiche("skill", "a-verifie", {"type": "core"})
        if profil is not None:
            self.ecrire("obsia.local.yml", profil)

    def test_un_profil_hors_catalogue_est_signale(self):
        self.decor("schema: 1\nmodules:\n  - noyau\n  - noyau-inconnu\n")

        code = self.executer()

        self.assertEqual(code, 0, self.erreurs_texte())
        self.assertIn("noyau-inconnu", self.avertissements_texte())
        self.assertNotIn("noyau-inconnu", self.erreurs_texte())

    def test_sans_profil_rien_n_est_signale(self):
        """Le cas de la CI : pas de profil, donc rien à dire."""
        self.decor(None)

        code = self.executer()

        self.assertEqual(code, 0, self.erreurs_texte())
        self.assertNotIn("inconnu", self.avertissements_texte())

    def test_un_profil_juste_est_muet(self):
        self.decor("schema: 1\nmodules:\n  - noyau\n")

        code = self.executer()

        self.assertEqual(code, 0, self.erreurs_texte())
        self.assertNotIn("inconnu", self.avertissements_texte())

    def test_le_signal_ne_fait_pas_echouer_le_controle(self):
        """Une installation amputée reste valide : c'est le §13 qui le veut."""
        self.decor("schema: 1\nmode: copie\nmodules:\n  - noyau\n  - absent\n")

        code = self.executer()

        self.assertEqual(code, 0, self.erreurs_texte())
        self.assertIn("absent", self.avertissements_texte())


class TestCarnets(BaseVerificateur):
    """§6 : forme des carnets, un seul niveau de sous-projet, transition."""

    def carnet(self, projet: str, nom: str, frontmatter: str) -> Path:
        return self.ecrire("mémoire/projets/%s/carnets/%s" % (projet, nom),
                           "---\n%s\n---\n\nCorps.\n" % frontmatter)

    def test_un_carnet_conforme_est_muet(self):
        self.carnet("refonte-de-la-memoire",
                    "2026-10-02-refonte-de-la-memoire-t1.md",
                    "agent: assistant\nprojet: refonte-de-la-memoire\nstatut: en cours\n")
        VC.verifier_carnets()
        self.assertEqual([], VC.erreurs)
        self.assertEqual([], VC.avertissements)

    def test_un_carnet_mal_nomme_est_refuse(self):
        self.carnet("refonte-de-la-memoire",
                    "2026-10-02-autre-projet-t1.md",
                    "agent: assistant\nprojet: refonte-de-la-memoire\nstatut: en cours\n")
        VC.verifier_carnets()
        self.assertIn("ne correspond pas au dossier", self.erreurs_texte())

    def test_un_carnet_sans_date_est_refuse(self):
        self.carnet("refonte-de-la-memoire", "t1.md",
                    "agent: assistant\nprojet: refonte-de-la-memoire\nstatut: en cours\n")
        VC.verifier_carnets()
        self.assertIn("mal nommé", self.erreurs_texte())

    def test_un_carnet_sans_statut_est_refuse(self):
        self.carnet("refonte-de-la-memoire",
                    "2026-10-02-refonte-de-la-memoire-t1.md",
                    "agent: assistant\nprojet: refonte-de-la-memoire\n")
        VC.verifier_carnets()
        self.assertIn("`statut:`", self.erreurs_texte())

    def test_un_statut_hors_liste_est_refuse(self):
        self.carnet("refonte-de-la-memoire",
                    "2026-10-02-refonte-de-la-memoire-t1.md",
                    "agent: assistant\nprojet: refonte-de-la-memoire\nstatut: perdu\n")
        VC.verifier_carnets()
        self.assertIn("en cours", self.erreurs_texte())

    def test_un_statut_vide_est_refuse(self):
        self.carnet("refonte-de-la-memoire",
                    "2026-10-02-refonte-de-la-memoire-t1.md",
                    "agent: assistant\nprojet: refonte-de-la-memoire\nstatut:\n")
        VC.verifier_carnets()
        self.assertIn("`statut:` vide", self.erreurs_texte())

    def test_un_agent_vide_est_refuse(self):
        self.carnet("refonte-de-la-memoire",
                    "2026-10-02-refonte-de-la-memoire-t1.md",
                    "agent:\nprojet: refonte-de-la-memoire\nstatut: en cours\n")
        VC.verifier_carnets()
        self.assertIn("`agent:` vide", self.erreurs_texte())

    def test_un_projet_qui_ne_correspond_pas_au_dossier_est_refuse(self):
        self.carnet("refonte-de-la-memoire",
                    "2026-10-02-refonte-de-la-memoire-t1.md",
                    "agent: assistant\nprojet: autre-projet\nstatut: en cours\n")
        VC.verifier_carnets()
        self.assertIn("`projet: autre-projet`", self.erreurs_texte())

    def test_un_sous_dossier_dans_carnets_est_refuse(self):
        self.ecrire("mémoire/projets/un-projet/carnets/archive/vieux.md", "Corps.\n")
        VC.verifier_carnets()
        self.assertIn("sous-dossier dans `carnets/`", self.erreurs_texte())

    def test_une_note_datee_a_plat_est_toleree(self):
        self.ecrire("mémoire/projets/ancien-projet/2026-09-18-une-note.md",
                    "---\nagent: assistant\n---\n\nCorps.\n")
        VC.verifier_carnets()
        self.assertEqual([], VC.erreurs)
        self.assertIn("ancienne forme", self.avertissements_texte())

    def test_un_sous_projet_imbrique_est_refuse(self):
        self.ecrire("mémoire/projets/un-projet/sous/encore/fichier.md", "Corps.\n")
        VC.verifier_carnets()
        self.assertIn("un seul niveau", self.erreurs_texte())

    def test_un_seul_niveau_de_sous_projet_est_admis(self):
        self.carnet("un-projet", "2026-10-02-un-projet-t1.md",
                    "agent: assistant\nprojet: un-projet\nstatut: clos\n")
        self.ecrire("mémoire/projets/un-projet/sous/carnets/2026-10-02-sous-t1.md",
                    "---\nagent: assistant\nprojet: sous\nstatut: clos\n---\n\nCorps.\n")
        VC.verifier_carnets()
        self.assertEqual([], VC.erreurs)


class TestAnnexesContrat(BaseVerificateur):
    """§5, §13 : les annexes du noyau, tout `IA/system/contrat/*.md`.

    Une annexe se définit **par son dossier** : tout `*.md` du dossier est
    contrôlé, sauf `registre.md`, l'index exempté nommément. Une annexe renommée
    doit rester dans le filet. Le frontmatter réutilise les gardes communes —
    `schema` entier, `name` qui suit le fichier et `NOM_VALIDE`, `description`
    d'une seule ligne physique — sans `read_only`, réservé aux fiches qui
    s'exécutent.
    """

    DOSSIER = "IA/system/contrat"

    def annexe(self, nom: str, champs: dict, corps: str = "") -> list[dict]:
        """Écrit une annexe et la relit comme le fait le vérificateur."""
        valeurs = {"schema": "1", "kind": "contract", "name": nom,
                   "description": "Annexe de test.", "module": "noyau"}
        valeurs.update(champs)
        lignes = ["%s: %s" % (c, v) for c, v in valeurs.items() if v is not None]
        self.ecrire("%s/%s.md" % (self.DOSSIER, nom),
                    "---\n%s\n---\n\n%s\n" % ("\n".join(lignes), corps))
        return VC.verifier_annexes_contrat(
            self.racine / self.DOSSIER,
            self.modules_a_la_main("noyau", "construction"))

    def test_une_annexe_conforme_passe(self):
        annexes = self.annexe("contrat-noyau", {})
        self.assertEqual([], VC.erreurs, self.erreurs_texte())
        self.assertEqual(1, len(annexes))

    def test_un_kind_autre_que_contract_est_refuse(self):
        self.annexe("contrat-noyau", {"kind": "module"})
        self.assertIn("le dossier des annexes du contrat", self.erreurs_texte())

    def test_un_schema_qui_n_est_pas_un_entier_est_refuse(self):
        self.annexe("contrat-noyau", {"schema": "un"})
        self.assertIn("`schema` doit être un entier", self.erreurs_texte())

    def test_un_name_qui_ne_suit_pas_le_fichier_est_refuse(self):
        self.annexe("contrat-noyau", {"name": "contrat-autre"})
        self.assertIn("≠ nom du fichier", self.erreurs_texte())

    def test_un_name_hors_nom_valide_est_refuse(self):
        self.annexe("contrat_Noyau", {})
        self.assertIn("minuscules et tirets", self.erreurs_texte())

    def test_une_description_vide_est_refusee(self):
        self.annexe("contrat-noyau", {"description": ""})
        self.assertIn("`description` vide", self.erreurs_texte())

    def test_une_description_repliee_est_refusee(self):
        self.annexe("contrat-noyau", {"description": ">"})
        self.assertIn("scalaire replié", self.erreurs_texte())

    def test_une_description_poursuivie_sur_la_ligne_suivante_est_refusee(self):
        self.annexe("contrat-noyau", {"description": "Une phrase qui s'achève :"})
        self.assertIn("se poursuivre sur la ligne suivante", self.erreurs_texte())

    def test_un_module_inconnu_est_refuse(self):
        self.annexe("contrat-noyau", {"module": "fantome"})
        self.assertIn("module inexistant", self.erreurs_texte())

    def test_un_module_absent_est_refuse(self):
        self.annexe("contrat-noyau", {"module": None})
        self.assertIn("champ obligatoire manquant : `module`", self.erreurs_texte())

    def test_un_frontmatter_absent_est_refuse(self):
        self.ecrire("%s/contrat-noyau.md" % self.DOSSIER, "Corps sans en-tête.\n")
        VC.verifier_annexes_contrat(self.racine / self.DOSSIER,
                                    self.modules_a_la_main("noyau"))
        self.assertIn("frontmatter absent", self.erreurs_texte())

    def test_le_registre_est_exempte(self):
        self.ecrire("%s/registre.md" % self.DOSSIER, "# Registre\n\nSans en-tête.\n")
        VC.verifier_annexes_contrat(self.racine / self.DOSSIER,
                                    self.modules_a_la_main("noyau"))
        self.assertEqual([], VC.erreurs, self.erreurs_texte())

    def test_tout_fichier_du_dossier_est_controle(self):
        """Un nom qui ne commence plus par `contrat-` ne sort pas du filet."""
        self.ecrire("%s/annexe-noyau.md" % self.DOSSIER, "Sans en-tête.\n")
        VC.verifier_annexes_contrat(self.racine / self.DOSSIER,
                                    self.modules_a_la_main("noyau"))
        self.assertIn("frontmatter absent", self.erreurs_texte())

    def test_le_dossier_absent_avertit(self):
        """Pas de dossier : on le dit, on ne sort pas en 0 sans rien dire."""
        VC.verifier_annexes_contrat(self.racine / self.DOSSIER,
                                    self.modules_a_la_main("noyau"))
        self.assertEqual([], VC.erreurs, self.erreurs_texte())
        self.assertIn("dossier des annexes du contrat absent",
                      self.avertissements_texte())

    def test_les_chemins_cites_dans_une_annexe_sont_controles(self):
        """Point 3 : le dossier est déjà dans le filet de `verifier_chemins_cites`."""
        self.annexe("contrat-noyau", {},
                    "Voir `IA/skills/inexistant.md` pour la suite.\n")
        VC.verifier_chemins_cites()
        self.assertIn("IA/skills/inexistant.md", self.erreurs_texte())

    def test_un_chemin_relatif_du_dossier_est_resolu(self):
        """`../VAULT-CONTRACT.md` mène bien à `IA/system/VAULT-CONTRACT.md`.

        C'est le cas qui a motivé l'écart voulu de N1 : une annexe cite le
        contrat depuis son dossier, et le chemin n'est valide que résolu depuis
        le fichier qui le cite."""
        self.ecrire("IA/system/VAULT-CONTRACT.md", "# Contrat\n\nRien à voir ici.\n")
        self.annexe("contrat-noyau", {},
                    "Voir `../VAULT-CONTRACT.md` pour la règle (§5).\n")
        VC.verifier_chemins_cites()
        self.assertEqual([], VC.erreurs, self.erreurs_texte())

    def test_un_chemin_relatif_casse_du_dossier_est_signale(self):
        self.annexe("contrat-noyau", {},
                    "Voir `../inexistant.md` pour la règle (§5).\n")
        VC.verifier_chemins_cites()
        self.assertIn("../inexistant.md", self.erreurs_texte())

    def test_une_annexe_ne_peuple_pas_son_module(self):
        """Une annexe déclare un module, elle ne l'habite pas (§13)."""
        self.annexe("contrat-noyau", {})
        VC.verifier_appartenance(self.modules_a_la_main("noyau"), [], [], [], [])
        self.assertIn("n'installerait rien", self.avertissements_texte())


if __name__ == "__main__":
    unittest.main()
