# Coder avant le cadrage fait grossir l'outil, jamais converger

Leçon tirée du daemon AIo (dépôt `ia-orchestrator`), construit comme harness
candidat pour piloter OBSIA depuis le PC et le téléphone.

## Statut
🟢 Vérifiée — le 2026-09-11, en comparant des harnais pour OBSIA : la
comparaison a fini par regarder l'historique du projet candidat lui-même.

---

## Le constat

AIo devait répondre à cinq besoins précis : continuité de conversation entre
PC et téléphone, connexion aux API et aux modèles locaux, hébergement sur le
NAS accessible de l'extérieur, interface graphique, multi-sessions. Il les
remplit tous, sur le papier. Mais rien de tout ça n'a jamais été figé par
écrit avant de coder — et l'historique du dépôt en porte la marque :

- **deux pivots d'architecture** en 21 commits : réécriture d'AionUi en
  application de bureau (PyQt6), puis remplacement par un service ACP avec
  interface web ;
- **dix fonctionnalités empilées** PR après PR — QR code, restriction IP,
  tâches planifiées, mode équipe, intégration OBSIA complète, dossiers de
  définitions, terminal intégré, aperçu de fichiers, fournisseur llama.cpp —
  sans qu'aucune ne revienne revalider l'ensemble ;
- **deux fichiers devenus énormes** : `server/http.py` (1560 lignes) et
  `server/hub.py` (1031 lignes) concentrent le quart des 10 700 lignes du
  dépôt — la signature d'un empilement, pas d'un découpage voulu ;
- **un correctif d'urgence** (commit `86b916d`) pour deux fuites de droits
  entre sessions : les zones d'écriture (`brouillon/`, `mémoire/<agent>/`)
  étaient posées sur l'agent partagé au lieu d'être attachées à chaque
  session, et une conversation héritait des droits d'une autre.

Aucun de ces symptômes n'est un défaut de modèle ou de langage. Le code
produit à chaque étape était correct pour l'étape ; c'est l'absence de vue
d'ensemble validée qui a laissé la complexité s'accumuler sans qu'aucun point
d'arrêt ne dise « stop, on revérifie que c'est toujours ce qui est voulu ».

## La leçon

C'est exactement le constat qui a justifié la création de l'agent `batisseur`
([[2026-09-09-agent-de-construction]]) : « un outil qui a de bonnes parties
sans être le bon outil est la signature d'un cadrage sauté ». Cette note en
est la première confirmation empirique — le protocole n'avait encore jamais
été éprouvé sur un projet réel.

Trois signaux à surveiller, dans n'importe quel projet, harness compris :

| Signal observé chez AIo | Ce qu'il aurait fallu |
| --- | --- |
| pivot d'architecture en cours de route | une stack choisie une fois, coût d'entretien accepté d'avance (`choix-de-la-stack`) |
| fonctionnalités ajoutées sans revalider le tout | un plan en tranches, chacune démontrée avant la suivante (`plan-de-livraison`, `construction-dune-tranche`) |
| bug corrigé en urgence, sans hypothèses posées d'abord | localiser, hypothèses falsifiables, instrumenter, corriger — jamais de correctif à la volée (`investigation-de-bug`) |

Aucun de ces garde-fous n'est cher à poser. Ce qu'ils coûtent, c'est de la
discipline en cours de route — refuser d'élargir une tranche, refuser de
corriger un cadrage « dans sa tête » sans réécrire le document. C'est
précisément ce qui a manqué ici.

## Décision qui en découle

Plutôt que de continuer à empiler des correctifs sur AIo, ou que de le
réécrire une troisième fois sans méthode, la voie choisie est de repartir à
zéro **via le bâtisseur**, en traitant `ia-orchestrator` comme l'existant à
inventorier (`inventaire-de-lexistant`) : ce qui s'est révélé juste (ACP,
fournisseurs Ollama/llama.cpp, terminal intégré, appairage QR) devient une
liste à reprendre ; ce qui a cassé (l'absence de découpage, l'accumulation
sans plan) devient une liste de ce qu'on ne refait pas.

## Portée

Vaut pour tout projet de construction dans ce coffre, pas seulement pour un
harness. Le signal à surveiller n'est pas « le code a des bugs » — tout code
en a — mais « le périmètre a changé plusieurs fois sans qu'un document soit
rouvert pour en décider ». Le second est un cadrage sauté ; le premier, un
aléa normal de la construction.
