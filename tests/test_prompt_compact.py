"""Le mode compact de `generer_prompt.py` : un prompt court par agent.

Pour un modèle à petit contexte, le prompt ne porte que les règles graves du
noyau (écriture et preview, secrets), la fiche de l'agent et ses skills en une
ligne. Il ne tronque jamais : au-delà du plafond, la ligne de commande refuse.
Les agents versionnés sont lus tels quels.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from generer_prompt import (PLAFOND_COMPACT, RACINE_DEFAUT,       # noqa: E402
                            NOYAU, BalisageInvalide, NoyauIncomplet,
                            chemins_absolus, corps_declaratif, decouper_en_phases,
                            lire_frontmatter, prompt_compact, regle_des_secrets,
                            section_ecriture, skills_par_phase)

SCRIPT = RACINE_DEFAUT / "scripts" / "generer_prompt.py"
#: Les agents dont la fiche tient aujourd'hui sous le plafond.
SOUS_LE_PLAFOND = ("assistant", "contradicteur", "visionnaire", "administrateur-mint")


def compact_ou_saut(test, nom):
    """Le prompt compact d'un agent versionné, ou le saut s'il n'est pas publié.

    Le dépôt public ne porte pas tous les agents : un agent absent se saute,
    il ne fait pas planter la suite sur `len(None)`.
    """
    prompt = prompt_compact(RACINE_DEFAUT, nom)
    if prompt is None:
        test.skipTest(f"agent absent : {nom}")
    return prompt


class TestLePromptCompact(unittest.TestCase):
    def test_il_tient_sous_le_plafond(self):
        for nom in SOUS_LE_PLAFOND:
            with self.subTest(agent=nom):
                self.assertLessEqual(len(compact_ou_saut(self, nom)), PLAFOND_COMPACT)

    def test_il_porte_les_regles_graves(self):
        prompt = compact_ou_saut(self, "assistant")
        ecriture, regle = section_ecriture(RACINE_DEFAUT), regle_des_secrets(RACINE_DEFAUT)
        # Le vrai contrat doit les porter : un échec ici, pas un saut.
        self.assertTrue(ecriture.strip(), "le §2 du contrat est introuvable")
        self.assertTrue(regle.strip(), "le §4 du contrat a perdu ses repères")
        self.assertIn(ecriture, prompt)
        for ligne in regle.splitlines():
            self.assertIn(ligne, prompt)
        self.assertIn("preview", ecriture)

    def test_il_porte_la_fiche_et_chaque_skill_en_une_ligne(self):
        fiche = RACINE_DEFAUT / "IA" / "agents" / "assistant.md"
        prompt = compact_ou_saut(self, "assistant")
        self.assertIn(corps_declaratif(fiche), prompt)
        for nom in lire_frontmatter(fiche)["skills"]:
            self.assertIn("`%s`" % nom, prompt)
        self.assertNotIn("## Skills disponibles", prompt)

    def test_les_skills_n_y_sont_que_par_leur_nom(self):
        prompt = compact_ou_saut(self, "assistant")
        self.assertNotIn("À charger", prompt[prompt.index("## Tes skills"):])

    def test_aucun_chemin_absolu(self):
        for nom in SOUS_LE_PLAFOND:
            with self.subTest(agent=nom):
                self.assertEqual(chemins_absolus(compact_ou_saut(self, nom)), [])

    def test_agent_inconnu(self):
        self.assertIsNone(prompt_compact(RACINE_DEFAUT, "inexistant"))


FICHE_A_PHASES = """# A
socle `obsidian-manager`
<!-- phase: creation -->
porte `cadrage-produit`
<!-- phase: fin -->
<!-- phase: evolution -->
reprise `reprise-dun-projet` et `cadrage-produit`
<!-- phase: fin -->
fin du socle"""


class TestLesPhases(unittest.TestCase):
    def test_le_socle_et_les_phases_se_separent(self):
        socle, phases = decouper_en_phases(FICHE_A_PHASES)
        self.assertEqual(list(phases), ["creation", "evolution"])
        self.assertIn("fin du socle", socle)
        self.assertNotIn("porte", socle)
        self.assertNotIn("<!--", socle + "".join(phases.values()))

    def test_un_skill_va_a_la_premiere_phase_qui_le_cite(self):
        socle, phases = decouper_en_phases(FICHE_A_PHASES)
        g = skills_par_phase(["obsidian-manager", "cadrage-produit",
                              "reprise-dun-projet", "mermaid"], socle, phases)
        self.assertEqual(g, {"communs": ["obsidian-manager", "mermaid"],
                             "creation": ["cadrage-produit"],
                             "evolution": ["reprise-dun-projet"]})

    def test_un_balisage_bancal_est_refuse(self):
        for fautive in ("<!-- phase: a -->\nx",
                        "<!-- phase: fin -->",
                        "<!-- phase: a -->\n<!-- phase: b -->",
                        "<!-- phase: a -->\n<!-- phase: fin -->\n"
                        "<!-- phase: a -->\n<!-- phase: fin -->"):
            with self.subTest(fautive=fautive):
                with self.assertRaises(BalisageInvalide):
                    decouper_en_phases(fautive)

    def test_chaque_fiche_versionnee_est_bien_balisee(self):
        for fiche in sorted((RACINE_DEFAUT / "IA" / "agents").glob("*.md")):
            with self.subTest(fiche=fiche.name):
                decouper_en_phases(corps_declaratif(fiche))

    def test_chaque_phase_de_chaque_agent_tient_sous_le_plafond(self):
        for fiche in sorted((RACINE_DEFAUT / "IA" / "agents").glob("*.md")):
            nom = fiche.stem
            _, phases = decouper_en_phases(corps_declaratif(fiche))
            for phase in [None, *phases]:
                with self.subTest(agent=nom, phase=phase):
                    self.assertLessEqual(len(prompt_compact(RACINE_DEFAUT, nom, phase)),
                                         PLAFOND_COMPACT)

    def test_les_noms_de_phase_de_chaque_fiche_sont_ceux_attendus(self):
        # Une faute de frappe dans une balise créerait une phase de plus,
        # muette, au lieu d'échouer : les noms sont épinglés ici.
        attendues = {
            "batisseur": ["cadrage", "construction", "rapide", "reprise", "changement"],
            "administrateur": ["constat", "intervention", "consignation"],
        }
        for fiche in sorted((RACINE_DEFAUT / "IA" / "agents").glob("*.md")):
            with self.subTest(fiche=fiche.name):
                _, phases = decouper_en_phases(corps_declaratif(fiche))
                self.assertEqual(list(phases), attendues.get(fiche.stem, []))

    def test_une_phase_inconnue_est_refusee(self):
        with self.assertRaises(KeyError):
            prompt_compact(RACINE_DEFAUT, "assistant", "inexistante")


class TestLaLigneDeCommande(unittest.TestCase):
    def lancer(self, agent):
        return subprocess.run([sys.executable, str(SCRIPT), "--compact", agent],
                              capture_output=True, text=True)

    def test_sous_le_plafond_elle_ecrit(self):
        r = self.lancer("assistant")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Tu es l'agent OBSIA `assistant`", r.stdout)

    def test_une_phase_inconnue_sort_en_1_sans_rien_ecrire(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "--compact", "batisseur",
                            "--phase", "inexistante"], capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout), (1, ""))
        self.assertIn("Phase inconnue", r.stderr)

    def test_phase_sans_compact_refusee(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "--phase", "cadrage"],
                           capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout), (1, ""))

    def test_compact_et_embarque_s_excluent(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "--compact", "assistant",
                            "--embarque", "contradicteur"],
                           capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout), (1, ""))


FICHE = """---
schema: 1
kind: agent
name: gros
description: Un agent de test.
module: noyau
read_only: true
---

# Gros
"""


class TestUnCoffreDeCirconstance(unittest.TestCase):
    """Racine temporaire : ce qui se teste ne dépend d'aucune vraie fiche."""

    def setUp(self):
        self.racine = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.racine)
        (self.racine / "IA" / "agents").mkdir(parents=True)
        (self.racine / "IA" / "skills").mkdir()

    def poser(self, corps="", noyau=None):
        (self.racine / "IA" / "agents" / "gros.md").write_text(FICHE + corps,
                                                                encoding="utf-8")
        if noyau is not None:
            (self.racine / NOYAU).parent.mkdir(parents=True, exist_ok=True)
            (self.racine / NOYAU).write_text(noyau, encoding="utf-8")

    def lancer(self):
        return subprocess.run([sys.executable, str(SCRIPT), "--racine",
                               str(self.racine), "--compact", "gros"],
                              capture_output=True, text=True)

    def test_au_dela_du_plafond_elle_refuse_sans_tronquer(self):
        self.poser("mot " * PLAFOND_COMPACT)
        r = self.lancer()
        self.assertEqual((r.returncode, r.stdout), (1, ""))
        self.assertIn("trop long", r.stderr)

    def test_sous_le_plafond_elle_ecrit(self):
        self.poser("court")
        r = self.lancer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("# Gros", r.stdout)

    def test_un_noyau_sans_section_d_ecriture_est_refuse(self):
        self.poser("court", noyau="# Contrat\n\n## 4. Exécution\n\nrien\n")
        with self.assertRaises(NoyauIncomplet):
            prompt_compact(self.racine, "gros")
        r = self.lancer()
        self.assertEqual((r.returncode, r.stdout), (1, ""))
        self.assertIn("Noyau incomplet", r.stderr)

    def test_un_noyau_sans_repere_des_secrets_est_refuse(self):
        self.poser("court", noyau="# Contrat\n\n## 2. Écriture\n\nx\n\n## 3. Suite\n")
        with self.assertRaises(NoyauIncomplet):
            prompt_compact(self.racine, "gros")

if __name__ == "__main__":
    unittest.main()
