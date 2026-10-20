"""La fiche de l'écrivain ouvre l'exception bornée du §7.4.

Le §7.4 n'autorise un MCP à rendre l'aperçu **avec** l'écriture qu'à une
**condition d'entrée** : sa fiche doit dire qu'il écrit *pour un harnais pilotant
un modèle local*.
Sans elle, l'écrivain reste dans le droit commun — l'aperçu d'abord, l'écriture
ensuite — et n'a rien à faire sur un coffre réel.

Ce que ces tests protègent, et qui ne se voit nulle part ailleurs : que la fiche
existe ; qu'elle reste une fiche MCP valide au sens du §5 (frontmatter complet,
`transport` et `permission` connus — c'est le vérificateur du socle qui tranche,
pas une copie de ses règles) ; qu'elle porte la phrase qui ouvre l'exception ;
que l'index `IA/README.md` la liste, faute de quoi le catalogue cacherait
l'outil et personne ne saurait qu'il existe (§11).

Depuis la phase 6, ils protègent aussi sa **retirabilité** : le serveur doit
rester un maillon qu'on débranche — retrait franc ou logique — **sans rien
casser**, et la procédure doit être écrite (§10 de la fiche d'OpenCode). Enfin
ils gardent la **décision** sur le 5e critère : il **reste ouvert** — « s'arrête
et le dit » n'est tenu que sur la **capacité**, **pas sur la parole** du modèle.
"""

import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "scripts"))   # `scripts/` n'est pas un paquet

import verifier_coffre as VC            # noqa: E402

FICHE = RACINE / "IA" / "MCP" / "ecrivain-du-coffre.md"
INDEX = RACINE / "IA" / "README.md"
CHEMIN_RELATIF = "IA/MCP/ecrivain-du-coffre.md"


class TestFicheDeLEcrivain(unittest.TestCase):

    def test_la_fiche_existe(self):
        self.assertTrue(FICHE.is_file(),
                        "la fiche de l'écrivain manque : %s (§7.4)" % FICHE)

    def test_la_fiche_est_un_mcp_valide_pour_le_socle(self):
        # On interroge le vérificateur, on ne recopie pas ses règles : s'il
        # durcit le format un jour, ce test suit au lieu de mentir.
        lues = {str(fm["_chemin"]): fm for fm in VC.verifier_mcp(RACINE / "IA" / "MCP")}
        self.assertIn(CHEMIN_RELATIF, lues,
                      "le socle ne lit pas la fiche comme une fiche MCP (§5)")
        fm = lues[CHEMIN_RELATIF]
        self.assertEqual("ecrivain-du-coffre", fm["name"])
        self.assertIn(fm["transport"], VC.TRANSPORTS)
        self.assertIn(fm["permission"], VC.PERMISSIONS)

    def test_la_description_de_la_fiche_nomme_pour_quel_harnais_elle_ecrit(self):
        # La condition d'entrée du §7.4 porte sur ce que la fiche **déclare**, et ce
        # qu'elle déclare vit dans la `description` du frontmatter : c'est elle que
        # l'index reproduit et qu'un agent lit pour choisir l'outil. Un test sur le
        # fichier entier resterait vert si la phrase survivait ailleurs, après un
        # remaniement de la description : il n'épinglerait pas la condition.
        lues = {str(fm["_chemin"]): fm for fm in VC.verifier_mcp(RACINE / "IA" / "MCP")}
        description = str(lues[CHEMIN_RELATIF]["description"]).lower()
        self.assertIn("harnais pilotant un modèle local", description)
        self.assertIn("condition d'entrée", description)

    def test_la_fiche_declare_la_permission_elevee(self):
        """L'écrivain vise des fichiers **hors du dépôt** : §5 l'élève à ``elevated``.

        Le niveau suit la **cible**, pas la distance : le coffre parent n'est pas dans
        ce dépôt, et aucun ``revert`` d'OBSIA ne rattrape son écriture. C'est déjà le
        motif qui met ``coffre-parent`` en ``elevated``.
        """
        self.assertIn("elevated", VC.PERMISSIONS)
        lues = {str(fm["_chemin"]): fm for fm in VC.verifier_mcp(RACINE / "IA" / "MCP")}
        self.assertEqual("elevated", lues[CHEMIN_RELATIF]["permission"])

    def test_l_index_du_catalogue_liste_l_ecrivain(self):
        index = INDEX.read_text(encoding="utf-8")
        self.assertIn("ecrivain-du-coffre", index,
                      "l'index n'est pas régénéré : l'outil resterait invisible (§11)")

    def test_l_agent_assistant_declare_l_ecrivain(self):
        """§5 : un MCP n'est utilisable que **déclaré par un agent**."""
        assistant = next(a for a in self._agents() if a.get("name") == "assistant")
        self.assertIn("ecrivain-du-coffre", assistant.get("mcp", []),
                      "sans déclaration, l'écrivain n'existe pour aucun agent (§5)")

    def test_plus_aucun_mcp_n_est_declare_par_aucun_agent(self):
        """L'avertissement « déclaré par aucun agent » doit avoir disparu."""
        VC.avertissements.clear()
        VC.verifier_references(self._agents(), self._skills())
        restants = [a for a in VC.avertissements if "MCP" in a and "aucun agent" in a]
        self.assertEqual([], restants,
                         "un MCP reste déclaré par aucun agent : %s" % restants)

    def test_la_fiche_dit_que_l_ecrivain_se_retire(self):
        """6e critère de la phase 6 : le serveur reste **retirable**.

        Sa déclaration vit **hors dépôt** (§13) : la retirer ne touche ni le dépôt
        ni le coffre. La fiche doit le dire, **nommer les deux gestes** et dire le
        retrait **réversible** — pas seulement poser un mot.
        """
        corps = FICHE.read_text(encoding="utf-8").lower()
        self.assertIn("retirable", corps)
        self.assertIn("retrait franc", corps)
        self.assertIn("réversible", corps)

    def test_l_adaptateur_dit_comment_retirer_l_ecrivain(self):
        """La fiche d'OpenCode porte la procédure, son constat et sa limite (§10)."""
        adaptateur = RACINE / "IA" / "system" / "adaptateurs-harness" / "opencode.md"
        corps = adaptateur.read_text(encoding="utf-8")
        self.assertIn("retrait franc", corps)
        self.assertIn("opencode mcp list", corps)
        self.assertIn("réversible", corps)
        # Décision de l'utilisateur (2026-10-10) : le 5e critère reste **ouvert**,
        # tenu sur la **capacité** mais **pas sur la parole**. Que la fiche le dise,
        # sinon un lecteur croira le point tranché.
        self.assertIn("pas sur la parole", corps)
        self.assertIn("reste OUVERT", " ".join(corps.split()))

    def test_la_section_aionui_ne_coupe_aucune_autre_section(self):
        """Relecture adverse (2026-10-12) — F1 de la PR #178.

        La section AionUi avait été glissée **dans** ``## Rien ne l'attache``, dont
        la conclusion tombait alors sous le titre suivant : une section n'en
        englobe pas une autre. Elle ferme désormais la fiche, après ``## L'appel
        déporté``, et son renvoi interne dit « plus haut ». Ce test tient l'ordre ;
        le fond de la section, lui, se relit.
        """
        corps = FICHE.read_text(encoding="utf-8")
        titres = [ligne for ligne in corps.splitlines() if ligne.startswith("## ")]
        self.assertEqual(
            "## Le harnais AionUi — une liste centrale, un défaut par agent",
            titres[-1],
            "la section AionUi doit fermer la fiche, pas s'insérer au milieu")
        # La conclusion de `## Rien ne l'attache` appartient à sa section : le
        # titre suivant ne doit pas tomber avant elle.
        self.assertLess(
            corps.index("Un point a été "), corps.index("## Le constat d'acte"),
            "une section s'est glissée au milieu de `Rien ne l'attache`")
        aionui = corps[corps.index("## Le harnais AionUi"):]
        self.assertNotIn("plus bas", aionui,
                         "la section AionUi ferme la fiche : son renvoi est « plus haut »")

    # — outils —

    @staticmethod
    def _declaratifs(dossier, genre):
        return [fm for fm in (VC.verifier_fichier(p, genre)
                              for p in VC.fichiers_declaratifs(dossier)) if fm]

    def _agents(self):
        return self._declaratifs(RACINE / "IA" / "agents", "agent")

    def _skills(self):
        return self._declaratifs(RACINE / "IA" / "skills", "skill")


if __name__ == "__main__":
    unittest.main()
