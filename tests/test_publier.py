"""`publier.py` : ce qu'il refuse d'écraser.

`synchroniser` efface le contenu suivi de la cible avant d'y verser l'export :
c'est le seul geste du coffre qui détruit. Une cible qui est un coffre vivant,
un dossier qui porte la source, ou un clone du dépôt privé, y perdrait son
travail sans retour. Ces tests fixent les refus — avant l'export, code 1.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import publier as PUB                                          # noqa: E402

PUBLIER = SCRIPTS / "publier.py"
ORIGINE_PRIVEE = "https://example.com/moi/coffre-prive.git"
ORIGINE_PUBLIQUE = "https://example.com/moi/coffre-public.git"


def git(depot: Path, *arguments: str) -> None:
    """Un git muet, avec une identité à nous : rien n'ira dans la config globale."""
    subprocess.run(["git", "-c", "user.email=tests", "-c", "user.name=Tests",
                    *arguments], cwd=str(depot), check=True, capture_output=True)


class BasePublication(unittest.TestCase):
    """Une source et une cible : deux dépôts git, chacun avec son `origin`.

    La cible est le miroir d'OBSIA — c'est le seul genre de cible que
    `publier.py` accepte d'écraser, avec un dépôt vierge.
    """

    #: Ce qui reconnaît un miroir : le contrat du coffre, que rien d'autre ne porte.
    MARQUE = Path("IA") / "system" / "VAULT-CONTRACT.md"

    def setUp(self):
        self.parent = Path(tempfile.mkdtemp(prefix="obsia-test-publier-"))
        self.addCleanup(shutil.rmtree, self.parent, ignore_errors=True)
        self.source = self.depot("prive", ORIGINE_PRIVEE)
        self.cible = self.depot("public", ORIGINE_PUBLIQUE, miroir=True)

    def depot(self, nom: str, origine: str, miroir: bool = False) -> Path:
        chemin = self.parent / nom
        chemin.mkdir()
        git(chemin, "init", "-q")
        git(chemin, "remote", "add", "origin", origine)
        (chemin / "README.md").write_text("# %s\n" % nom, encoding="utf-8")
        if miroir:
            marque = chemin / self.MARQUE
            marque.parent.mkdir(parents=True)
            marque.write_text("---\n\n# Contrat du coffre\n", encoding="utf-8")
        git(chemin, "add", "-A")
        git(chemin, "commit", "-q", "-m", "Départ")
        return chemin


class TestRefusDeSynchroniser(BasePublication):
    """`raison_de_refus` : ce qui doit arrêter la publication avant l'export."""

    def test_refuse_la_source_elle_meme(self):
        self.assertIsNotNone(PUB.raison_de_refus(self.source, self.source))

    def test_refuse_une_cible_qui_contient_la_source(self):
        self.assertIsNotNone(PUB.raison_de_refus(self.source, self.parent))

    def test_refuse_une_cible_sous_la_source(self):
        self.assertIsNotNone(PUB.raison_de_refus(self.source,
                                                 self.source / "dedans"))

    def test_refuse_un_coffre_vivant(self):
        (self.cible / "-SAVOIRS").mkdir()
        self.assertIsNotNone(PUB.raison_de_refus(self.source, self.cible))

    def test_refuse_un_dossier_obsidian(self):
        (self.cible / ".obsidian").mkdir()
        self.assertIsNotNone(PUB.raison_de_refus(self.source, self.cible))

    def test_refuse_une_memoire_remplie(self):
        memoire = self.cible / "mémoire"
        memoire.mkdir()
        (memoire / "note.md").write_text("à moi\n", encoding="utf-8")
        self.assertIsNotNone(PUB.raison_de_refus(self.source, self.cible))

    def test_accepte_la_memoire_de_distribution(self):
        """Ce qu'une publication laisse dans `mémoire/` : rien de personnel."""
        memoire = self.cible / "mémoire"
        memoire.mkdir()
        for nom in PUB.MEMOIRE_DE_DISTRIBUTION:
            (memoire / nom).write_text("---\n\nVide.\n", encoding="utf-8")
        self.assertIsNone(PUB.raison_de_refus(self.source, self.cible))

    def test_accepte_une_cible_deja_publiee(self):
        """Republier sur sa propre publication ne doit pas se refuser."""
        memoire = self.cible / "mémoire"
        memoire.mkdir()
        (memoire / "README.md").write_text("# Mémoire\n", encoding="utf-8")
        (memoire / "profil-utilisateur.md").write_text("Nom :\n",
                                                       encoding="utf-8")
        (memoire / "sommaire.md").write_text("# Sommaire\n", encoding="utf-8")
        self.assertIsNone(PUB.raison_de_refus(self.source, self.cible))

    def test_refuse_un_sous_dossier_de_memoire(self):
        (self.cible / "mémoire" / "projets").mkdir(parents=True)
        self.assertIsNotNone(PUB.raison_de_refus(self.source, self.cible))

    def test_refuse_la_meme_origine_que_la_source(self):
        git(self.cible, "remote", "set-url", "origin", ORIGINE_PRIVEE)
        self.assertIsNotNone(PUB.raison_de_refus(self.source, self.cible))

    def test_l_origine_est_ramenee_a_lessentiel(self):
        """Une seule identité pour un même dépôt, quelle que soit son écriture."""
        self.assertEqual(PUB.url_origine(self.source),
                         "example.com/moi/coffre-prive")

    def test_refuse_la_meme_origine_ecrite_autrement(self):
        """Ssh et https désignent le même dépôt : c'est le même `origin`.

        Comparer les URL brutes laisserait passer un clone du privé selon la
        façon dont il a été cloné — le refus ne vaut que s'il ne se contourne
        pas en changeant de protocole.
        """
        for ecriture in ("git@example.com:moi/coffre-prive.git",
                         "ssh://git@example.com/moi/coffre-prive",
                         "https://example.com/moi/coffre-prive/",
                         "HTTPS://Example.com/moi/coffre-prive.git"):
            with self.subTest(ecriture=ecriture):
                git(self.cible, "remote", "set-url", "origin", ecriture)
                self.assertIsNotNone(
                    PUB.raison_de_refus(self.source, self.cible), ecriture)

    def test_ne_rapproche_pas_deux_depots_differents(self):
        """Normaliser ne doit pas confondre ce qui n'est pas le même dépôt."""
        for ecriture in ("git@example.com:moi/coffre-public.git",
                         "https://example.com/autre/coffre-prive.git"):
            with self.subTest(ecriture=ecriture):
                git(self.cible, "remote", "set-url", "origin", ecriture)
                self.assertIsNone(
                    PUB.raison_de_refus(self.source, self.cible), ecriture)

    def test_accepte_le_clone_du_depot_public(self):
        self.assertIsNone(PUB.raison_de_refus(self.source, self.cible))

    def test_accepte_un_miroir_d_obsia(self):
        """Un clone de la publication se reconnaît au contrat qu'il porte."""
        miroir = self.depot("miroir", ORIGINE_PUBLIQUE, miroir=True)
        self.assertIsNone(PUB.raison_de_refus(self.source, miroir))

    def test_accepte_une_cible_vierge(self):
        """Un dépôt neuf n'a rien à perdre : rien que son `.git/`."""
        vierge = self.parent / "vierge"
        vierge.mkdir()
        git(vierge, "init", "-q")
        self.assertIsNone(PUB.raison_de_refus(self.source, vierge))

    def test_refuse_un_dossier_vide_sans_git(self):
        """Sans `.git/`, ce n'est pas un dépôt vierge mais un dossier inconnu."""
        vide = self.parent / "pas-un-depot"
        vide.mkdir()
        self.assertIsNotNone(PUB.raison_de_refus(self.source, vide))

    def test_refuse_un_depot_vierge_qui_porte_un_fichier(self):
        """« Vierge » ne tolère rien d'autre que `.git/` : un `.gitignore` suffit."""
        presque = self.parent / "presque-vierge"
        presque.mkdir()
        git(presque, "init", "-q")
        (presque / ".gitignore").write_text("brouillon/\n", encoding="utf-8")
        self.assertIsNotNone(PUB.raison_de_refus(self.source, presque))

    def test_refuse_un_depot_etranger(self):
        """Un dépôt qui n'est pas un clone d'OBSIA : rien ne dit qu'il est à nous.

        `synchroniser` en effacerait tout le contenu suivi. C'est le cas que le
        seul refus d'origine laissait passer : un dépôt à personne, sans
        `origin` comparable, face auquel on n'avait aucune raison de refuser.
        """
        etranger = self.depot("etranger", ORIGINE_PUBLIQUE)
        self.assertIsNotNone(PUB.raison_de_refus(self.source, etranger))

    def test_le_refus_d_un_depot_etranger_dit_sur_quoi_il_se_fonde(self):
        etranger = self.depot("etranger", ORIGINE_PUBLIQUE)
        self.assertIn("VAULT-CONTRACT",
                      PUB.raison_de_refus(self.source, etranger))

    def test_le_refus_d_un_depot_etranger_dit_ce_qu_est_un_depot_vierge(self):
        """Sans le dire, « dépôt vierge » se devine — et se devine mal.

        On croit qu'un dépôt vide fait l'affaire ; il faut qu'il porte son
        `.git/` et rien d'autre, sinon c'est un dépôt qu'on s'apprête à vider.
        """
        etranger = self.depot("etranger", ORIGINE_PUBLIQUE)
        self.assertIn("`.git/`", PUB.raison_de_refus(self.source, etranger))

    def test_le_refus_rend_le_code_1_sans_rien_effacer(self):
        garde = self.cible / "-PROJETS"
        garde.mkdir()
        (garde / "chantier.md").write_text("en cours\n", encoding="utf-8")

        resultat = subprocess.run(
            [sys.executable, "-B", str(PUBLIER), "--racine", str(self.source),
             "--cible", str(self.cible), "--appliquer"],
            capture_output=True, text=True, check=False)

        self.assertEqual(resultat.returncode, 1, resultat.stdout)
        self.assertIn("-PROJETS", resultat.stderr)
        self.assertEqual((garde / "chantier.md").read_text(encoding="utf-8"),
                         "en cours\n")


class TestVidageDeLaCible(BasePublication):
    """`synchroniser` : ce qu'il efface, et par quel geste."""

    def export_pret(self) -> Path:
        """Un export minimal, de quoi peupler la cible."""
        export = self.parent / "export"
        (export / "IA" / "system").mkdir(parents=True)
        (export / "README.md").write_text("# Public\n", encoding="utf-8")
        (export / "IA" / "system" / "contrat.md").write_text("Contrat.\n",
                                                             encoding="utf-8")
        return export

    def test_un_lien_symbolique_est_defait_sans_etre_suivi(self):
        dehors = self.parent / "ailleurs"
        dehors.mkdir()
        garde = dehors / "a-moi.md"
        garde.write_text("mon travail\n", encoding="utf-8")
        # Le miroir porte déjà un `IA/` réel : on le remplace par un lien.
        shutil.rmtree(self.cible / "IA")
        (self.cible / "IA").symlink_to(dehors, target_is_directory=True)

        PUB.synchroniser(self.export_pret(), self.cible)

        self.assertTrue(garde.is_file(), "le contenu pointé a été effacé")
        self.assertEqual(garde.read_text(encoding="utf-8"), "mon travail\n")
        self.assertFalse((self.cible / "IA").is_symlink())
        self.assertTrue((self.cible / "IA" / "system" / "contrat.md").is_file())

    def test_l_apercu_liste_ce_qui_sera_supprime(self):
        (self.cible / "-DOCUMENTS").mkdir()
        (self.cible / "notes.md").write_text("brouillon\n", encoding="utf-8")

        supprimes = PUB.chemins_a_supprimer(self.cible)

        self.assertIn("-DOCUMENTS/", supprimes)
        self.assertIn("notes.md", supprimes)
        self.assertIn("README.md", supprimes)
        self.assertNotIn(".git", supprimes)


def assemble(*morceaux: str) -> str:
    """Recolle un faux secret au moment du test.

    Le contrôle de fuite lit tous les fichiers publiés, ce fichier de test
    compris : un motif interdit recopié tel quel ici serait signalé à la
    publication du coffre — le contrôle se lit lui-même. D'où le découpage.
    """
    return "".join(morceaux)


class BaseControle(unittest.TestCase):
    """Un dossier de fichiers à relire, monté à la main, hors de tout dépôt."""

    def setUp(self):
        self.parent = Path(tempfile.mkdtemp(prefix="obsia-test-controle-"))
        self.addCleanup(shutil.rmtree, self.parent, ignore_errors=True)
        self.racine = self.parent / "source"
        self.racine.mkdir()

    def ecrire(self, nom: str, contenu) -> Path:
        chemin = self.racine / nom
        chemin.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(contenu, bytes):
            chemin.write_bytes(contenu)
        else:
            chemin.write_text(contenu, encoding="utf-8")
        return chemin

    def controler(self) -> "PUB.Controle":
        return PUB.controler_fuites(self.racine)

    def etiquettes(self, controle) -> list:
        return [etiquette for _, _, etiquette, _ in controle.trouvailles]


class TestCeQuiNEstPasRelu(BaseControle):
    """Un contrôle dont on ignore l'angle mort ne vaut rien.

    Un fichier non relu n'est pas un fichier propre : c'est un fichier dont on
    ne sait rien. Celui qui publie doit pouvoir lire la liste, et le rapport ne
    peut pas annoncer « aucune trouvaille » sans dire sur quoi il porte.
    """

    def test_nomme_les_fichiers_sautes_et_pourquoi(self):
        self.ecrire("assets/logo.png", b"\x89PNG\r\n\x1a\n\x00\x00\xff")
        self.ecrire("notes.txt", b"caf\xe9 en latin-1, pas de l'utf-8\n")

        controle = self.controler()

        self.assertEqual(sorted(controle.non_relus),
                         [("assets/logo.png", "extension binaire"),
                          ("notes.txt", "non UTF-8")])
        self.assertEqual(controle.relus, 0)

    def test_relit_les_svg(self):
        """Un `.svg` est du texte : le compter comme binaire le laissait passer."""
        self.ecrire("assets/logo.svg",
                    "<svg xmlns='http://www.w3.org/2000/svg'>\n"
                    "  <!-- %s -->\n</svg>\n" % assemble("192.168.1.", "42"))

        controle = self.controler()

        self.assertIn("adresse IP privée", self.etiquettes(controle))
        self.assertEqual(controle.non_relus, [])

    def test_un_domaine_admis_ne_couvre_pas_ses_sous_domaines(self):
        """`exemple.fr.attaquant.net` n'est pas `exemple.fr`."""
        self.ecrire("notes.md",
                    "écrire à %s\n" % assemble("jean@exemple.fr",
                                               ".attaquant.net"))

        self.assertIn("adresse de courriel", self.etiquettes(self.controler()))

    def test_les_adresses_du_projet_ne_sont_pas_des_fuites(self):
        self.ecrire("notes.md", "écrire à noreply@github.com, ou à "
                                "utilisateur@exemple.fr, ou à moi@example.com\n")

        self.assertEqual(self.etiquettes(self.controler()), [])


class TestCeQuiFuitEncore(BaseControle):
    """Les faux négatifs mesurés par l'audit : ce que le contrôle laissait passer.

    Un contrôle de fuite se juge aussi sur ce qu'il attrape à tort. Chaque motif
    ajouté vient donc avec son témoin négatif : la prose du contrat parle de
    mots de passe à longueur de page sans jamais en donner, et elle doit rester
    publiable telle quelle.
    """

    def test_les_mots_cles_francais(self):
        """`mdp`, `mot de passe`, `jeton`, `clé` : le coffre s'écrit en français."""
        valeur = assemble("cheval", "-bleu-42-rapide")
        self.ecrire("notes.md",
                    "mdp : %s\nmot de passe : %s\njeton : %s\nclé : %s\n"
                    % (valeur, valeur, valeur, valeur))

        self.assertEqual(self.etiquettes(self.controler()),
                         ["secret affecté"] * 4)

    def test_une_valeur_a_espaces_ou_a_symboles(self):
        """`[A-Za-z0-9…]` ne lisait que l'alphanumérique : le reste passait."""
        self.ecrire("config.md",
                    "password: \"%s\"\nsecret = %s\n"
                    % (assemble("correct horse", " battery staple"),
                       assemble("Zq9!kD#mQ", "@7x4/%")))

        self.assertEqual(self.etiquettes(self.controler()),
                         ["secret affecté"] * 2)

    def test_un_identifiant_compose(self):
        """`password_hash`, `db_password` : la frontière de mot tombait sur `_`."""
        valeur = assemble("$2b$12$", "K8sLpQ2mR7vXzA1b")
        self.ecrire("config.md",
                    "%s: %s\n%s = %s\n%s = %s\n"
                    % (assemble("password_", "hash"), valeur,
                       assemble("db_", "password"), valeur,
                       assemble("mdp_", "hash"), valeur))

        self.assertEqual(self.etiquettes(self.controler()),
                         ["secret affecté"] * 3)

    def test_un_identifiant_compose_sans_valeur(self):
        """`password_hash` est un nom de colonne tant qu'aucune valeur ne suit."""
        self.ecrire("notes.md",
                    "la colonne %s garde l'empreinte, %s est lue à l'exécution\n"
                    % (assemble("password_", "hash"),
                       assemble("db_", "password")))

        self.assertEqual(self.etiquettes(self.controler()), [])

    def test_un_nom_de_variable_n_est_pas_un_secret(self):
        """`bearer_token_env_var` porte le nom d'une variable, pas sa valeur."""
        self.ecrire("notes.md",
                    "%s = %s    # un nom, jamais un secret\n"
                    % (assemble("bearer", "_token_env_var"),
                       assemble("\"SEARXNG", "_TOKEN\"")))

        self.assertEqual(self.etiquettes(self.controler()), [])

    def test_une_valeur_a_espaces_sans_guillemets(self):
        """Une phrase de passe se recopie aussi sans guillemets."""
        self.ecrire("config.yml", "secret: %s\n"
                    % assemble("correct horse", " battery staple"))

        self.assertEqual(self.etiquettes(self.controler()), ["secret affecté"])

    def test_la_prose_apres_deux_points_ne_se_signale_pas(self):
        """Trois phrases du coffre : le mot-clé y est noyé dans la ligne."""
        self.ecrire("notes.md",
                    "L'URL est une adresse interne, pas un secret : une note du "
                    "coffre parent la porte\n"
                    "ouvre le port 8080 sans mot de passe : acceptable seulement "
                    "en local, jamais ailleurs\n"
                    "qpdf --decrypt %s chiffre.pdf clair.pdf\n"
                    % assemble("--pass", "word=MOTDEPASSE"))

        self.assertEqual(self.etiquettes(self.controler()), [])

    def test_une_cle_secrete_aws_nue(self):
        """Sans préfixe `AKIA`, la clé secrète AWS seule passait inaperçue.

        Rien n'est affecté ici : pas de `=`, pas de `:`. La ligne dit seulement
        ce qu'elle vaut, comme le ferait un carnet de notes recopié.
        """
        self.ecrire("notes.md", "la clé aws_secret_access_key vaut %s\n"
                    % assemble("wJalrXUtnFEMI/K7MDENG",
                               "/bPxRfiCYEXAMPLEKEY"))

        self.assertEqual(self.etiquettes(self.controler()), ["clé secrète AWS"])

    def test_une_empreinte_git_n_est_pas_une_cle_aws(self):
        """Quarante caractères hexadécimaux, c'est un commit, pas un secret."""
        sha = ("0123456789abcdef" * 2)[:40]
        self.ecrire("journal.md", "le secret du tirage tient dans le commit %s\n"
                    % sha)

        self.assertEqual(self.etiquettes(self.controler()), [])

    def test_un_nom_d_hote_interne(self):
        self.ecrire("notes.md",
                    "%s\n%s\n%s\n%s\n%s\n"
                    % (assemble("nas", ".lan"),
                       assemble("serveur", ".local"),
                       assemble("srv", ".internal"),
                       assemble("portail", ".home.arpa"),
                       assemble("poste-portable", ".ts.net")))

        self.assertEqual(self.etiquettes(self.controler()),
                         ["nom d'hôte interne"] * 5)

    def test_les_noms_de_fichiers_locaux_ne_sont_pas_des_hotes(self):
        """`obsia.local.yml` et `AGENTS.local.md` : des noms, pas des machines."""
        self.ecrire("notes.md",
                    "le profil `obsia.local.yml`, la fiche `AGENTS.local.md`, "
                    "`CLAUDE.local.md`, dans ~/.local/share/obsia/\n")

        self.assertEqual(self.etiquettes(self.controler()), [])

    def test_la_prose_du_contrat_reste_publiable(self):
        """Les phrases du contrat parlent de secrets sans en donner aucun."""
        self.ecrire("contrat.md",
                    "Un secret — mot de passe,\njeton, clé — n'a sa place ni ici "
                    "ni ailleurs.\n"
                    "Un secret — mot de passe, jeton, clé — n'a sa place nulle part.\n"
                    "Le dossier se lit dans `obsia.local.yml` (clé `coffre_parent`, "
                    "§13).\n"
                    "il refuse : un bloc de clé privée, un préfixe de jeton connu, "
                    "ou un secret affecté\n"
                    "Jamais de secret (clé API, jeton) dans le code : variables\n"
                    "le contrat parle de jetons et de mots de passe à longueur de "
                    "page\n")

        self.assertEqual(self.etiquettes(self.controler()), [])


class TestNomsInterdits(BaseControle):
    """La liste locale des noms interdits — ce qu'aucun motif ne reconnaît.

    Un nom d'hôte nu n'a pas de forme : seul l'utilisateur sait qu'il en est
    un. Ce qui doit être prouvé : la liste se lit, un nom s'attrape entier et
    sans casse, un nom trop court est écarté — et surtout, un nom de cette
    liste **avertit** au lieu de refuser : il n'est ni une trouvaille
    bloquante ni quelque chose que `--forcer` doit franchir. Il signale,
    ligne par ligne, et laisse publier.
    """

    def liste(self, contenu: str) -> Path:
        chemin = self.parent / "noms-interdits"
        chemin.write_text(contenu, encoding="utf-8")
        return chemin

    def test_la_liste_se_lit_commentaires_et_noms_courts_ecartes(self):
        noms, courts = PUB.charger_noms_interdits(
            self.liste("# machines\nposte-atelier  # le portable\n\nia\n"))
        self.assertEqual(noms, ["poste-atelier"])
        self.assertEqual(courts, ["ia"])

    def test_sans_liste_rien_n_est_retenu(self):
        self.assertEqual(PUB.charger_noms_interdits(self.parent / "absente"), ([], []))

    def test_un_nom_s_attrape_entier_et_sans_casse(self):
        self.ecrire("a.md", "À instancier sur Poste-Atelier seulement.\n")
        self.ecrire("b.md", "poste-atelier-2 et poste-ateliers ne sont pas lui.\n")
        controle = PUB.controler_fuites(self.racine, ["poste-atelier"])
        self.assertEqual(controle.trouvailles, [])
        self.assertEqual([(t[0], t[2]) for t in controle.avertissements],
                         [("a.md", "nom interdit")])

    def test_sans_noms_le_controle_ne_change_pas(self):
        self.ecrire("a.md", "poste-atelier\n")
        controle = self.controler()
        self.assertEqual(controle.trouvailles, [])
        self.assertEqual(controle.avertissements, [])

    def test_un_nom_interdit_n_a_rien_a_forcer(self):
        """Un nom de la liste avertit : il ne refuse pas, il n'a rien à forcer.

        Il n'est pas dans `SANS_FORCAGE` — ce qui y reste, ce sont les valeurs à
        forme reconnaissable (clé privée, jeton), les seules que `--forcer` ne
        franchit jamais.
        """
        self.assertNotIn("nom interdit", PUB.SANS_FORCAGE)

    def test_un_mot_banal_ne_bloque_ni_la_prose_ni_le_home(self):
        """Témoin négatif : un mot banal déclaré n'arrête pas la publication.

        La liste frappe des mots, pas seulement des identités : « table » est
        un mot banal, il apparaît dans la prose courante, et le témoin est vrai
        jusque dans un chemin `$HOME/.config/table/…` — le mot y figure
        vraiment. Aucun des deux ne produit de trouvaille bloquante : le nom
        devient un avertissement, la publication passe. C'est ce qui protège le
        passage du refus à l'avertissement.
        """
        self.ecrire("prose.md", "La table est mise, le repas est prêt.\n")
        self.ecrire("config.md",
                    "liste lue dans $HOME/.config/table/noms-interdits\n")
        controle = PUB.controler_fuites(self.racine, ["table"])

        self.assertEqual(controle.trouvailles, [])
        self.assertEqual(
            [(rel, etiquette) for rel, _, etiquette, _ in controle.avertissements],
            [("config.md", "nom interdit"), ("prose.md", "nom interdit")])


class BasePublicationReelle(unittest.TestCase):
    """Une source committée et une cible vierge : `publier.py` pour de vrai.

    C'est le seul moyen de juger ce que voit celui qui publie — l'ordre des
    contrôles, les fichiers non relus, le message de commit — sans relire le
    code pour le croire.
    """

    def setUp(self):
        self.parent = Path(tempfile.mkdtemp(prefix="obsia-test-publication-"))
        self.addCleanup(shutil.rmtree, self.parent, ignore_errors=True)

        self.source = self.parent / "source"
        self.source.mkdir()
        git(self.source, "init", "-q")
        git(self.source, "remote", "add", "origin", ORIGINE_PRIVEE)
        self.poser_les_scripts()
        self.ecrire("README.md", "# coffre\n")
        self.committer()

        self.cible = self.parent / "cible"
        self.cible.mkdir()
        git(self.cible, "init", "-q")
        git(self.cible, "remote", "add", "origin", ORIGINE_PUBLIQUE)

    def poser_les_scripts(self) -> None:
        """Trois scripts muets : l'export doit pouvoir être régénéré et vérifié."""
        self.ecrire("scripts/regenerate_sommaire.py", "import sys\nsys.exit(0)\n")
        self.ecrire("scripts/regenerate_index.py", "import sys\nsys.exit(0)\n")
        self.ecrire("scripts/verifier_coffre.py", "print('coffre cohérent')\n")

    def ecrire(self, nom: str, contenu) -> Path:
        chemin = self.source / nom
        chemin.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(contenu, bytes):
            chemin.write_bytes(contenu)
        else:
            chemin.write_text(contenu, encoding="utf-8")
        return chemin

    def committer(self) -> None:
        git(self.source, "add", "-A")
        git(self.source, "commit", "-q", "-m", "Lot")

    def lancer(self, *arguments: str) -> subprocess.CompletedProcess:
        """Lance le script sur la source des tests, avec une identité Git à nous."""
        return subprocess.run(
            [sys.executable, "-B", str(PUBLIER), "--racine", str(self.source),
             "--cible", str(self.cible), *arguments],
            capture_output=True, text=True, check=False,
            env={**os.environ,
                 "GIT_AUTHOR_NAME": "Tests", "GIT_AUTHOR_EMAIL": "tests@example.com",
                 "GIT_COMMITTER_NAME": "Tests",
                 "GIT_COMMITTER_EMAIL": "tests@example.com"})

    def publies(self) -> set:
        """Ce qui est arrivé dans la cible, chemins relatifs, `.git/` exclu."""
        return {str(p.relative_to(self.cible))
                for p in self.cible.rglob("*")
                if ".git" not in p.relative_to(self.cible).parts}


class TestLeRapportDitTout(BasePublicationReelle):
    def test_le_rapport_compte_les_fichiers_non_relus(self):
        self.ecrire("assets/logo.png", b"\x89PNG\r\n\x1a\n\x00\x00\xff")
        self.committer()

        resultat = self.lancer("--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertRegex(resultat.stdout,
                         r"Aucune trouvaille sur \d+ fichier\(s\) relu\(s\) "
                         r"— 1 non relu\(s\)")
        self.assertIn("assets/logo.png (extension binaire)", resultat.stdout)


class TestLeControlePorteSurLExportFinal(BasePublicationReelle):
    """Ce que les générateurs viennent d'écrire doit être relu, lui aussi.

    Le contrôle passait avant la régénération : les index et les sommaires
    produits par `regenerate_index.py` et `regenerate_sommaire.py` partaient
    dans la cible sans que personne ne les ait jamais lus — et c'est justement
    là que se recopie ce que la source contient.
    """

    def index_fuyard(self) -> None:
        """Un générateur qui recopie une adresse interne dans l'index.

        La valeur est recollée à l'exécution : le script vit dans l'export, le
        contrôle le lit lui aussi, et une adresse écrite en clair dans ce
        script ferait signaler le script — donc bien avant la régénération.
        """
        self.ecrire("scripts/regenerate_index.py", (
            "from pathlib import Path\n"
            "racine = Path(__file__).resolve().parent.parent\n"
            "index = racine / 'IA' / 'system' / 'agents-index.md'\n"
            "index.parent.mkdir(parents=True, exist_ok=True)\n"
            "index.write_text('192.168.1.' + '42\\n', encoding='utf-8')\n"))

    def test_un_index_regenere_fuyard_arrete_la_publication(self):
        self.index_fuyard()
        self.committer()

        resultat = self.lancer("--appliquer")

        self.assertEqual(resultat.returncode, 1,
                         resultat.stdout + resultat.stderr)
        self.assertIn("IA/system/agents-index.md", resultat.stdout)
        self.assertIn("adresse IP privée", resultat.stdout)
        self.assertEqual(self.publies(), set(),
                         "rien ne doit être écrit dans la cible")


class TestCeQuiNeSeForcePas(BasePublicationReelle):
    """`--forcer` rattrape un faux positif, pas une fuite.

    Une clé privée ne se révoque pas, un jeton connu se révoque — mais dans les
    deux cas, publier d'abord revient à jeter ce qu'on voulait garder. Ces deux
    catégories se réparent dans la source, et nulle part ailleurs.
    """

    def test_une_cle_privee_ne_se_force_pas(self):
        self.ecrire("notes.md", assemble("-----BEGIN OPENSSH ",
                                         "PRIVATE KEY-----\n"))
        self.committer()

        resultat = self.lancer("--appliquer", "--forcer")

        self.assertEqual(resultat.returncode, 1, resultat.stdout + resultat.stderr)
        self.assertIn("clé privée", resultat.stdout + resultat.stderr)
        self.assertRegex(resultat.stdout,
                         r"\d+ fichier\(s\) relu\(s\), \d+ non relu\(s\)",
                         "le total s'affiche aussi quand le refus tombe")
        self.assertEqual(self.publies(), set(),
                         "rien ne doit être écrit dans la cible")

    def test_un_jeton_connu_ne_se_force_pas(self):
        self.ecrire("notes.md", "jeton %s\n" % assemble("ghp_",
                                                        "A1b2C3d4E5f6G7h8I9j0"))
        self.committer()

        resultat = self.lancer("--appliquer", "--forcer")

        self.assertEqual(resultat.returncode, 1, resultat.stdout + resultat.stderr)
        self.assertIn("jeton d'API", resultat.stdout + resultat.stderr)
        self.assertEqual(self.publies(), set(),
                         "rien ne doit être écrit dans la cible")

    def test_forcer_ecrit_la_derogation_dans_le_commit(self):
        """Une publication forcée doit laisser sa trace là où on la relira."""
        self.ecrire("notes.md", "nas %s\n" % assemble("192.168.1.", "42"))
        self.committer()

        resultat = self.lancer("--appliquer", "--forcer", "--commit")

        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        message = subprocess.run(
            ["git", "-C", str(self.cible), "log", "-1", "--format=%B"],
            capture_output=True, text=True, check=True).stdout
        self.assertIn("--forcer", message)
        self.assertIn("adresse IP privée", message)


class TestUnNomInterditAvertit(BasePublicationReelle):
    """Un nom de la liste locale avertit : la publication passe, sans `--forcer`.

    La liste doit retenir des identités mais frappe des mots : un mot banal y
    figure un faux positif — ici une ligne de prose. La publication ne doit ni
    s'arrêter ni exiger `--forcer` : l'avertissement s'écrit, et le fichier part
    quand même. Le témoin du chemin `$HOME/` vit dans le contrôle unitaire,
    `test_un_mot_banal_ne_bloque_ni_la_prose_ni_le_home`. Ici la liste est
    fictive, portée par `OBSIA_NOMS_INTERDITS` : jamais un nom de la vraie liste
    de l'utilisateur dans le dépôt, qui se publie.
    """

    def lancer_avec_liste(self, *arguments: str) -> subprocess.CompletedProcess:
        liste = self.parent / "noms-fictifs"
        liste.write_text("table\n", encoding="utf-8")
        return subprocess.run(
            [sys.executable, "-B", str(PUBLIER), "--racine", str(self.source),
             "--cible", str(self.cible), *arguments],
            capture_output=True, text=True, check=False,
            env={**os.environ,
                 "OBSIA_NOMS_INTERDITS": str(liste),
                 "GIT_AUTHOR_NAME": "Tests", "GIT_AUTHOR_EMAIL": "tests@example.com",
                 "GIT_COMMITTER_NAME": "Tests",
                 "GIT_COMMITTER_EMAIL": "tests@example.com"})

    def test_un_mot_banal_n_arrete_pas_la_publication(self):
        self.ecrire("notes.md", "La table est mise, le repas est prêt.\n")
        self.committer()

        resultat = self.lancer_avec_liste("--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        self.assertIn("nom interdit", resultat.stdout)
        self.assertIn("avertissement", resultat.stdout)
        self.assertIn("notes.md", self.publies(),
                      "la prose signalée doit quand même être publiée")

    def test_un_nom_interdit_ne_demande_pas_forcer(self):
        """L'avertissement n'exige pas `--forcer` : il n'y a rien à forcer."""
        self.ecrire("notes.md", "Une simple table au milieu de la prose.\n")
        self.committer()

        resultat = self.lancer_avec_liste("--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        self.assertNotIn("--forcer", resultat.stdout)

    def test_l_avertissement_du_nom_s_ecrit_dans_le_commit(self):
        """Le message part dans le public : le nombre, jamais le chemin ni le nom."""
        self.ecrire("notes.md", "La table est mise, le repas est prêt.\n")
        self.committer()

        resultat = self.lancer_avec_liste("--appliquer", "--commit")

        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        message = subprocess.run(
            ["git", "-C", str(self.cible), "log", "-1", "--format=%B"],
            capture_output=True, text=True, check=True).stdout
        self.assertIn("1 avertissement(s) de nom interdit", message)
        self.assertNotIn("notes.md", message,
                         "le chemin n'a rien à faire dans le message public")
        self.assertNotIn("table", message,
                         "le nom lui-même ne doit pas partir dans le public")

    def test_le_nom_ne_fuit_pas_par_le_chemin_du_fichier(self):
        """Un fichier nommé d'après le mot ne doit pas le porter dans le commit.

        Le nom peut tenir au chemin lui-même (`inventaire-table.md`) : citer
        `chemin:ligne` dans le message public le ferait fuir. Seul le nombre
        part ; le détail reste dans le rapport local, affiché sur la sortie.
        """
        self.ecrire("inventaire-table.md", "La table est mise, le repas est prêt.\n")
        self.committer()

        resultat = self.lancer_avec_liste("--appliquer", "--commit")

        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        self.assertIn("inventaire-table.md:1", resultat.stdout,
                      "le détail doit rester dans le rapport local")
        message = subprocess.run(
            ["git", "-C", str(self.cible), "log", "-1", "--format=%B"],
            capture_output=True, text=True, check=True).stdout
        self.assertIn("1 avertissement(s) de nom interdit", message)
        self.assertNotIn("table", message,
                         "le nom ne doit pas fuir par le chemin du fichier")

    def test_l_avertissement_ne_cache_pas_le_total_des_fichiers(self):
        """Le total « N relus, M non relus » s'affiche même sous un avertissement."""
        self.ecrire("notes.md", "La table est mise, le repas est prêt.\n")
        self.ecrire("assets/logo.png", b"\x89PNG\r\n\x1a\n\x00\x00\xff")
        self.committer()

        resultat = self.lancer_avec_liste("--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        self.assertIn("avertissement(s)", resultat.stdout)
        self.assertRegex(resultat.stdout,
                         r"\d+ fichier\(s\) relu\(s\), 1 non relu\(s\)")
        self.assertIn("assets/logo.png (extension binaire)", resultat.stdout)


if __name__ == "__main__":
    unittest.main()
