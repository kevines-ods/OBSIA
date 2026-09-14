# 2026-09-14 — La mémoire se partage par ce qu'elle décrit, pas par agent

Refonte de `mémoire/` : profil, préférences et projets remontent à la racine et
deviennent communs ; seul `expériences/` reste chez l'agent.

## Statut

🟢 Appliqué et vérifié — `verifier_coffre.py` et `evaluer_routage.py` sortent
en 0. Éprouvé sur les 29 notes existantes, jamais encore sur un second agent
qui écrirait réellement en mémoire.

---

## Le déclencheur

Constat de l'utilisateur : « les mémoires du bâtisseur sont dans assistant
alors que c'est 2 agents différents ».

Le constat était faux dans sa lettre et juste dans son fond. Le bâtisseur
n'avait aucune mémoire : ce qui se trouvait dans
`mémoire/assistant/agent-batisseur/` était un dossier de **projet** — les
notes de la séance où l'assistant a construit l'agent bâtisseur. Le nom du
dossier, lui, se lisait comme un espace mémoire d'agent.

## Décisions

- **L'axe de découpe change.** Il n'est plus « quel agent a écrit » mais
  **« qu'est-ce que la note décrit »** :

  | Contenu | Décrit | Où |
  | --- | --- | --- |
  | `profil-utilisateur.md` | l'utilisateur | racine, commun |
  | `préférences/` | ses règles | racine, commun |
  | `projets/<nom-projet>/` | un chantier | racine, commun |
  | `<agent>/expériences/` | ce qu'un agent a appris | chez l'agent |

- **Les projets remontent aussi**, ce qui n'était pas demandé. Motif : un
  chantier ouvert par un agent et repris par un autre aurait vu son histoire
  coupée en deux dossiers, sans que rien ne le signale. Un projet n'appartient
  pas à qui l'a ouvert.

- **`expériences/` reste chez l'agent.** C'est la seule chose qui lui
  appartienne : ce qu'il a appris sur sa propre manière de travailler. Le glob
  `mémoire/*/expériences/` de `compilation-des-lecons` continue de fonctionner
  sans changement.

- **`agent-batisseur/` devient `construction-du-batisseur/`.** Un nom de
  projet dit le chantier, jamais qui l'a mené — sans quoi il se lit comme un
  agent. Règle ajoutée au §6.

- **Le contrat perd une règle au lieu d'en gagner une.** L'exception « tout
  agent lit `profil-utilisateur.md`, celui qui n'est pas chez lui le complète
  par patch » disparaît : le fichier est commun, tout agent `read_only: false`
  le corrige sur place.

- **`IA/system/session-log/` est exempté du contrôle des chemins.** Découvert
  en appliquant le changement, cf. la leçon dédiée.

## Évidence

- Le §6 du contrat portait déjà la rustine, écrite noir sur blanc : « il reste
  unique dans le coffre […] celui qui n'est pas chez lui le complète par
  patch ». Une exception rédigée et jamais relue comme un symptôme.
- Les trois notes de `préférences/` — français, logiciel libre, portabilité
  entre harness — énoncent des règles de l'utilisateur, aucune ne décrit
  l'assistant.
- Les sept notes d'`expériences/` s'ouvrent toutes sur « leçon générale /
  réutilisable, vaut pour tout… » : aucune n'est propre à l'assistant non
  plus. C'est le point faible connu du découpage retenu.

## Interprétation

Le découpage par agent avait l'air d'une garantie d'isolation. Il n'isolait
rien d'utile : il rendait seulement plus coûteux l'accès à ce qui était commun,
et le coût se payait en exceptions. L'isolation qui compte — un agent n'écrit
pas dans le dossier d'un autre — survit intacte à la refonte.

## Questions ouvertes

- **`expériences/` mérite-t-il de rester par agent ?** Les sept notes
  existantes plaident contre. L'arbitrage a été de conserver le découpage tant
  qu'un second agent n'a pas réellement écrit : sans deuxième jeu de notes, on
  trancherait sur un seul échantillon.
- Rien ne détecte aujourd'hui un dossier de projet mal nommé — le vérificateur
  ne contrôle pas `mémoire/`, et c'est délibéré (§11).

## Synthèse IA

La refonte a été appliquée puis vérifiée par les scripts du coffre ; les
chemins cités dans `IA/` ont été corrigés un à un. `prompt-fondateur.md` n'a
pas été touché : il porte la mention « intention d'origine, non normative » et
le réécrire falsifierait le point de départ.
