"""Le garde du registre des leçons : ce qu'il exige d'une PR, ce qu'il épargne.

Lancé sur un dépôt git jetable, comme son cousin le garde-plancher : ce qu'il
juge ne se lit que dans un *diff* — la ligne de leçon ajoutée, la base du
comparatif, le code de sortie.

Onze scénarios, tous nés de la panne réelle de novembre 2026 : une PR qui
touche un skill sans toucher le registre (la panne), la colonne « Vérifié par »
vide, un « non rejoué » sans son pourquoi (l'aveu nu), et ce que le garde
épargne : la preuve rejouée, le « non rejoué » qui se justifie, la PR qui ne
touche aucun skill.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
GARDE = RACINE / "scripts" / "garde_registre.py"

REGISTRE = "IA/system/impact-des-skills.md"

# Tableau minimal du registre : en-tête, séparateur, une ligne de leçon déjà
# correcte. Le garde ne lit que la forme, jamais le lien.
REGISTRE_DE_BASE = """# impact-des-skills.md

| Date | Leçon | Skill touché | Ce qui a changé | Vérifié par | Statut | Revue |
|---|---|---|---|---|---|---|
| 2026-09-13 | `rendu-mermaid-en-conteneur` | `mermaid` | rendu jetable à lancer | rendu rejoué en conteneur, SVG produit | confirmé | — |
"""

LIGNE_PREUVE_REJOUEE = (
    "| 2026-11-16 | `une-lecon` | `livraison-git` | règle ajoutée "
    "| rejouée sur une vraie livraison | proposé | 2026-12-16 |\n"
)
LIGNE_VERIFIE_VIDE = (
    "| 2026-11-16 | `une-lecon` | `livraison-git` | règle ajoutée "
    "|  | proposé | 2026-12-16 |\n"
)
LIGNE_NON_REJOUE_NU = (
    "| 2026-11-16 | `une-lecon` | `livraison-git` | règle ajoutée "
    "| `non rejoué` | proposé | 2026-12-16 |\n"
)
LIGNE_NON_REJOUE_JUSTIFIE = (
    "| 2026-11-16 | `une-lecon` | `livraison-git` | règle ajoutée "
    "| `non rejoué` — règle de tenue de PR, coût constaté sur trois PR "
    "| proposé | 2026-12-16 |\n"
)


LIGNE_BASE_PREUVE = (
    "| 2026-09-13 | `rendu-mermaid-en-conteneur` | `mermaid` | rendu jetable "
    "à lancer | rendu rejoué en conteneur, SVG produit | confirmé | — |"
)
LIGNE_BASE_PREUVE_VIDEE = (
    "| 2026-09-13 | `rendu-mermaid-en-conteneur` | `mermaid` | rendu jetable "
    "à lancer |  | confirmé | — |"
)
_BS = chr(92)  # barre oblique inverse, hors du piège des échappements imbriqués
LIGNE_AVEC_PIPE_NON_ECHAPPE = (
    "| 2026-11-16 | `une-lecon` | `livraison-git` | règle a | b "
    "| rejouée sur une vraie livraison | proposé | 2026-12-16 |\n"
)
LIGNE_AVEC_PIPE_ECHAPPE = (
    "| 2026-11-16 | `une-lecon` | `livraison-git` | lien [[une note"
    + _BS + "|un titre]] "
    "| rejouée sur une vraie livraison | proposé | 2026-12-16 |\n"
)


class DepotJetable:
    """Un dépôt à deux commits : une base, une tête « PR »."""

    def __init__(self, modifie_registre=None, touche_skill=False,
                 vide_ligne_base=False, retire_ligne_base=False):
        self.racine = Path(tempfile.mkdtemp(prefix="garde-registre-"))
        for commande in (
            ("init", "-q"),
            ("config", "user.email", "test@exemple"),
            ("config", "user.name", "test"),
        ):
            self._git(*commande)
        self._ecrire(REGISTRE, REGISTRE_DE_BASE)
        self._ecrire("IA/skills/mermaid/mermaid.md", "# Mermaid\n")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "base")

        if touche_skill:
            self._ecrire("IA/skills/mermaid/mermaid.md", "# Mermaid\n\n- règle neuve\n")
        # Un seul registre composé : chaque transformation part de l'état de
        # la précédente, la dernière écriture ne doit jamais effacer les autres.
        registre = REGISTRE_DE_BASE
        if retire_ligne_base:
            registre = registre.replace(LIGNE_BASE_PREUVE + "\n", "")
        if vide_ligne_base:
            registre = registre.replace(
                LIGNE_BASE_PREUVE, LIGNE_BASE_PREUVE_VIDEE
            )
        if modifie_registre is not None:
            registre = registre.replace(
                "| 2026-09-13",
                modifie_registre + "| 2026-09-13",
            )
        if registre != REGISTRE_DE_BASE:
            self._ecrire(REGISTRE, registre)
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "pr", "--allow-empty")

    def _git(self, *args):
        subprocess.run(
            ["git", "-C", str(self.racine), *args],
            check=True,
            capture_output=True,
        )

    def _ecrire(self, chemin, contenu):
        cible = self.racine / chemin
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(contenu, encoding="utf-8")

    def lance_le_garde(self, base="HEAD~1"):
        return subprocess.run(
            [
                sys.executable,
                str(GARDE),
                "--depot",
                str(self.racine),
                "--base",
                base,
            ],
            capture_output=True,
            text=True,
        )


class GardeRegistre(unittest.TestCase):
    def test_pr_sans_skill_n_a_rien_a_reclamer(self):
        depot = DepotJetable(modifie_registre=LIGNE_PREUVE_REJOUEE)
        verdict = depot.lance_le_garde()
        self.assertEqual(verdict.returncode, 0, verdict.stdout + verdict.stderr)
        self.assertIn("sans objet", verdict.stdout)

    def test_pr_qui_touche_un_skill_sans_registre_est_refusee(self):
        depot = DepotJetable(touche_skill=True)
        verdict = depot.lance_le_garde()
        self.assertEqual(verdict.returncode, 1, verdict.stdout + verdict.stderr)
        self.assertIn("sans toucher", verdict.stdout)

    def test_preuve_rejouee_passe(self):
        depot = DepotJetable(touche_skill=True, modifie_registre=LIGNE_PREUVE_REJOUEE)
        verdict = depot.lance_le_garde()
        self.assertEqual(verdict.returncode, 0, verdict.stdout + verdict.stderr)

    def test_verifie_par_vide_est_refuse(self):
        depot = DepotJetable(touche_skill=True, modifie_registre=LIGNE_VERIFIE_VIDE)
        verdict = depot.lance_le_garde()
        self.assertEqual(verdict.returncode, 1, verdict.stdout + verdict.stderr)
        self.assertIn("« Vérifié par » vide", verdict.stdout)

    def test_non_rejoue_sans_son_pourquoi_est_refuse(self):
        depot = DepotJetable(touche_skill=True, modifie_registre=LIGNE_NON_REJOUE_NU)
        verdict = depot.lance_le_garde()
        self.assertEqual(verdict.returncode, 1, verdict.stdout + verdict.stderr)
        self.assertIn("sans son pourquoi", verdict.stdout)

    def test_non_rejoue_justifie_passe(self):
        depot = DepotJetable(
            touche_skill=True, modifie_registre=LIGNE_NON_REJOUE_JUSTIFIE
        )
        verdict = depot.lance_le_garde()
        self.assertEqual(verdict.returncode, 0, verdict.stdout + verdict.stderr)

    def test_virer_la_preuve_d_une_ligne_ancienne_est_refuse(self):
        depot = DepotJetable(
            touche_skill=True, modifie_registre=LIGNE_PREUVE_REJOUEE,
            vide_ligne_base=True,
        )
        verdict = depot.lance_le_garde()
        self.assertEqual(verdict.returncode, 1, verdict.stdout + verdict.stderr)
        self.assertIn("« Vérifié par » vide", verdict.stdout)

    def test_retirer_une_ligne_sans_remplacement_est_refuse(self):
        depot = DepotJetable(
            touche_skill=True, modifie_registre=LIGNE_PREUVE_REJOUEE,
            retire_ligne_base=True,
        )
        verdict = depot.lance_le_garde()
        self.assertEqual(verdict.returncode, 1, verdict.stdout + verdict.stderr)
        self.assertIn("retirée sans remplacement", verdict.stdout)

    def test_pipe_non_echappe_dans_une_cellule_est_refuse(self):
        depot = DepotJetable(
            touche_skill=True, modifie_registre=LIGNE_AVEC_PIPE_NON_ECHAPPE
        )
        verdict = depot.lance_le_garde()
        self.assertEqual(verdict.returncode, 1, verdict.stdout + verdict.stderr)
        self.assertIn("non conforme", verdict.stdout)

    def test_pipe_echappe_dans_une_cellule_passe(self):
        depot = DepotJetable(
            touche_skill=True, modifie_registre=LIGNE_AVEC_PIPE_ECHAPPE
        )
        verdict = depot.lance_le_garde()
        self.assertEqual(verdict.returncode, 0, verdict.stdout + verdict.stderr)

    def test_base_absente_finit_en_deux(self):
        depot = DepotJetable(touche_skill=True)
        verdict = depot.lance_le_garde(base="origin/main")
        self.assertEqual(verdict.returncode, 2, verdict.stdout + verdict.stderr)


if __name__ == "__main__":
    unittest.main()
