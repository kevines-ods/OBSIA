"""L'outil du skill `cron` : `appliquer_taches.py`, et son filtre `--tache`.

Rien ne touche la machine : registre, unités, enveloppes, archive et
configuration sont redirigés vers un dossier temporaire, et `systemctl` comme
`systemd-analyze` sont remplacés. Une tâche réservée à une autre machine ne
doit être posée que si on la nomme.
"""

import importlib.util
import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "IA" / "skills" / "cron" / "scripts" / "appliquer_taches.py"

_spec = importlib.util.spec_from_file_location("appliquer_taches", SCRIPT)
AT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(AT)

TACHE = """---
schema: 1
kind: tâche
name: {nom}
description: Tâche de test {nom}.
module: noyau
quand: "0 * * * *"
fuseau: Europe/Paris
mode: commande
exécutant: local
actif: true
---

## Commande

```bash
true
```
"""


class TestUneSeuleTache(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        taches = self.tmp / "tâches"
        taches.mkdir()
        for nom in ("alpha", "beta"):
            (taches / f"{nom}.md").write_text(TACHE.format(nom=nom), encoding="utf-8")
        self.appels = []
        for nom, valeur in (("TACHES", taches), ("UNITES", self.tmp / "unites"),
                            ("ENVELOPPES", self.tmp / "env"),
                            ("ARCHIVE", self.tmp / "archive"),
                            ("CONFIG", self.tmp / "appliquer.conf"),
                            # Absent par défaut : sans ce patch, le test lit le
                            # vrai coffre parent de la machine qui l'exécute.
                            ("COFFRE_PARENT", self.tmp / "coffre-absent"),
                            ("TACHES_COFFRE", self.tmp / "coffre-absent" / "0-PROJETS" / "tâches-planifiées")):
            p = mock.patch.object(AT, nom, valeur)
            p.start()
            self.addCleanup(p.stop)
        for nom, faux in (("calendrier_valide", lambda e: True),
                          ("systemctl", lambda *a: self.appels.append(a) or True)):
            p = mock.patch.object(AT, nom, faux)
            p.start()
            self.addCleanup(p.stop)

    def lancer(self, *args):
        sortie = io.StringIO()
        with mock.patch.object(sys, "argv", ["appliquer_taches.py", *args]), \
                redirect_stdout(sortie):
            code = AT.main()
        return code, sortie.getvalue()

    def timers(self):
        d = self.tmp / "unites"
        return sorted(p.name for p in d.glob("obsia-*.timer")) if d.is_dir() else []

    def test_par_defaut_tout_le_registre_est_pose(self):
        code, _ = self.lancer("--appliquer")
        self.assertEqual(code, 0)
        self.assertEqual(self.timers(), ["obsia-alpha.timer", "obsia-beta.timer"])

    def test_seule_la_tache_nommee_est_posee(self):
        code, sortie = self.lancer("--appliquer", "--tache", "beta")
        self.assertEqual(code, 0)
        self.assertEqual(self.timers(), ["obsia-beta.timer"])
        self.assertNotIn("alpha", sortie)
        self.assertIn(("enable", "--now", "obsia-beta.timer"), self.appels)

    def test_le_registre_du_coffre_est_fusionne(self):
        coffre_taches = self.tmp / "coffre" / "0-PROJETS" / "tâches-planifiées"
        coffre_taches.mkdir(parents=True)
        (coffre_taches / "gamma.md").write_text(TACHE.format(nom="gamma"), encoding="utf-8")
        with mock.patch.object(AT, "TACHES_COFFRE", coffre_taches):
            code, _ = self.lancer("--appliquer")
        self.assertEqual(code, 0)
        self.assertEqual(self.timers(),
                         ["obsia-alpha.timer", "obsia-beta.timer", "obsia-gamma.timer"])

    def test_un_nom_declare_aux_deux_registres_est_refuse(self):
        coffre_taches = self.tmp / "coffre" / "0-PROJETS" / "tâches-planifiées"
        coffre_taches.mkdir(parents=True)
        (coffre_taches / "alpha.md").write_text(TACHE.format(nom="alpha"), encoding="utf-8")
        with mock.patch.object(AT, "TACHES_COFFRE", coffre_taches):
            code, sortie = self.lancer("--appliquer")
        self.assertEqual(code, 2)
        self.assertIn("alpha", sortie)
        self.assertEqual(self.timers(), [])

    def test_registre_du_coffre_absent_ne_bloque_pas(self):
        # Le coffre parent n'existe pas sur cette machine (CI, démo) : aucune
        # tâche propre à cette installation, et aucun avertissement — rien à
        # y lire, et aucun coffre à y chercher.
        erreur = io.StringIO()
        with redirect_stderr(erreur):
            code, _ = self.lancer("--appliquer")
        self.assertEqual(code, 0)
        self.assertEqual(self.timers(), ["obsia-alpha.timer", "obsia-beta.timer"])
        self.assertIn(("enable", "--now", "obsia-beta.timer"), self.appels)
        self.assertEqual(erreur.getvalue(), "")

    def test_coffre_present_sans_registre_avertit(self):
        # Le coffre parent existe (marqueurs présents), mais sans
        # `0-PROJETS/tâches-planifiées/` — un registre déplacé là puis jamais
        # relu disparaîtrait sans avertissement.
        coffre = self.tmp / "coffre-present"
        (coffre / "0-SAVOIRS").mkdir(parents=True)
        with mock.patch.object(AT, "COFFRE_PARENT", coffre), \
                mock.patch.object(AT, "TACHES_COFFRE", coffre / "0-PROJETS" / "tâches-planifiées"):
            erreur = io.StringIO()
            with redirect_stderr(erreur):
                code, _ = self.lancer("--appliquer")
        self.assertEqual(code, 0)
        self.assertIn("aucun registre", erreur.getvalue())

    def test_la_forme_avec_egal_vaut_aussi(self):
        self.lancer("--appliquer", "--tache=alpha")
        self.assertEqual(self.timers(), ["obsia-alpha.timer"])

    def test_l_apercu_filtre_aussi_et_n_ecrit_rien(self):
        code, sortie = self.lancer("--tache", "alpha")
        self.assertEqual(code, 0)
        self.assertIn("alpha", sortie)
        self.assertNotIn("beta", sortie)
        self.assertEqual(self.timers(), [])

    def test_un_nom_inconnu_est_refuse_sans_rien_ecrire(self):
        code, sortie = self.lancer("--appliquer", "--tache", "gamma")
        self.assertNotEqual(code, 0)
        self.assertIn("gamma", sortie)
        self.assertEqual(self.timers(), [])
        self.assertEqual(self.appels, [])

    def test_tache_sans_nom_est_refusee(self):
        code, _ = self.lancer("--appliquer", "--tache")
        self.assertNotEqual(code, 0)
        self.assertEqual(self.timers(), [])

    def test_tache_repetee_est_refusee_sans_rien_ecrire(self):
        for args in (("--tache", "alpha", "--tache", "beta"),
                     ("--tache=alpha", "--tache", "beta"),
                     ("--tache=alpha", "--tache=alpha")):
            with self.subTest(args=args):
                code, sortie = self.lancer("--appliquer", *args)
                self.assertEqual(code, 2)
                self.assertIn("qu'une fois", sortie)
                self.assertEqual(self.timers(), [])
                self.assertEqual(self.appels, [])

    def test_retirer_ne_vise_que_la_tache_nommee(self):
        self.lancer("--appliquer")
        for nom in ("alpha", "beta"):
            chemin = self.tmp / "tâches" / f"{nom}.md"
            chemin.write_text(chemin.read_text(encoding="utf-8")
                              .replace("actif: true", "actif: false"), encoding="utf-8")
        self.lancer("--appliquer", "--tache", "alpha")
        self.assertEqual(self.timers(), ["obsia-beta.timer"])


if __name__ == "__main__":
    unittest.main()
