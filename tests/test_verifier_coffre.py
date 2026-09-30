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


if __name__ == "__main__":
    unittest.main()
