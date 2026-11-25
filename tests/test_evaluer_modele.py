"""L'épreuve « gestionnaire » du banc : ce qu'elle compte juste, ce qu'elle refuse.

`evaluer_modele.py` éprouvait un modèle contre sept pièges du contrat ; il ne
disait rien de sa capacité à **mener une équipe**. L'épreuve gestionnaire pose
cinq situations de boucle et note le registre de progression rendu : conforme
au schéma publié par `orchestration-equipe`, puis juste sur la situation.

Aucun serveur ici : la notation est une fonction d'une réponse, on lui tend
des réponses écrites à la main — une juste par cas, et chaque faute qu'elle
doit voir.
"""

import importlib.util
import json
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "scripts" / "evaluer_modele.py"

_spec = importlib.util.spec_from_file_location("evaluer_modele", SCRIPT)
EM = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(EM)


def registre(satisfaite=False, boucle=False, progres=True, membre="", consigne=""):
    return {
        "demande_satisfaite": {"reason": "r", "answer": satisfaite},
        "en_boucle": {"reason": "r", "answer": boucle},
        "progres": {"reason": "r", "answer": progres},
        "prochain_membre": {"reason": "r", "answer": membre},
        "consigne": {"reason": "r", "answer": consigne},
    }


def bloc(donnee):
    return "Voici le registre.\n\n```json\n%s\n```\n" % json.dumps(donnee, ensure_ascii=False)


def cas(nom):
    return next(c for c in EM.CAS_GESTIONNAIRE if c["nom"] == nom)


# Une réponse juste par cas : le banc doit les compter justes.
JUSTES = {
    "premier-ticket": registre(
        membre="visionnaire",
        consigne="Dis si l'export CSV du projet Facturier rapproche du cap de sa vision."),
    "suite-du-plan": registre(
        membre="contradicteur",
        consigne="Relis la branche batisseur/export-csv du projet Facturier et rends ton verdict."),
    "blocage-repere": registre(
        boucle=True, progres=False, membre="contradicteur",
        consigne="La branche batisseur/export-csv est poussée sur origin : relis-la."),
    "demande-satisfaite": registre(satisfaite=True),
    "membre-hors-equipe": registre(
        membre="contradicteur",
        consigne="Relis la branche batisseur/export-csv du projet Facturier et rends ton verdict."),
}


class SchemaLuDansLeSkill(unittest.TestCase):

    def test_le_schema_vient_du_skill_et_porte_les_cinq_cles(self):
        schema = EM.charger_schema_registre()
        self.assertEqual(
            sorted(schema["required"]),
            ["consigne", "demande_satisfaite", "en_boucle", "prochain_membre", "progres"])


class ChaqueCasAUneReponseJuste(unittest.TestCase):

    def test_cinq_cas_et_chacun_compte_juste_sa_bonne_reponse(self):
        schema = EM.charger_schema_registre()
        self.assertEqual(sorted(c["nom"] for c in EM.CAS_GESTIONNAIRE), sorted(JUSTES))
        for nom, donnee in JUSTES.items():
            with self.subTest(cas=nom):
                ok, motif = EM.noter_gestionnaire(cas(nom), bloc(donnee), schema)
                self.assertTrue(ok, motif)

    def test_le_raisonnement_retire_avant_lecture(self):
        schema = EM.charger_schema_registre()
        reponse = ("<think>```json\n{\"brouillon\": 1}\n```</think>"
                   + bloc(JUSTES["premier-ticket"]))
        ok, motif = EM.noter_gestionnaire(cas("premier-ticket"), reponse, schema)
        self.assertTrue(ok, motif)

    def test_le_nom_du_membre_se_lit_sans_casse_ni_backticks(self):
        # Relecture du 2026-11-19 : « Contradicteur » était refusé comme hors
        # de l'équipe — une faute de typographie, pas de jugement.
        schema = EM.charger_schema_registre()
        for nom in ("Contradicteur", "`contradicteur`", " CONTRADICTEUR "):
            with self.subTest(nom=nom):
                donnee = dict(JUSTES["suite-du-plan"],
                              prochain_membre={"reason": "r", "answer": nom})
                ok, motif = EM.noter_gestionnaire(cas("suite-du-plan"), bloc(donnee), schema)
                self.assertTrue(ok, motif)

    def test_un_json_nu_sans_bloc_est_lu(self):
        schema = EM.charger_schema_registre()
        reponse = json.dumps(JUSTES["demande-satisfaite"])
        ok, motif = EM.noter_gestionnaire(cas("demande-satisfaite"), reponse, schema)
        self.assertTrue(ok, motif)


class FautesDeForme(unittest.TestCase):

    def setUp(self):
        self.schema = EM.charger_schema_registre()
        self.cas = cas("premier-ticket")

    def faute(self, reponse, mot):
        ok, motif = EM.noter_gestionnaire(self.cas, reponse, self.schema)
        self.assertFalse(ok)
        self.assertIn(mot, motif)

    def test_prose_sans_registre(self):
        self.faute("Je confie la première étape au visionnaire.", "registre")

    def test_cle_manquante(self):
        donnee = dict(JUSTES["premier-ticket"])
        del donnee["en_boucle"]
        self.faute(bloc(donnee), "en_boucle")

    def test_cle_inattendue(self):
        donnee = dict(JUSTES["premier-ticket"], plan={"reason": "r", "answer": "x"})
        self.faute(bloc(donnee), "plan")

    def test_booleen_ecrit_en_chaine(self):
        donnee = dict(JUSTES["premier-ticket"],
                      progres={"reason": "r", "answer": "true"})
        self.faute(bloc(donnee), "progres")

    def test_deux_blocs_json(self):
        double = bloc(JUSTES["premier-ticket"]) + bloc(JUSTES["premier-ticket"])
        self.faute(double, "blocs")


class FautesDeJugement(unittest.TestCase):

    def setUp(self):
        self.schema = EM.charger_schema_registre()

    def noter(self, nom, donnee):
        return EM.noter_gestionnaire(cas(nom), bloc(donnee), self.schema)

    def test_le_gestionnaire_ne_se_designe_jamais(self):
        ok, motif = self.noter("premier-ticket", registre(
            membre="batisseur", consigne="Je fais l'export CSV du projet Facturier."))
        self.assertFalse(ok)
        self.assertIn("gestionnaire", motif)

    def test_un_membre_hors_equipe_est_refuse(self):
        ok, motif = self.noter("membre-hors-equipe", registre(
            membre="assistant",
            consigne="Range la note de l'export CSV du projet Facturier."))
        self.assertFalse(ok)
        self.assertIn("équipe", motif)

    def test_mauvais_membre_pour_l_etape(self):
        ok, motif = self.noter("suite-du-plan", registre(
            membre="visionnaire",
            consigne="Redis si l'export CSV du projet Facturier suit la vision."))
        self.assertFalse(ok)
        self.assertIn("contradicteur", motif)

    def test_consigne_vide(self):
        ok, motif = self.noter("premier-ticket", registre(membre="visionnaire", consigne="  "))
        self.assertFalse(ok)
        self.assertIn("consigne", motif)

    def test_consigne_qui_suppose_la_conversation(self):
        ok, motif = self.noter("suite-du-plan", registre(
            membre="contradicteur", consigne="Relis ce qu'on vient de faire."))
        self.assertFalse(ok)
        self.assertIn("consigne", motif)

    def test_blocage_non_vu(self):
        ok, motif = self.noter("blocage-repere", registre(
            membre="contradicteur",
            consigne="Relis la branche batisseur/export-csv du projet Facturier."))
        self.assertFalse(ok)
        self.assertIn("blocage", motif)

    def test_blocage_confie_au_mauvais_membre(self):
        # Le §6 ne désigne aucun membre : il vient du plan, et la relecture de
        # la branche est l'étape du contradicteur.
        ok, motif = self.noter("blocage-repere", registre(
            boucle=True, progres=False, membre="visionnaire",
            consigne="Relis la branche batisseur/export-csv du projet Facturier."))
        self.assertFalse(ok)
        self.assertIn("contradicteur", motif)

    def test_blocage_annonce_a_tort(self):
        ok, motif = self.noter("suite-du-plan", registre(
            boucle=True, membre="contradicteur",
            consigne="Relis la branche batisseur/export-csv du projet Facturier."))
        self.assertFalse(ok)
        self.assertIn("blocage", motif)

    def test_demande_satisfaite_non_reconnue(self):
        ok, motif = self.noter("demande-satisfaite", registre(
            membre="contradicteur",
            consigne="Relis encore la branche batisseur/export-csv du projet Facturier."))
        self.assertFalse(ok)
        self.assertIn("satisfaite", motif)

    def test_fin_annoncee_trop_tot(self):
        ok, motif = self.noter("suite-du-plan", registre(satisfaite=True))
        self.assertFalse(ok)
        self.assertIn("satisfaite", motif)


class SchemaHorsDePortee(unittest.TestCase):
    """Le validateur ne connaît qu'un sous-ensemble de JSON Schema : ce qu'il
    ne connaît pas l'arrête net, au lieu de planter ou de laisser passer."""

    def refuse(self, schema):
        with self.assertRaises(EM.SchemaNonPris):
            EM.valider_registre({"a": 1}, schema, schema)

    def test_un_mot_cle_inconnu_arrete(self):
        self.refuse({"type": "object", "properties": {"a": {"enum": [1]}}})

    def test_un_type_inconnu_arrete(self):
        self.refuse({"type": "object", "properties": {"a": {"type": "integer"}}})

    def test_une_liste_de_types_arrete(self):
        self.refuse({"type": "object", "properties": {"a": {"type": ["string", "null"]}}})

    def test_le_schema_du_skill_est_pris(self):
        schema = EM.charger_schema_registre()
        EM.valider_registre(JUSTES["premier-ticket"], schema, schema)


class Seuil(unittest.TestCase):

    def test_neuf_sur_dix_passe_huit_sur_dix_non(self):
        self.assertTrue(EM.seuil_gestionnaire_tenu(9, 10))
        self.assertFalse(EM.seuil_gestionnaire_tenu(8, 10))
        self.assertFalse(EM.seuil_gestionnaire_tenu(0, 0))


if __name__ == "__main__":
    unittest.main()
