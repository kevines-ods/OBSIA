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
from contextlib import redirect_stderr
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
