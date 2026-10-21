"""Contrôles de `scripts/verifier_coffre.py` (§5, §10.2, §13).

Le vérificateur travaille sur un état global : `RACINE`, `erreurs`,
`avertissements`. Chaque test installe donc son propre coffre temporaire et
des listes neuves, puis remet l'état d'origine — un test ne doit pas dépendre
de celui qui l'a précédé, ni laisser une trace derrière lui.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from io import StringIO
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))        # `scripts/` n'est pas un paquet

import regenerate_index as RI           # noqa: E402
import verifier_coffre as VC            # noqa: E402

DEFAUT = {"schema": "1", "read_only": "false", "module": "noyau"}


def git(depot: Path, *arguments: str):
    """git dans `depot` : les contrôles du dépôt de données en ont besoin."""
    return subprocess.run(["git", "-C", str(depot), *arguments],
                          capture_output=True, text=True, check=False)


class BaseVerificateur(unittest.TestCase):
    """Un coffre temporaire, et l'état global du vérificateur mis de côté."""

    def setUp(self):
        # Le dépôt vit **dans** un coffre parent : la mémoire est à côté de lui
        # (§7.1), donc les carnets ne sont pas sous `self.racine`.
        self.parent = Path(tempfile.mkdtemp(prefix="obsia-test-verif-"))
        self.racine = self.parent / "OBSIA"
        self.racine.mkdir()
        self.addCleanup(shutil.rmtree, self.parent, ignore_errors=True)

        self._racine_avant = VC.RACINE
        self._coffre_avant = VC.COFFRE
        self._erreurs_avant = list(VC.erreurs)
        self._avertissements_avant = list(VC.avertissements)
        self.addCleanup(self.restaurer)

        VC.RACINE = self.racine
        VC.COFFRE = self.parent
        VC.erreurs.clear()
        VC.avertissements.clear()

    def restaurer(self):
        VC.RACINE = self._racine_avant
        VC.COFFRE = self._coffre_avant
        VC.erreurs[:] = self._erreurs_avant
        VC.avertissements[:] = self._avertissements_avant

    def ecrire(self, relatif: str, contenu: str) -> Path:
        chemin = self.racine / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")
        return chemin

    def ecrire_coffre(self, relatif: str, contenu: str) -> Path:
        """Écrit dans le coffre parent — là où vit la mémoire (§7.1)."""
        chemin = self.racine.parent / relatif
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

    def neutraliser_les_derives(self) -> None:
        """Écarte le seul contrôle qui juge des fichiers hors du coffre du test.

        `verifier_derives()` lance `regenerate_index.py --verifier` sur les
        sources d'index du coffre : un coffre de test n'a ni agent ni skill à
        indexer, il répondrait donc « Aucun agent ou aucun skill collecté —
        index non régénéré » pour toutes les classes. Celles qui n'ont pas
        peuplé ces sources le demandent **explicitement**, et une classe qui
        veut prouver la vraie couture ne l'appelle pas.

        Rien n'était demandé avant : `executer()` la neutralisait pour tout le
        monde, et le seul contrôle qui regarde les index n'était exécuté nulle
        part — un index périmé serait passé sans un mot.
        """
        avant = VC.verifier_derives
        self.addCleanup(setattr, VC, "verifier_derives", avant)
        VC.verifier_derives = lambda: None

    def executer(self, *arguments: str) -> int:
        """Lance le vérificateur entier, comme la CI : c'est lui qu'on juge."""
        avant_argv = sys.argv
        self.addCleanup(setattr, sys, "argv", avant_argv)
        sys.argv = ["verifier_coffre.py", "--silencieux", *arguments]
        # Le rapport final part sur stderr, même en silencieux : le compte rendu
        # du test n'a pas à le porter, les messages sont dans `VC.erreurs`.
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            return VC.main()

    def erreurs_texte(self) -> str:
        return "\n".join(VC.erreurs)

    def avertissements_texte(self) -> str:
        return "\n".join(VC.avertissements)


class TestMemoireEmprunteeAuMoteur(BaseVerificateur):
    """« Qui est un agent » et les noms de mémoire n'ont qu'une définition (§6).

    Deux copies finiraient par diverger sur les noms mêmes qui séparent la
    mémoire vivante du chantier gelé : le vérificateur importe la copie unique
    du moteur partagé au lieu de la réécrire.
    """

    def test_les_noms_et_la_liste_des_agents_viennent_du_moteur(self):
        import convention_des_notes as MOTEUR
        self.assertIs(VC.liste_des_agents, MOTEUR.liste_des_agents)
        self.assertIs(VC.MEMOIRES, MOTEUR.MEMOIRES)
        self.assertIs(VC.PREFERENCES, MOTEUR.PREFERENCES)
        self.assertIs(VC.EXPERIENCES, MOTEUR.EXPERIENCES)

    def test_un_agent_se_declare_en_fichier_plat_ou_en_dossier(self):
        # Les deux formes du §5 comptent : un agent déclaré en dossier a lui
        # aussi une mémoire vivante, à ne pas confondre avec un chantier gelé.
        self.ecrire("IA/agents/plat.md", "---\nkind: agent\n---\n")
        self.ecrire("IA/agents/dossier/dossier.md", "---\nkind: agent\n---\n")
        self.assertEqual(VC.noms_d_agents_declares(), {"plat", "dossier"})


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

    def setUp(self):
        super().setUp()
        self.neutraliser_les_derives()

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

    def setUp(self):
        super().setUp()
        self.neutraliser_les_derives()

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
    """§6 : forme des carnets, un dossier par chantier, transition.

    La mémoire n'est plus dans le dépôt (§7.1) : les projets s'écrivent donc
    dans le coffre parent, à côté du dépôt, et non sous `self.racine`.
    """

    def setUp(self):
        super().setUp()
        # Sur le coffre lui-même, ses écarts sont des erreurs (§7.1) : c'est ce
        # que le pre-commit du dépôt de données vérifie. Depuis le dépôt produit,
        # les mêmes constats avertissent sans bloquer.
        self._strict_avant = VC.MEMOIRE_STRICTE
        self.addCleanup(setattr, VC, "MEMOIRE_STRICTE", self._strict_avant)
        VC.MEMOIRE_STRICTE = True
        # Deux cas de cette classe décrivent la tolérance de bascule, pas la date
        # du jour : sans épinglage ils rougissent d'eux-mêmes le 2027-01-01, sans
        # qu'une ligne de code ait bougé. Rendre l'horloge d'origine en sortie.
        self._date_avant = VC.date
        self.addCleanup(setattr, VC, "date", self._date_avant)

    def carnet(self, projet: str, nom: str, frontmatter: str) -> Path:
        return self.ecrire_coffre("0-PROJETS/%s/carnets/%s" % (projet, nom),
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

    def test_le_projet_d_un_carnet_de_chantier_est_le_chantier(self):
        """Niveau 1 : `projet:` porte le nom du **chantier**, pas du projet racine.

        C'est la règle que le gabarit du skill `cloture-de-session` doit écrire :
        le gabarit et le garde ont divergé, et les carnets de chantier étaient
        refusés.
        """
        self.ecrire_coffre(
            "0-PROJETS/obsia/refonte/carnets/2026-10-02-refonte-t1.md",
            "---\nagent: assistant\nprojet: obsia\nstatut: en cours\n---\n\nCorps.\n")

        VC.verifier_carnets()

        self.assertIn("`projet: obsia` ne correspond pas au dossier `refonte`",
                      self.erreurs_texte())

    def test_un_sous_dossier_dans_carnets_est_refuse(self):
        self.ecrire_coffre("0-PROJETS/un-projet/carnets/archive/vieux.md", "Corps.\n")
        VC.verifier_carnets()
        self.assertIn("sous-dossier dans `carnets/`", self.erreurs_texte())

    def test_les_archives_d_avant_la_cloture_avertissent(self):
        """`archives/` n'existe plus : un chantier clos part dans `0-MEMOIRES/`.

        Tant que la bascule dure, l'ancienne forme avertit sans faire échouer :
        le contrôle des carnets doit être utilisable pendant qu'on migre. Le
        dernier jour de la tolérance est épinglé : c'est le 2027-01-01 que la
        forme tombe, et un cas qui interroge l'horloge sans le dire rougit seul.
        """
        VC.date = FauxJour(date(2026, 12, 31))
        self.ecrire_coffre("0-PROJETS/un-projet/carnets/archives/vieux.md", "Corps.\n")
        self.ecrire_coffre("0-PROJETS/un-projet/archives/vieux.md", "Corps.\n")

        VC.verifier_carnets()

        self.assertEqual([], VC.erreurs, self.erreurs_texte())
        self.assertEqual(2, len(VC.avertissements), self.avertissements_texte())
        self.assertIn("0-MEMOIRES", self.avertissements_texte())

    def test_la_memoire_se_lit_dans_l_ancien_emplacement_aussi(self):
        """Clause de transition : `mémoire/projets` se lit tant que la bascule dure."""
        self.ecrire("mémoire/projets/un-projet/carnets/2026-10-02-un-projet-t1.md",
                    "---\nagent:\nprojet: un-projet\nstatut: en cours\n---\n\nCorps.\n")

        VC.verifier_carnets()

        self.assertIn("`agent:` vide", self.erreurs_texte())

    def test_une_note_datee_a_plat_est_toleree(self):
        """Tolérée jusqu'au dernier jour : la date est épinglée, pas lue."""
        VC.date = FauxJour(date(2026, 12, 31))
        self.ecrire_coffre("0-PROJETS/ancien-projet/2026-09-18-une-note.md",
                           "---\nagent: assistant\n---\n\nCorps.\n")
        VC.verifier_carnets()
        self.assertEqual([], VC.erreurs)
        self.assertIn("ancienne forme", self.avertissements_texte())

    def test_un_sous_projet_imbrique_est_refuse(self):
        self.ecrire_coffre("0-PROJETS/un-projet/sous/encore/fichier.md", "Corps.\n")
        VC.verifier_carnets()
        self.assertIn("chantier imbriqué", self.erreurs_texte())

    def test_un_seul_niveau_de_sous_projet_est_admis(self):
        self.carnet("un-projet", "2026-10-02-un-projet-t1.md",
                    "agent: assistant\nprojet: un-projet\nstatut: clos\n")
        self.ecrire_coffre("0-PROJETS/un-projet/sous/carnets/2026-10-02-sous-t1.md",
                           "---\nagent: assistant\nprojet: sous\nstatut: clos\n---\n\nCorps.\n")
        VC.verifier_carnets()
        self.assertEqual([], VC.erreurs)


class TestGabaritDuCarnet(unittest.TestCase):
    """Le gabarit du carnet nomme le dossier porteur (§6).

    Ce test fige le **texte du skill** `cloture-de-session` : le gabarit se lit
    et se recopie, il n'est pas vérifié par le garde — c'est le carnet écrit
    d'après lui qui l'est, dans `TestCarnets`. Échouer ici signale donc au
    rédacteur du skill qu'il s'écarte de la règle du garde.
    """

    def setUp(self):
        depot = Path(__file__).resolve().parents[1]
        self.gabarit = (depot / "IA" / "skills" / "cloture-de-session.md").read_text(
            encoding="utf-8")

    def test_le_nom_du_carnet_porte_le_chantier(self):
        self.assertIn("AAAA-MM-JJ-<chantier>-<sujet>.md", self.gabarit)

    def test_le_champ_projet_du_gabarit_porte_le_chantier(self):
        self.assertIn("projet: <chantier>", self.gabarit)


class TestNomsDeMemoire(BaseVerificateur):
    """§6 : dans `0-MEMOIRES/`, deux mémoires ne se confondent pas.

    Le dossier porte la mémoire **vivante** des agents — `préférences/` et
    `<nom-agent>/expériences/` — **et** les chantiers clos, gelés. Un projet qui
    prendrait le nom d'un agent ou celui de `préférences/` rendrait les deux
    indistinguables : le contrôle le refuse, par la forme faute de lire une
    intention.
    """

    def setUp(self):
        super().setUp()
        self.neutraliser_les_derives()
        self._strict_avant = VC.MEMOIRE_STRICTE
        self.addCleanup(setattr, VC, "MEMOIRE_STRICTE", self._strict_avant)
        VC.MEMOIRE_STRICTE = True
        self.fiche("agent", "batisseur", {"description": "Agent de test."})

    def dossier(self, relatif: str) -> Path:
        chemin = self.racine.parent / relatif
        chemin.mkdir(parents=True, exist_ok=True)
        return chemin

    def test_une_memoire_bien_formee_est_muette(self):
        self.ecrire_coffre("0-MEMOIRES/préférences/langue-des-notes.md", "Corps.\n")
        self.ecrire_coffre("0-MEMOIRES/batisseur/expériences/un-verrou-qui-tient.md",
                           "Corps.\n")
        self.dossier("0-MEMOIRES/obsia/souverainete-des-donnees")

        VC.verifier_noms_de_memoire()

        self.assertEqual([], VC.erreurs, self.erreurs_texte())

    def test_un_projet_ne_peut_pas_s_appeler_preferences(self):
        """Sous `préférences/`, un dossier est un projet qui a volé le nom."""
        self.dossier("0-MEMOIRES/préférences/un-projet")

        VC.verifier_noms_de_memoire()

        self.assertIn("Un projet ne peut pas porter ce nom", self.erreurs_texte())

    def test_un_projet_ne_peut_pas_porter_le_nom_d_un_agent(self):
        self.dossier("0-MEMOIRES/batisseur/chantier-gelat")

        VC.verifier_noms_de_memoire()

        self.assertIn("ne peut pas porter le nom d'un agent", self.erreurs_texte())

    def test_un_projet_gele_sans_chantier_est_refuse(self):
        self.dossier("0-MEMOIRES/obsia")

        VC.verifier_noms_de_memoire()

        self.assertIn("projet gelé sans chantier", self.erreurs_texte())

    def test_un_dossier_inconnu_au_premier_niveau_est_refuse(self):
        self.ecrire_coffre("0-MEMOIRES/une-note-egaree.md", "Corps.\n")

        VC.verifier_noms_de_memoire()

        self.assertIn("n'accueille que des dossiers", self.erreurs_texte())

    def test_sans_coffre_parent_il_n_y_a_rien_a_controler(self):
        """Un clone de la CI n'a pas de `0-MEMOIRES/` : le contrôle se tait."""
        VC.verifier_noms_de_memoire()

        self.assertEqual([], VC.erreurs)

    def test_le_controle_tourne_dans_la_verification(self):
        """Il part avec les autres : une mémoire mal nommée ne passe pas."""
        self.dossier("0-MEMOIRES/préférences/un-projet")

        self.executer("--coffre", str(self.racine.parent))

        self.assertIn("Un projet ne peut pas porter ce nom", self.erreurs_texte())


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


class TestLigneDeCommandeDuCoffre(BaseVerificateur):
    """`--coffre <chemin>` et `--carnets` : ce que le pre-commit du dépôt de
    données appelle (§7.1). Sur ce coffre-là, la mémoire est jugée strictement —
    un carnet mal formé refuse le commit."""

    GABARIT = "IA/system/depot-de-donnees/gitignore-coffre"
    LISTE = "/*\n!/.gitignore\n!/0-*/\n!/_MAINTENANCE/\n"

    def setUp(self):
        super().setUp()
        self.neutraliser_les_derives()

    def preparer(self):
        """Le coffre est outillé : gabarit présent, liste blanche conforme."""
        self.ecrire(self.GABARIT, self.LISTE)
        (self.parent / ".gitignore").write_text(self.LISTE, encoding="utf-8")

    def test_les_carnets_conformes_sortent_en_zero(self):
        self.preparer()
        self.ecrire_coffre("0-PROJETS/un-projet/carnets/2026-01-01-un-projet-vrille.md",
                           "---\nagent: batisseur\nprojet: un-projet\nstatut: en cours\n"
                           "---\n\nCorps.\n")
        self.assertEqual(0, self.executer("--coffre", str(self.parent), "--carnets"),
                         self.erreurs_texte())

    def test_un_carnet_fautif_sort_en_un(self):
        self.preparer()
        self.ecrire_coffre("0-PROJETS/un-projet/carnets/carnet.md",
                           "---\nagent: batisseur\nprojet: un-projet\nstatut: en cours\n"
                           "---\n\nCorps.\n")
        self.assertEqual(1, self.executer("--coffre", str(self.parent), "--carnets"))
        self.assertIn("carnet mal nommé", self.erreurs_texte())

    def test_une_liste_blanche_absente_est_une_erreur(self):
        """Le gabarit est là, le coffre n'a pas encore sa liste blanche."""
        self.ecrire(self.GABARIT, self.LISTE)
        self.assertEqual(1, self.executer("--coffre", str(self.parent), "--carnets"))
        self.assertIn("liste blanche", self.erreurs_texte())

    def test_un_argument_inconnu_sort_en_deux(self):
        self.assertEqual(2, self.executer("--gribouille"))

    def test_un_coffre_non_designe_n_est_pas_juge(self):
        """Sans `--coffre`, la mémoire du voisin avertit sans rien refuser : le
        dépôt produit ne se met pas à refuser ses commits pour un carnet — le
        contrôle du coffre, lui, a ses propres crochets (§7.1, M5)."""
        VC.MEMOIRE_STRICTE = False
        self.ecrire_coffre("0-PROJETS/un-projet/carnets/carnet.md",
                           "---\nagent: batisseur\nprojet: un-projet\n---\n\nCorps.\n")
        VC.verifier_carnets()
        self.assertEqual([], VC.erreurs)
        self.assertTrue(VC.avertissements)


class TestDepotDeDonnees(BaseVerificateur):
    """§7.1 : la liste blanche du coffre est le gabarit, et le dépôt produit
    n'entre jamais dans la mémoire."""

    GABARIT = "IA/system/depot-de-donnees/gitignore-coffre"
    LISTE = "/*\n!/.gitignore\n!/0-*/\n"

    def setUp(self):
        super().setUp()
        self._strict_avant = VC.MEMOIRE_STRICTE
        self.addCleanup(setattr, VC, "MEMOIRE_STRICTE", self._strict_avant)
        VC.MEMOIRE_STRICTE = True

    def test_un_gabarit_absent_est_une_erreur(self):
        VC.verifier_depot_de_donnees()
        self.assertIn("gabarit de la liste blanche du coffre absent",
                      self.erreurs_texte())

    def test_une_liste_blanche_conforme_passe(self):
        self.ecrire(self.GABARIT, self.LISTE)
        (self.parent / ".gitignore").write_text(self.LISTE, encoding="utf-8")
        VC.verifier_depot_de_donnees()
        self.assertEqual([], VC.erreurs, self.erreurs_texte())

    def test_une_liste_blanche_retouchee_est_signalee(self):
        self.ecrire(self.GABARIT, self.LISTE)
        (self.parent / ".gitignore").write_text(self.LISTE + "!/secret/\n",
                                                encoding="utf-8")
        VC.verifier_depot_de_donnees()
        self.assertIn("diffère du gabarit", self.erreurs_texte())

    def test_le_depot_produit_suivi_par_la_memoire_est_signale(self):
        self.ecrire(self.GABARIT, self.LISTE)
        (self.parent / ".gitignore").write_text(self.LISTE, encoding="utf-8")
        self.ecrire("IA/README.md", "# Racine\n")
        git(self.parent, "init", "--quiet")
        git(self.parent, "add", "-f", "OBSIA/IA/README.md")
        VC.verifier_depot_de_donnees()
        self.assertIn("dépôt produit est suivi", self.erreurs_texte())

    def test_un_coffre_sans_depot_git_est_accepte(self):
        """La liste blanche seule suffit : le dépôt de données viendra après."""
        self.ecrire(self.GABARIT, self.LISTE)
        (self.parent / ".gitignore").write_text(self.LISTE, encoding="utf-8")
        VC.verifier_depot_de_donnees()
        self.assertEqual([], VC.erreurs, self.erreurs_texte())


class FauxJour:
    """Un `datetime.date` de rechange : `today()` renvoie un jour fixe.

    `verifier_bascule` lit la date du jour ; sans ce bouchon, on ne pourrait
    éprouver l'échéance qu'en attendant 2027.
    """

    def __init__(self, jour: date):
        self.jour = jour

    def today(self) -> date:
        return self.jour

    @staticmethod
    def fromisoformat(texte: str) -> date:
        return date.fromisoformat(texte)


class TestBasculeDatée(BaseVerificateur):
    """§6 (transition) : la tolérance datée — avertissement, puis erreur.

    Jusqu'au 2026-12-31, l'ancienne forme de la mémoire se tolère : la
    migration est en cours. Passé ce jour, sa survie fait échouer le contrôle —
    une tolérance qu'on ne paie pas ne se retire pas.
    """

    GABARIT = TestDepotDeDonnees.GABARIT
    LISTE = TestDepotDeDonnees.LISTE

    def setUp(self):
        super().setUp()
        self._date_avant = VC.date
        self.addCleanup(setattr, VC, "date", self._date_avant)

    def coffre_prepare(self):
        """Un coffre minimal valide : la liste blanche et son gabarit."""
        self.ecrire(self.GABARIT, self.LISTE)
        (self.parent / ".gitignore").write_text(self.LISTE, encoding="utf-8")

    def test_avant_le_jour_dit_l_ancien_memoire_est_tolere(self):
        self.ecrire("mémoire/projets/obsia/carnets.md", "Ancien carnet.\n")
        VC.verifier_bascule(date(2026, 12, 31))
        self.assertEqual([], VC.erreurs, self.erreurs_texte())

    def test_apres_le_jour_dit_l_ancien_memoire_est_une_erreur(self):
        self.ecrire("mémoire/projets/obsia/carnets.md", "Ancien carnet.\n")
        VC.verifier_bascule(date(2027, 1, 1))
        self.assertIn("bascule non achevée", self.erreurs_texte())
        self.assertIn("mémoire", self.erreurs_texte())

    def test_avant_le_jour_dit_session_log_est_tolere(self):
        """`session-log/` est de la mémoire : il suit `mémoire/`, sans plus."""
        self.ecrire("IA/system/session-log/2026-09-01-seance.md", "Séance.\n")
        VC.verifier_bascule(date(2026, 12, 31))
        self.assertEqual([], VC.erreurs, self.erreurs_texte())

    def test_apres_le_jour_dit_session_log_est_une_erreur(self):
        self.ecrire("IA/system/session-log/2026-09-01-seance.md", "Séance.\n")
        VC.verifier_bascule(date(2027, 1, 1))
        self.assertIn("bascule non achevée", self.erreurs_texte())
        self.assertIn("session-log", self.erreurs_texte())

    def test_apres_le_jour_dit_un_dossier_tiret_est_une_erreur(self):
        self.coffre_prepare()
        (self.parent / "-PROJETS").mkdir()
        VC.verifier_bascule(date(2027, 1, 1))
        self.assertIn("bascule non achevée", self.erreurs_texte())
        self.assertIn("-PROJETS", self.erreurs_texte())

    def test_un_coffre_migre_passe_apres_le_jour_dit(self):
        self.coffre_prepare()
        (self.parent / "0-PROJETS").mkdir()
        VC.verifier_bascule(date(2027, 1, 1))
        self.assertEqual([], VC.erreurs, self.erreurs_texte())

    def test_un_tiret_hors_coffre_ne_fait_pas_echouer(self):
        """Un dossier `-…` chez un inconnu n'est pas un vestige de notre bascule."""
        (self.parent / "-brouillons").mkdir()
        VC.verifier_bascule(date(2027, 1, 1))
        self.assertEqual([], VC.erreurs, self.erreurs_texte())

    def test_main_refuse_apres_le_jour_dit(self):
        """L'échéance est branchée : le contrôle complet échoue, pas seulement
        la fonction appelée seule."""
        self.coffre_prepare()
        (self.parent / "-PROJETS").mkdir()
        VC.date = FauxJour(date(2027, 1, 1))
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            code = VC.main(["--carnets", "--silencieux"])
        self.assertEqual(1, code)
        self.assertIn("bascule non achevée", self.erreurs_texte())


class TestBasculeDesFormesTolerees(BaseVerificateur):
    """§11 : la tolérance des formes d'attente tombe le 2026-12-31, elle aussi.

    `signaler_bascule` avertissait sans condition : une note datée à plat, un
    dossier `archives/` restaient des avertissements éternels après le jour dit,
    alors que le même vestige sous l'ancienne forme faisait échouer le contrôle.
    Deux poids, deux mesures pour une seule échéance. Le jour est forcé par le
    paramètre `aujourdhui`, ou par `FauxJour` quand c'est `verifier_carnets` qui
    lit la date, pour que ces cas ne dépendent pas de l'horloge de la machine.
    """

    def setUp(self):
        super().setUp()
        self._date_avant = VC.date
        self.addCleanup(setattr, VC, "date", self._date_avant)

    # --- le jour d'aujourd'hui : rien ne change, c'est interdit

    def test_aujourd_hui_une_note_a_plat_reste_toleree(self):
        """Le 2026-10-17, le coffre doit rester tolérant : avertir, pas refuser."""
        VC.date = FauxJour(date(2026, 10, 17))
        self.ecrire_coffre("0-PROJETS/essai/2026-09-01-note.md", "Note.\n")
        VC.verifier_carnets()
        self.assertEqual([], VC.erreurs, self.erreurs_texte())
        self.assertTrue(any("tolérance de bascule" in a for a in VC.avertissements),
                        VC.avertissements)

    # `main` n'est pas appelé ici, et c'est un choix de budget : chaque passage
    # coûte un processus par `verifier_depot_de_donnees`, pour cinq de marge.
    # Les trois points d'appel de `signaler_bascule` passent tous par
    # `verifier_carnets`, qui est donc l'étage où la chaîne se prouve.

    # --- les deux bords

    def test_le_dernier_jour_la_tolerance_avertit_encore(self):
        VC.signaler_bascule("x.md", "note datée", aujourdhui=date(2026, 12, 31))
        self.assertEqual([], VC.erreurs, self.erreurs_texte())
        self.assertIn("tolérance de bascule", VC.avertissements[0])
        self.assertIn("2026-12-31", VC.avertissements[0])

    def test_le_premier_jour_apres_la_tolerance_est_une_erreur(self):
        VC.signaler_bascule("x.md", "note datée", aujourdhui=date(2027, 1, 1))
        self.assertEqual([], VC.avertissements)
        self.assertIn("bascule non achevée", self.erreurs_texte())
        self.assertIn("x.md", self.erreurs_texte())
        self.assertIn("2026-12-31", self.erreurs_texte())
        self.assertIn("§11", self.erreurs_texte())
        self.assertIn("souverainete-des-donnees", self.erreurs_texte())

    # --- les trois formes que `signaler_bascule` excuse

    def test_une_note_a_plat_refusee_apres_le_jour_dit(self):
        """Le message doit dire où la mémoire doit vivre, pas seulement quand.

        Les trois assertions qui suivent sont nées d'une mutation : retirer
        « (§6) » des trois points d'appel laissait la suite entièrement verte.
        Le chemin était exercé, le message n'était épinglé par rien.
        """
        VC.date = FauxJour(date(2027, 1, 1))
        self.ecrire_coffre("0-PROJETS/essai/2026-09-01-note.md", "Note.\n")
        VC.verifier_carnets()
        self.assertIn("bascule non achevée", self.erreurs_texte())
        self.assertIn("2026-09-01-note.md", self.erreurs_texte())
        # La §6 dit où la mémoire doit vivre, la §11 quand la tolérance tombe :
        # n'en citer qu'une laisse le lecteur avec la moitié du chemin.
        self.assertIn("§6", self.erreurs_texte())
        self.assertIn("§11", self.erreurs_texte())
        self.assertIn("à migrer vers `carnets/`", self.erreurs_texte())

    def test_un_archives_de_projet_refuse_apres_le_jour_dit(self):
        VC.date = FauxJour(date(2027, 1, 1))
        self.ecrire_coffre("0-PROJETS/essai/archives/2026-09-01-vieux.md", "Vieux.\n")
        VC.verifier_carnets()
        self.assertIn("bascule non achevée", self.erreurs_texte())
        self.assertIn("archives", self.erreurs_texte())
        # Chaque point d'appel porte sa propre destination : ici `0-MEMOIRES/`,
        # pas `carnets/`. Sans ces deux lignes, retirer « (§6) » de cet appel
        # laissait la suite entièrement verte — la preuve ne couvrait qu'un appel.
        self.assertIn("§6", self.erreurs_texte())
        self.assertIn("0-MEMOIRES/", self.erreurs_texte())

    def test_un_archives_de_projet_reste_tolere_avant_le_jour_dit(self):
        VC.date = FauxJour(date(2026, 12, 31))
        self.ecrire_coffre("0-PROJETS/essai/archives/2026-09-01-vieux.md", "Vieux.\n")
        VC.verifier_carnets()
        self.assertEqual([], VC.erreurs, self.erreurs_texte())
        self.assertTrue(any("tolérance de bascule" in a for a in VC.avertissements),
                        VC.avertissements)

    def test_un_archives_de_carnets_refuse_apres_le_jour_dit(self):
        """Le troisième point d'appel : les archives sous `carnets/` du projet."""
        VC.date = FauxJour(date(2027, 1, 1))
        self.ecrire_coffre("0-PROJETS/essai/carnets/archives/2026-09-01-vieux.md",
                           "Vieux.\n")
        VC.verifier_carnets()
        self.assertIn("bascule non achevée", self.erreurs_texte())
        self.assertIn("carnets/archives", self.erreurs_texte())
        # Le troisième appel a sa destination à lui, et sa propre §6 : c'est la
        # même exigence que les deux autres, vérifiée séparément parce qu'une
        # assertion posée sur un appel ne prouve rien des deux autres.
        self.assertIn("§6", self.erreurs_texte())
        self.assertIn("0-MEMOIRES/", self.erreurs_texte())


class TestTailleDuFichierAgents(BaseVerificateur):
    """L'`AGENTS.md` écrit ne doit pas approcher le plafond de consignes de Codex.

    Codex ne retient en tout que 32 Kio — fichier global et fichiers du projet
    ensemble — et au-delà, le surplus est laissé de côté sans rien dire : l'agent
    perd des agents et des skills entiers. Le contrôle mesure le pire cas — le
    catalogue entier, profil ignoré, comme la CI — sur le texte que l'installeur
    écrit vraiment, marqueur compris, et avertit dès 28 Kio.
    """

    def fichier_de_taille(self, cible: int) -> int:
        """Un coffre dont l'`AGENTS.md` écrit fait exactement `cible` octets.

        La description d'un agent se retrouve telle quelle dans le fichier : on
        la calibre, plutôt que de deviner la taille du gabarit. La cible doit
        dépasser ce gabarit, sinon la description serait à raccourcir sous zéro.
        """
        import generer_prompt as GP
        import installer

        def ecrire(longueur: int) -> None:
            self.ecrire(
                "IA/agents/agent-gros.md",
                "---\nschema: 1\nkind: agent\nname: agent-gros\n"
                "description: %s\nread_only: false\nmodule: noyau\n---\n\nCorps.\n"
                % ("x" * longueur))

        def mesurer() -> int:
            # `collecter` signale « dossier absent » pour ce coffre-ci, qui n'a ni
            # skills, ni tâches, ni MCP : on tait ce bavardage de test.
            with redirect_stderr(StringIO()):
                prompt = GP.prompt_du_coffre(self.racine, sans_profil=True)
            return len(installer.contenu_agents(prompt).encode("utf-8"))

        ecrire(1)
        gabarit = mesurer()
        if cible < gabarit:
            raise ValueError("la cible %d est sous le gabarit du coffre (%d)"
                             % (cible, gabarit))
        ecrire(1 + cible - gabarit)
        return mesurer()

    def test_les_seuils_sont_ceux_de_codex(self):
        """28 Kio d'avance sur le plafond de 32 Kio : les nombres sont la règle."""
        self.assertEqual(28672, VC.TAILLE_FICHIER_AGENTS_AVERTISSEMENT)
        self.assertEqual(32768, VC.TAILLE_FICHIER_AGENTS_ERREUR)

    def test_l_avertissement_laisse_une_marge_avant_le_plafond(self):
        """Alerter collé au plafond ne laisserait rien à faire quand il sonne.

        Les 4 Kio de marge servent deux fois : le temps de réduire le catalogue,
        et le fichier global de Codex, qui partage le budget.
        """
        self.assertLess(VC.TAILLE_FICHIER_AGENTS_AVERTISSEMENT, VC.TAILLE_FICHIER_AGENTS_ERREUR)
        self.assertEqual(4 * 1024,
                         VC.TAILLE_FICHIER_AGENTS_ERREUR - VC.TAILLE_FICHIER_AGENTS_AVERTISSEMENT)
        self.assertEqual(32 * 1024, VC.TAILLE_FICHIER_AGENTS_ERREUR)   # le plafond de Codex

    def test_un_profil_local_ne_rapetissit_pas_la_mesure(self):
        """On mesure le catalogue entier — pas le rendu au profil courant.

        C'est le pire cas, celui de la CI, où `obsia.local.yml` n'est pas
        versionné et n'existe donc pas. Se caler sur le rendu du profil
        laisserait passer, sur toute machine dotée d'un profil, un dépassement
        que la CI refuse. Le coffre est calé pour que le profil écarte juste
        assez — son rendu tombe à un octet sous le seuil, le catalogue le
        dépasse de plus de deux Kio — : seul le catalogue entier avertit.
        """
        import generer_prompt as GP
        import installer
        import modules

        self.ecrire("IA/system/modules/noyau.md",
                    "---\nschema: 1\nkind: module\nname: noyau\n"
                    "description: Le socle.\nessentiel: true\n---\n")
        self.ecrire("IA/system/modules/gros.md",
                    "---\nschema: 1\nkind: module\nname: gros\n"
                    "description: Un module qu'un profil peut écarter.\n"
                    "essentiel: false\n---\n")
        self.ecrire("obsia.local.yml", "schema: 1\nmodules:\n  - noyau\n")
        self.assertEqual(["noyau"], sorted(modules.modules_actifs(self.racine)))

        def ecrire_agent(nom: str, module: str, longueur: int) -> None:
            """Sa description règle la taille, octet pour octet."""
            self.ecrire(
                "IA/agents/agent-%s.md" % nom,
                "---\nschema: 1\nkind: agent\nname: agent-%s\n"
                "description: %s\nread_only: false\nmodule: %s\n---\n\nCorps.\n"
                % (nom, "x" * longueur, module))

        def mesurer(sans_profil: bool) -> int:
            with redirect_stderr(StringIO()):
                prompt = GP.prompt_du_coffre(self.racine, sans_profil=sans_profil)
            return len(installer.contenu_agents(prompt).encode("utf-8"))

        # L'agent retenu porte la taille ; l'écarté ne s'ajoute qu'au catalogue.
        seuil = VC.TAILLE_FICHIER_AGENTS_AVERTISSEMENT
        ecrire_agent("noyau", "noyau", 1)
        ecrire_agent("gros", "gros", 2 * 1024)
        ecrire_agent("noyau", "noyau",
                     1 + (seuil - 1) - mesurer(sans_profil=False))

        rendu = mesurer(sans_profil=False)
        entier = mesurer(sans_profil=True)

        self.assertEqual(seuil - 1, rendu)               # le profil passe dessous
        self.assertGreater(entier - seuil, 2 * 1024)     # le catalogue, non
        self.assertLessEqual(entier, VC.TAILLE_FICHIER_AGENTS_ERREUR)

        VC.verifier_taille_du_fichier_agents()

        self.assertEqual([], VC.erreurs, self.erreurs_texte())
        self.assertEqual(1, len(VC.avertissements), self.avertissements_texte())
        self.assertIn(str(entier), VC.avertissements[0])

    def test_la_taille_compte_le_marqueur_que_l_installeur_ecrit(self):
        """Le fichier écrit porte un marqueur en tête : le mesurer, c'est le lire.

        Mesurer le prompt seul laisserait passer un fichier déjà au-delà du
        plafond — l'angle mort que la relecture a relevé.
        """
        import generer_prompt as GP
        import installer

        taille = self.fichier_de_taille(4096)
        with redirect_stderr(StringIO()):
            prompt = GP.prompt_du_coffre(self.racine, sans_profil=True)
        ecrit = installer.contenu_agents(prompt)

        self.assertTrue(ecrit.startswith(installer.MARQUEUR_AGENTS))
        # Le marqueur, sa ligne vide, puis le prompt : voilà l'écart exact.
        self.assertEqual(
            len(ecrit.encode("utf-8")),
            len((prompt + "\n").encode("utf-8"))
            + len(installer.MARQUEUR_AGENTS.encode("utf-8")) + 2)
        self.assertEqual(4096, taille)

    def test_sous_le_seuil_rien_n_est_signale(self):
        """Sous 28 Kio, le fichier a de la marge : ni erreur ni avertissement."""
        taille = self.fichier_de_taille(VC.TAILLE_FICHIER_AGENTS_AVERTISSEMENT - 1)

        VC.verifier_taille_du_fichier_agents()

        self.assertEqual(VC.TAILLE_FICHIER_AGENTS_AVERTISSEMENT - 1, taille)
        self.assertEqual([], VC.erreurs, self.erreurs_texte())
        self.assertEqual([], VC.avertissements, self.avertissements_texte())

    def test_entre_les_deux_seuils_avertit_sans_refuser(self):
        """Entre 28 et 32 Kio : la marge se réduit, mais le fichier passe."""
        taille = self.fichier_de_taille(VC.TAILLE_FICHIER_AGENTS_AVERTISSEMENT + 1)

        VC.verifier_taille_du_fichier_agents()

        self.assertEqual([], VC.erreurs, self.erreurs_texte())
        self.assertEqual(1, len(VC.avertissements), self.avertissements_texte())
        message = VC.avertissements[0]
        self.assertIn(str(taille), message)                          # la taille
        self.assertIn(str(VC.TAILLE_FICHIER_AGENTS_AVERTISSEMENT), message)  # le seuil
        self.assertIn("Codex", message)                              # la raison
        self.assertIn("32 Kio", message)                             # vers quoi
        self.assertIn("fichier global", message)                     # la marge

    def test_au_dessus_du_plafond_de_codex_refuse(self):
        """Au-delà de 32 Kio, le surplus est déjà laissé de côté : c'est une erreur."""
        taille = self.fichier_de_taille(VC.TAILLE_FICHIER_AGENTS_ERREUR + 1)

        VC.verifier_taille_du_fichier_agents()

        self.assertEqual(1, len(VC.erreurs), self.erreurs_texte())
        message = VC.erreurs[0]
        self.assertIn(str(taille), message)
        self.assertIn(str(VC.TAILLE_FICHIER_AGENTS_ERREUR), message)
        self.assertIn("Codex", message)
        self.assertIn("laissé de côté", message)
        self.assertEqual([], VC.avertissements, self.avertissements_texte())


class TestPlafondDuNoyau(BaseVerificateur):
    """§11 : le noyau du contrat a un plafond, déclaré à un seul endroit.

    Le noyau est lu **en entier** par tout agent au démarrage : le laisser
    grossir, c'est payer ce poids à chaque séance. Le plafond vit dans son
    unique endroit déclaré — la table de `CONSTRAINTS.md`, ligne « Noyau du
    contrat », comme le plancher de tests — et le contrôle affiche à chaque
    passage la taille, le plafond et l'écart.
    """

    LIGNE = ("| Noyau du contrat | **≤ 4 560 mots** — le plafond descend, il ne "
             "monte pas en silence | `scripts/verifier_coffre.py` | chaque poussée |\n")

    def declarer(self, ligne: str = LIGNE) -> None:
        self.ecrire("CONSTRAINTS.md",
                    "| Dimension | Règle | Vérifié par | Quand |\n"
                    "| --- | --- | --- | --- |\n" + ligne)

    def noyau_de(self, mots: int) -> Path:
        """Un noyau de `mots` mots, sans avoir à calibrer un vrai texte."""
        return self.ecrire("IA/system/VAULT-CONTRACT.md",
                           " ".join("mot%d" % i for i in range(mots)) + "\n")

    def test_le_plafond_est_lu_a_son_unique_endroit_declare(self):
        self.declarer()
        self.assertEqual(4560, VC.plafond_du_noyau())

    def test_la_ligne_dit_la_taille_le_plafond_et_l_ecart(self):
        self.declarer()
        self.noyau_de(4553)

        ligne = VC.verifier_taille_du_noyau()

        self.assertIn("4553", ligne)      # la taille
        self.assertIn("4560", ligne)      # le plafond
        self.assertIn("marge 7", ligne)   # l'écart
        self.assertEqual([], VC.erreurs, self.erreurs_texte())

    def test_au_dessus_du_plafond_le_verificateur_refuse(self):
        self.declarer()
        self.noyau_de(4600)

        VC.verifier_taille_du_noyau()

        self.assertEqual(1, len(VC.erreurs), self.erreurs_texte())
        message = VC.erreurs[0]
        self.assertIn("4600", message)             # la taille
        self.assertIn("4560", message)             # le plafond
        self.assertIn("40 au-dessus", message)     # l'écart
        self.assertIn("VAULT-CONTRACT", message)   # où regarder

    def test_un_plafond_non_declare_est_une_erreur(self):
        """Sans la ligne déclarée, le noyau grossirait sans que rien ne le dise."""
        self.declarer("")
        self.noyau_de(10)

        VC.verifier_taille_du_noyau()

        self.assertEqual(1, len(VC.erreurs), self.erreurs_texte())
        self.assertIn("Noyau du contrat", VC.erreurs[0])

    def test_sans_noyau_rien_n_est_mesure(self):
        """Un clone sans noyau — ou un dossier de mémoire — n'a rien à mesurer."""
        self.declarer()

        self.assertIsNone(VC.verifier_taille_du_noyau())
        self.assertEqual([], VC.erreurs, self.erreurs_texte())
        self.assertEqual([], VC.avertissements, self.avertissements_texte())

    def test_le_vrai_noyau_du_depot_tient_dans_son_plafond(self):
        """La garantie du dépôt, sur ses vrais fichiers : déclaration et noyau d'accord."""
        racine = Path(__file__).resolve().parent.parent
        plafond = VC.plafond_du_noyau(racine / "CONSTRAINTS.md")
        mots = VC.mots_du_noyau(racine / "IA" / "system" / "VAULT-CONTRACT.md")

        self.assertIsNotNone(plafond, "le plafond du noyau doit être déclaré")
        self.assertLessEqual(
            mots, plafond,
            "le noyau (%d mots) dépasse son plafond (%d)" % (mots, plafond))


class TestRegleDesSecretsDuNoyau(BaseVerificateur):
    """§4 : le bloc de la règle des secrets est là, entre ses repères.

    `generer_prompt.regle_des_secrets` rend ``""`` quand les repères
    `regle-secrets` quittent le noyau : le prompt engendré — et donc l'`AGENTS.md`
    lu par l'agent — perdent alors la règle **en silence**. Le test du générateur
    vit dans le dépôt produit ; ce contrôle-ci le dit depuis le coffre, là où
    l'amendement du §4 atterrit.
    """

    NOYAU = "IA/system/VAULT-CONTRACT.md"

    def noyau(self, texte: str) -> None:
        self.ecrire(self.NOYAU, texte)

    def test_un_bloc_vide_est_refuse(self):
        self.noyau("<!-- regle-secrets: debut -->\n"
                   "\n"
                   "<!-- regle-secrets: fin -->\n")

        ligne = VC.verifier_regle_des_secrets()

        self.assertEqual(1, len(VC.erreurs), self.erreurs_texte())
        self.assertIn("vide ou introuvable", VC.erreurs[0])
        self.assertIn("AGENTS.md", VC.erreurs[0])
        self.assertIn("rétablir le bloc", VC.erreurs[0])
        self.assertEqual("Règle des secrets : bloc vide ou introuvable.", ligne)

    def test_des_reperes_disparus_rendent_le_meme_refus(self):
        """Sans repères, l'extraction rend le vide : même refus, même message."""
        self.noyau("Le §4 est là, mais plus entre ses repères.\n")

        VC.verifier_regle_des_secrets()

        self.assertEqual(1, len(VC.erreurs), self.erreurs_texte())
        self.assertIn("vide ou introuvable", VC.erreurs[0])

    def test_un_bloc_present_est_compte_sans_erreur(self):
        self.noyau("<!-- regle-secrets: debut -->\n"
                   "Les secrets ne sortent jamais du coffre.\n"
                   "<!-- regle-secrets: fin -->\n")

        ligne = VC.verifier_regle_des_secrets()

        self.assertEqual([], VC.erreurs, self.erreurs_texte())
        self.assertTrue(ligne.startswith("Règle des secrets : "), ligne)
        self.assertIn("caractères", ligne)

    def test_sans_noyau_le_controle_se_tait(self):
        """Un clone sans contrat n'a rien à dire ici."""
        self.assertIsNone(VC.verifier_regle_des_secrets())
        self.assertEqual([], VC.erreurs, self.erreurs_texte())


class TestClausesDateesDuNoyau(BaseVerificateur):
    """§11 : une clause datée du noyau ne survit pas à sa date.

    Forme reconnue : une date ISO `AAAA-MM-JJ` écrite dans le noyau — la seule
    admise pour y dater une échéance (« se retire au plus tard le 2026-12-31 »).
    Passé le jour, l'avertissement dit la ligne et la date, parce qu'une
    échéance dépassée laisse croire qu'un régime tient encore.
    """

    NOYAU = "IA/system/VAULT-CONTRACT.md"

    def noyau(self, texte: str) -> None:
        self.ecrire(self.NOYAU, texte)

    def test_une_clause_datee_echue_avertit(self):
        self.noyau("La tolérance se retire au plus tard le 2026-12-31.\n")

        VC.verifier_clauses_datees_du_noyau(date(2027, 1, 1))

        self.assertEqual([], VC.erreurs, self.erreurs_texte())
        self.assertEqual(1, len(VC.avertissements), self.avertissements_texte())
        message = VC.avertissements[0]
        self.assertIn("2026-12-31", message)       # la date
        self.assertIn("ligne 1", message)          # où elle est
        self.assertIn("VAULT-CONTRACT", message)

    def test_une_clause_encore_valable_se_tait(self):
        """Le jour dit compris, la clause tient encore : aucun avertissement."""
        self.noyau("La tolérance se retire au plus tard le 2026-12-31.\n")

        VC.verifier_clauses_datees_du_noyau(date(2026, 12, 31))

        self.assertEqual([], VC.avertissements, self.avertissements_texte())

    def test_chaque_echeance_depassee_est_dite(self):
        self.noyau("Première, au plus tard le 2026-01-01.\n"
                   "Deuxième, au plus tard le 2026-02-01.\n")

        VC.verifier_clauses_datees_du_noyau(date(2027, 1, 1))

        self.assertEqual(2, len(VC.avertissements), self.avertissements_texte())
        self.assertIn("ligne 1", VC.avertissements[0])
        self.assertIn("ligne 2", VC.avertissements[1])

    def test_une_date_bien_ecrite_mais_inexistante_avertit(self):
        """`2028-02-30` a la forme d'une date sans en être une.

        `date.fromisoformat` lève ici une `ValueError` ; la laisser filer ferait
        sortir le vérificateur en traceback, et un coffre par ailleurs cohérent
        serait refusé pour une date mal écrite. On avertit, sans s'arrêter.
        """
        self.noyau("La tolérance se retire au plus tard le 2028-02-30.\n")

        VC.verifier_clauses_datees_du_noyau(date(2029, 1, 1))

        self.assertEqual([], VC.erreurs, self.erreurs_texte())
        self.assertEqual(1, len(VC.avertissements), self.avertissements_texte())
        message = VC.avertissements[0]
        self.assertIn("2028-02-30", message)       # la date montrée telle quelle
        self.assertIn("ligne 1", message)          # où elle est
        self.assertIn("illisible", message)

    def test_une_date_inexistante_ne_masque_pas_la_suivante(self):
        """Le mois 13 avertit « illisible », et la clause d'après garde son sort."""
        self.noyau("D'abord le 2026-13-01, puis le 2026-01-01.\n")

        VC.verifier_clauses_datees_du_noyau(date(2027, 1, 1))

        self.assertEqual(2, len(VC.avertissements), self.avertissements_texte())
        self.assertIn("ligne 1", VC.avertissements[0])
        self.assertIn("2026-13-01", VC.avertissements[0])
        self.assertIn("ligne 1", VC.avertissements[1])
        self.assertIn("2026-01-01", VC.avertissements[1])

    def test_sans_noyau_rien_n_est_signale(self):
        VC.verifier_clauses_datees_du_noyau(date(2030, 1, 1))
        self.assertEqual([], VC.avertissements, self.avertissements_texte())


class TestLaCoutureDesDerives(BaseVerificateur):
    """`verifier_derives` pour de vrai : un index périmé doit être vu.

    Toute la suite la remplaçait par `lambda: None` — le seul contrôle qui
    regarde les index dérivés n'était donc jamais exécuté, et un index périmé
    serait passé sans un mot. Les classes qui peuplent un coffre sans sources
    d'index la neutralisent explicitement (`neutraliser_les_derives()`) ;
    celle-ci les peuple et la laisse réelle, sur son coffre temporaire.
    """

    def setUp(self):
        super().setUp()
        self.fiche("agent", "agent-verif", {})
        self.fiche("skill", "skill-verif", {})
        (self.racine / "IA" / "system").mkdir(parents=True, exist_ok=True)

    def regenerer_les_index(self):
        """Écrit les cinq index du coffre — par le générateur, pas à la main."""
        with mock.patch.object(RI, "RACINE", self.racine), \
                redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            code = RI.main([])
        self.assertEqual(0, code, "le générateur a échoué sur ce coffre")

    def test_un_index_perime_est_une_erreur(self):
        VC.verifier_derives()
        self.assertIn("index périmés", self.erreurs_texte())
        self.assertIn("IA/system/agents-index.md", self.erreurs_texte())

    def test_un_index_a_jour_ne_dit_rien(self):
        self.regenerer_les_index()
        VC.verifier_derives()
        self.assertEqual("", self.erreurs_texte())

    def test_le_controle_remonte_par_la_ligne_de_commande(self):
        self.executer()
        self.assertIn("index périmés", self.erreurs_texte(),
                      "la ligne de commande ne doit plus taire ce contrôle")


if __name__ == "__main__":
    unittest.main()
