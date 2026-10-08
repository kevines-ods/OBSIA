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
        (self.cible / "0-SAVOIRS").mkdir()
        self.assertIsNotNone(PUB.raison_de_refus(self.source, self.cible))

    def test_refuse_un_dossier_obsidian(self):
        (self.cible / ".obsidian").mkdir()
        self.assertIsNotNone(PUB.raison_de_refus(self.source, self.cible))

    def test_refuse_un_coffre_dont_la_memoire_est_pleine(self):
        """`0-PROJETS/` rempli : c'est un coffre de travail, pas un miroir."""
        projets = self.cible / "0-PROJETS"
        projets.mkdir()
        (projets / "mon-projet").mkdir()
        self.assertIsNotNone(PUB.raison_de_refus(self.source, self.cible))

    def test_refuse_un_coffre_qui_garde_l_ancien_nom(self):
        """Les deux noms du même dossier comptent, tant que la bascule dure (§7.1)."""
        (self.cible / "-PROJETS").mkdir()
        self.assertIsNotNone(PUB.raison_de_refus(self.source, self.cible))

    def test_refuse_un_coffre_qui_a_une_archive_gelee(self):
        (self.cible / "0-MEMOIRES").mkdir()
        self.assertIsNotNone(PUB.raison_de_refus(self.source, self.cible))

    def test_accepte_une_cible_deja_publiee(self):
        """Republier sur sa propre publication ne doit pas se refuser.

        Un miroir publié ne porte **aucune** mémoire (§7.1) : il n'y a rien à
        lui effacer que quelqu'un regretterait.
        """
        (self.cible / "brouillon").mkdir()
        (self.cible / "brouillon" / "note.md").write_text("brouillon\n",
                                                          encoding="utf-8")
        self.assertIsNone(PUB.raison_de_refus(self.source, self.cible))

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
        garde = self.cible / "0-PROJETS"
        garde.mkdir()
        (garde / "chantier.md").write_text("en cours\n", encoding="utf-8")

        resultat = subprocess.run(
            [sys.executable, "-B", str(PUBLIER), "--racine", str(self.source),
             "--cible", str(self.cible), "--appliquer"],
            capture_output=True, text=True, check=False)

        self.assertEqual(resultat.returncode, 1, resultat.stdout)
        self.assertIn("0-PROJETS", resultat.stderr)
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
        (self.cible / "0-DOCUMENTS").mkdir()
        (self.cible / "notes.md").write_text("brouillon\n", encoding="utf-8")

        supprimes = PUB.chemins_a_supprimer(self.cible)

        self.assertIn("0-DOCUMENTS/", supprimes)
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

    def test_les_domaines_reserves_ne_sont_pas_des_fuites(self):
        """RFC 2606/6761 : ces domaines ne peuvent désigner personne.

        `example.com/net/org` et les domaines de premier niveau `.test`,
        `.example`, `.invalid` sont réservés : rien ne s'y enregistre, donc une
        adresse qui les porte ne dit rien d'un vrai correspondant.
        """
        self.ecrire("notes.md", "écrire à %s, ou à %s, ou à %s, ou à %s, "
                                "ou à %s, ou à %s\n" % (
            assemble("un@example", ".com"),
            assemble("deux@example", ".net"),
            assemble("trois@example", ".org"),
            assemble("quatre@exemple", ".invalid"),
            assemble("cinq@exemple", ".example"),
            assemble("six@exemple", ".test")))

        self.assertEqual(self.etiquettes(self.controler()), [])

    def test_un_sous_domaine_d_un_domaine_reserve_est_admis(self):
        """Le réservé couvre ses sous-domaines : `mail.example.com` comme
        `mail.exemple.test` — sinon la documentation ne pourrait pas citer
        l'adresse d'un service sur un domaine réservé."""
        self.ecrire("notes.md", "écrire à %s, ou à %s\n" % (
            assemble("un@mail", ".example.com"),
            assemble("deux@mail", ".exemple.test")))

        self.assertEqual(self.etiquettes(self.controler()), [])

    def test_un_vrai_domaine_reste_bloque(self):
        """Le réservé s'arrête au réservé : un domaine réel reste une fuite."""
        self.ecrire("notes.md",
                    "écrire à %s\n" % assemble("six@monentreprise", ".fr"))

        self.assertIn("adresse de courriel", self.etiquettes(self.controler()))

    def test_le_sous_domaine_d_un_domaine_de_projet_n_est_pas_admis(self):
        """`exemple.fr` est admis **en entier** : son sous-domaine ne l'est pas."""
        self.ecrire("notes.md",
                    "écrire à %s\n" % assemble("sept@mail", ".exemple.fr"))

        self.assertIn("adresse de courriel", self.etiquettes(self.controler()))


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

    def test_une_option_qui_recoit_un_chemin_de_fichier(self):
        """`--password-file=…` porte un chemin, pas le mot de passe.

        C'est la forme que conseille `IA/skills/pdf.md` — la fiche qui l'enseigne
        se signalait comme une fuite. Les deux écritures, `=` et espace.
        """
        self.ecrire("fiche.md",
                    "qpdf --decrypt --password-file=/chemin/hors-du-coffre/"
                    "motdepasse.txt chiffre.pdf clair.pdf\n"
                    "qpdf --decrypt --password-file /chemin/hors-du-coffre/"
                    "motdepasse.txt chiffre.pdf clair.pdf\n")

        self.assertEqual(self.etiquettes(self.controler()), [])

    def test_un_mot_de_passe_en_argument_reste_bloque(self):
        """L'exception vaut pour l'option de **fichier**, pas pour la valeur."""
        self.ecrire("fiche.md",
                    "qpdf --decrypt %s chiffre.pdf clair.pdf\n"
                    % assemble("--password=", "cheval-de-course-du-gard"))

        self.assertEqual(self.etiquettes(self.controler()), ["secret affecté"])

    def test_une_variable_de_fichier_reste_bloquee(self):
        """Sans tiret, rien ne dit que la valeur est un chemin : c'est un nom.

        Une option de commande est un répertoire connu (`--password-file`) ; une
        variable peut porter n'importe quoi, y compris le mot de passe lui-même.
        """
        self.ecrire("config.yml",
                    "%s = %s\n" % (assemble("password_", "file"),
                                   assemble("/chemin/vers/motdepasse", ".txt")))

        self.assertEqual(self.etiquettes(self.controler()), ["secret affecté"])

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


class TestTexteDePullRequest(BaseControle):
    """Le titre et la description d'une PR : ce que le contrôle d'arbre ne lit pas.

    Une pull request paraît sur le dépôt public avant que le premier fichier de
    l'export n'y soit — son titre reste dans la liste des PR. L'arbre ne voit
    donc jamais ce texte : il se juge seul, et par la même règle que lui.
    """

    def juger(self, texte: str, noms_interdits=()) -> "PUB.Controle":
        return PUB.controler_texte(texte, noms_interdits,
                                   "titre ou description de PR")

    def test_le_texte_seul_suffit_a_trouver_une_fuite(self):
        controle = self.juger("Corrige le lien vers %s\n"
                               % assemble("192.168.1.", "42"))

        self.assertEqual([etiquette for _, _, etiquette, _ in controle.trouvailles],
                         ["adresse IP privée"])
        self.assertEqual(controle.trouvailles[0][0], "titre ou description de PR")
        self.assertEqual(controle.trouvailles[0][1], 1)

    def test_la_meme_regle_que_l_arbre(self):
        """Une ligne de texte se juge comme la même ligne dans un fichier."""
        ligne = "password: %s\n" % assemble("cheval", "-bleu-42-rapide")
        self.ecrire("config.yml", ligne)

        self.assertEqual(self.etiquettes(self.controler()),
                         [etiquette for _, _, etiquette, _
                          in self.juger(ligne).trouvailles])

    def test_un_texte_propre_ne_dit_rien(self):
        controle = self.juger("Décrit le chantier souveraineté des données.\n")

        self.assertEqual(controle.trouvailles, [])
        self.assertEqual(controle.relus, 1)

    def test_un_texte_vide_n_a_pas_ete_relu(self):
        """« Aucune trouvaille » ne doit pas se lire sur rien."""
        controle = self.juger("   \n")

        self.assertEqual(controle.trouvailles, [])
        self.assertEqual(controle.relus, 0)

    def test_les_adresses_du_projet_restent_publiables(self):
        controle = self.juger("posé par noreply@github.com, relu par "
                               "moi@example.com\n")

        self.assertEqual(controle.trouvailles, [])

    def test_un_nom_interdit_avertit_sans_bloquer(self):
        controle = self.juger("lot signé par poste-atelier\n", ["poste-atelier"])

        self.assertEqual(controle.trouvailles, [])
        self.assertEqual(
            [etiquette for _, _, etiquette, _ in controle.avertissements],
            ["nom interdit"])


class TestLeDepotReel(BasePublication):
    """Le coffre est celui de la machine, pas le dossier d'où l'on parle.

    Un worktree vit ailleurs — `~/obsia-worktrees/<nom-agent>-<sujet>` — et son
    dossier parent n'est pas le coffre : c'est le hangar à worktrees, dont le nom
    se lit dans la documentation du dépôt. Prendre le parent pour le coffre ferait
    signaler cette documentation à chaque aperçu lancé depuis un worktree, et la
    publication y resterait bloquée : un chemin de machine ne se force pas.
    """

    def test_le_clone_principal_se_designe_lui_meme(self):
        self.assertEqual(self.source.resolve(), PUB.depot_reel(self.source))

    def test_un_worktree_designe_le_clone_principal(self):
        autre = self.parent / "worktrees" / "batisseur-sujet"
        autre.parent.mkdir()
        git(self.source, "worktree", "add", "--detach", str(autre))

        self.assertEqual(self.source.resolve(), PUB.depot_reel(autre))


class TestLeCheminDeLaMachine(BaseControle):
    """Le chemin réel de la machine qui publie ne franchit pas la frontière (§13).

    Un chemin absolu nomme une arborescence privée — et il est faux partout
    ailleurs, puisque le coffre change de place et de nom d'un poste à l'autre.
    Les motifs de `BLOQUANTS` ne peuvent pas le reconnaître : il dépend de la
    machine. Le contrôle le reçoit donc de la source.

    La racine ci-dessous est une **fixture** : elle a la forme d'un coffre, et
    n'est le coffre de personne. Le vrai chemin ne s'écrit pas ici — il serait
    lui-même la fuite que ce contrôle existe pour arrêter.
    """

    COFFRE = Path("/srv/coffre-de-test")
    DEPOT = COFFRE / "OBSIA"

    def controler(self):
        return PUB.controler_fuites(self.racine,
                                    machine=PUB.Path(str(self.DEPOT)))

    def test_le_chemin_du_coffre_parent_est_bloque(self):
        self.ecrire("notes.md",
                    "Le coffre vit dans %s, son dépôt juste en dessous.\n"
                    % self.COFFRE)

        self.assertEqual(self.etiquettes(self.controler()), ["chemin du coffre"])

    def test_le_chemin_du_depot_est_bloque(self):
        self.ecrire("notes.md", "cd %s\n" % self.DEPOT)

        self.assertEqual(self.etiquettes(self.controler()), ["chemin du dépôt"])

    def test_les_deux_chemins_dans_la_meme_ligne_ne_comptent_qu_une_fois(self):
        """Le dépôt est sous le coffre : le rapport dit lequel, pas les deux."""
        self.ecrire("notes.md", "Le dépôt %s porte l'AGENTS.md de %s\n"
                    % (self.DEPOT, self.COFFRE))

        self.assertEqual(self.etiquettes(self.controler()), ["chemin du dépôt"])

    def test_un_chemin_voisin_n_est_pas_la_machine(self):
        """`…-notes` n'est pas le coffre, `…/OBSIA-tests` n'est pas le dépôt."""
        self.ecrire("notes.md", "voir %s-notes et %s-tests/OBSIA\n"
                    % (self.COFFRE, self.COFFRE))

        self.assertEqual(self.etiquettes(self.controler()), [])

    def test_un_chemin_colle_a_un_echappement_est_vu(self):
        """Dans un test, le chemin s'écrit `"…\\n/srv/…"` — et il est bien là.

        Sans le desserrage, le `/` suivrait un `n` et passerait pour la suite
        d'un mot : le fichier partirait avec le chemin dedans.
        """
        self.ecrire("fixture.py",
                    'texte = "Une ligne.\\n%s\\nEt une autre.\\n"\n' % self.COFFRE)

        self.assertEqual(self.etiquettes(self.controler()), ["chemin du coffre"])

    def test_un_chemin_precede_d_une_barre_est_vu(self):
        """`file://`, `//…`, `…/montage/…` : la barre ne fait pas un mot.

        Le premier motif refusait un chemin collé à une barre oblique — c'est
        pourtant la forme que prennent une URL `file://` et un chemin recomposé
        sous un point de montage. Il ne protégeait que du bruit, et laissait
        passer la fuite entière.

        Le préfixe du troisième cas est fictif à dessein : un chemin d'exemple
        ici se signalerait sur la machine qui l'a pour racine.
        """
        self.ecrire("fiche.md",
                    "voir file://%s/assets\n"
                    "puis //%s\n"
                    "et /un/montage%s\n" % (self.DEPOT, self.COFFRE, self.COFFRE))

        self.assertEqual(self.etiquettes(self.controler()),
                         ["chemin du dépôt", "chemin du coffre", "chemin du coffre"])

    def test_un_chemin_dans_une_url_web_est_muet(self):
        """Le chemin d'une URL http(s) n'est pas une arborescence locale."""
        self.ecrire("fiche.md",
                    "voir https://exemple.fr%s et http://exemple.fr%s/x\n"
                    % (self.COFFRE, self.DEPOT))

        self.assertEqual(self.etiquettes(self.controler()), [])

    def test_une_url_ne_cache_que_son_propre_chemin(self):
        """Le silence vaut pour l'URL, pas pour la ligne qui la porte."""
        self.ecrire("fiche.md",
                    "voir https://exemple.fr/a, puis %s\n" % self.COFFRE)

        self.assertEqual(self.etiquettes(self.controler()), ["chemin du coffre"])

    def test_une_url_ne_pardonne_pas_la_seconde_occurrence(self):
        """Le silence vaut par occurrence, pas par ligne.

        Examinée une seule fois, la ligne s'arrêtait à la première : le chemin
        de l'URL — muet, à juste titre — blanchissait celui qui le suivait, écrit
        en `file://`, qui est pourtant la fuite.
        """
        self.ecrire("fiche.md",
                    "https://exemple.fr%s/depot puis file://%s/depot/y\n"
                    % (self.DEPOT, self.DEPOT))

        self.assertEqual(self.etiquettes(self.controler()), ["chemin du dépôt"])

    def test_les_formes_generiques_restent_publiables(self):
        """La documentation doit pouvoir montrer des chemins d'exemple."""
        self.ecrire("fiche.md",
                    "COFFRE=/chemin/vers/le/coffre\n"
                    "cd /home/moi/coffre\n"
                    "cd ~/coffre et C:\\coffre\n"
                    "voir `IA/skills/` et son sous-dossier OBSIA/\n")

        self.assertEqual(self.etiquettes(self.controler()), [])

    def test_sans_machine_le_controle_ne_depend_pas_du_poste(self):
        """Par défaut, rien n'est contrôlé : un test passe ici et partout."""
        self.ecrire("notes.md", "Le coffre vit dans %s\n" % self.COFFRE)

        self.assertEqual(self.etiquettes(PUB.controler_fuites(self.racine)), [])

    def test_un_chemin_ne_se_force_pas(self):
        """Publier malgré tout publierait l'arborescence privée."""
        self.assertIn("chemin du coffre", PUB.SANS_FORCAGE)
        self.assertIn("chemin du dépôt", PUB.SANS_FORCAGE)


class TestLaFormeTilde(BaseControle):
    """`~/coffre` et `/home/moi/coffre` désignent la même arborescence.

    Une note du coffre — et plus encore une commande recopiée — écrit souvent
    le chemin en `~`. Les deux formes fuient autant l'une que l'autre.

    Le home est passé à la main : `Path.home()` serait celui de la machine qui
    lance le test, et le test dépendrait d'elle.
    """

    MAISON = Path("/home/moi")
    COFFRE = MAISON / "coffre-de-test"
    DEPOT = COFFRE / "OBSIA"

    def controler(self, machine=None, maison=None) -> "PUB.Controle":
        return PUB.controler_fuites(self.racine,
                                    machine=machine or self.DEPOT,
                                    maison=maison or self.MAISON)

    def test_la_forme_tilde_est_vue_comme_le_chemin(self):
        self.ecrire("notes.md",
                    "cd ~/coffre-de-test/OBSIA puis ~/coffre-de-test\n")

        self.assertEqual(self.etiquettes(self.controler()), ["chemin du dépôt"])

    def test_une_forme_tilde_sans_rapport_reste_muette(self):
        """`~/coffre` n'est pas `/srv/coffre-de-test` : ne pas confondre."""
        self.ecrire("notes.md", "cd ~/coffre-de-test puis ~/autre\n")

        controle = self.controler(machine=Path("/srv/coffre-de-test/OBSIA"))

        self.assertEqual(self.etiquettes(controle), [])

    def test_le_home_lui_meme_ne_se_pose_pas(self):
        """Un coffre qui *est* le home ne fait pas de `~` tout court un motif."""
        self.ecrire("notes.md", "cd ~ puis ls\n")

        controle = self.controler(machine=Path("/home/moi/OBSIA"))

        self.assertEqual(self.etiquettes(controle), [])


class TestLaRacineCourte(BaseControle):
    """Une installation dans un dossier de premier niveau, le dépôt dans `/srv`.

    Le coffre y tient dans `/srv` tout court, et ce motif-là se signalerait dans
    la moitié des textes qui parlent d'un serveur ou d'un montage. Un contrôle qui
    crie à tort est un contrôle qu'on force sans le lire. Le dépôt, lui, garde
    son motif : le dossier du dépôt désigne bien quelque chose.

    Le chemin est recollé à l'exécution, comme les valeurs d'essai : une
    installation réelle au même endroit serait bloquée par ce fichier même.
    """

    DEPOT = Path("/srv") / "OBSIA"

    def controler(self) -> "PUB.Controle":
        return PUB.controler_fuites(self.racine, machine=self.DEPOT)

    def test_le_parent_de_premier_niveau_ne_signe_personne(self):
        """`/srv` seul n'est pas une fuite ; le dépôt juste en dessous, si."""
        self.ecrire("fiche.md", "Tout vit dans /srv\net cd %s\n" % self.DEPOT)

        self.assertEqual(self.etiquettes(self.controler()), ["chemin du dépôt"])


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


    def test_un_chemin_de_machine_ne_se_force_pas(self):
        """De bout en bout : le chemin de la source arrête la publication.

        La source des tests est un dossier temporaire ; c'est **ce** chemin-là qui
        tient le rôle de la machine qui publie, et il ne s'écrit nulle part
        ailleurs qu'ici — le chemin réel d'un poste n'a rien à faire dans un
        fichier publié, pas même dans un test qui parle de lui.
        """
        self.ecrire("notes.md", "Le dépôt vit dans %s\n" % self.source.resolve())
        self.committer()

        resultat = self.lancer("--appliquer", "--forcer")

        self.assertEqual(resultat.returncode, 1, resultat.stdout + resultat.stderr)
        self.assertIn("chemin du dépôt", resultat.stdout + resultat.stderr)
        self.assertEqual(self.publies(), set(),
                         "rien ne doit être écrit dans la cible")


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


class TestLeTexteDeLaPREnLigneDeCommande(unittest.TestCase):
    """`--controler-texte` : le mode CI, qui juge la PR et rien d'autre.

    La vérification n'a pas d'arbre exporté sous la main — GitHub lui donne le
    titre et la description, qu'elle passe par l'entrée standard. Le mode doit
    donc pouvoir refuser sans `--cible`, et ne rien lire d'autre que le flux.
    """

    def lancer(self, texte: str, *arguments: str) -> "subprocess.CompletedProcess":
        return subprocess.run(
            [sys.executable, "-B", str(PUBLIER), "--controler-texte", *arguments],
            input=texte, capture_output=True, text=True, check=False)

    def test_le_texte_du_flux_est_juge(self):
        resultat = self.lancer("titre anodin\n%s\n" % assemble("192.168.1.", "42"))

        self.assertEqual(resultat.returncode, 1)
        self.assertIn("adresse IP privée", resultat.stdout)

    def test_un_texte_propre_passe_sans_cible(self):
        resultat = self.lancer("Chantier souveraineté des données\n")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("Aucune trouvaille", resultat.stdout)

    def test_une_cle_ne_se_force_pas(self):
        resultat = self.lancer(
            "BEGIN %s\n" % assemble("-----BEGIN ", "PRIVATE KEY-----"),
            "--forcer")

        self.assertEqual(resultat.returncode, 1)
        self.assertIn("ne s'applique pas ici", resultat.stderr)

    def test_un_texte_vide_passe(self):
        """La description d'une PR peut être vide : ce n'est pas une fuite."""
        resultat = self.lancer("")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)

    def test_sans_cible_le_mode_ordinaire_refuse(self):
        resultat = subprocess.run([sys.executable, "-B", str(PUBLIER)],
                                  input="", capture_output=True, text=True,
                                  check=False)

        self.assertEqual(resultat.returncode, 2)
        self.assertIn("--cible est requis", resultat.stderr)


if __name__ == "__main__":
    unittest.main()
