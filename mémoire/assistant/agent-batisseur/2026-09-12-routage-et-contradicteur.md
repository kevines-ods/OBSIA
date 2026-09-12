# 2026-09-12 — Un troisième agent, et un contrôle qui a trouvé quatre défauts

Second lot repris d'`addyosmani/agent-skills` : un agent de relecture en
lecture seule absolue, ses deux skills, et le portage de l'étage de routage
des évaluations. Ce dernier a trouvé quatre défauts réels dès sa première
exécution.

## Statut

🟢 Écrit, vérifié, et le script de routage **branché en CI et en pré-commit**,
avec son refus éprouvé sur un cas volontairement faux. 3 agents, 33 skills.

## Décisions

- **Un agent de relecture, en `read_only: true`** plutôt que quatre personas.
  Le §1 est strict — un agent est un interlocuteur avec une mémoire — et
  quatre agents de plus auraient alourdi le coffre pour un seul besoin.
- **Lecture seule absolue, donc pas de mémoire.** Choisi, pas subi : un
  relecteur qui peut corriger corrige au lieu de relever, et le défaut
  disparaît sans que personne n'apprenne qu'il existait. Contrepartie assumée
  et écrite au §6 : un constat non repris est un constat perdu.
- **Aucun MCP déclaré** pour cet agent : lire un diff se fait par `git diff`,
  en local. Déclarer un outil capable d'écrire sur un dépôt distant
  contredirait son `read_only`.
- **Les exemptions du contrôle vivent dans le script**, jamais dans le
  frontmatter d'un skill. Idée reprise de leur linter, et elle vaut : un skill
  qui se déclare lui-même dispensé d'un contrôle annule le contrôle.

## Évidence — ce que le script a trouvé

Première exécution sur 31 demandes écrites comme l'utilisateur parle :
**quatre échecs**. Deux étaient des artefacts de mon propre outil, deux des
défauts réels de description. Les séparer était la première chose à faire.

| Défaut | Nature | Correction |
| --- | --- | --- |
| `cadrage-produit` au rang 7 | artefact — `fige` ne rejoignait pas `figer` | radical minimal ramené de 4 à 3 lettres |
| `mise-en-ligne` au rang 6 | artefact **et** défaut — `déploie` ≠ `déployer`, et « déployer » manquait à la description | alternance `y`/`i` traitée, et le mot ajouté |
| `investigation-de-bug` à zéro | **réel** — aucun mot commun avec « ça plante quand je clique » | description refaite avec le vocabulaire réel |
| `cloture-de-session` à zéro | **réel** — « séance » et « ce qui a été décidé » manquaient | idem |

Après correction : 33 demandes sur 33, aucune collision au-delà de 0,62.

## Interprétation

**Une attente de test peut être fausse, et la relâcher n'est pas toujours une
capitulation.** Une demande exigeait que `mise-en-ligne` devance `traefik` sur
« déploie le service et rends-le joignable par son nom de domaine ». Or
« nom de domaine » est le vocabulaire signature de `traefik` : pour le
dépasser, il aurait fallu charger `mise-en-ligne` des mots de `traefik`, ce
qui aurait dégradé le cas symétrique — celui où `traefik` doit gagner, et
gagne largement.

La distinction se juge en regardant le cas symétrique. Le vrai défaut était le
rang 6 ; l'exigence de devancer était mon excès. L'attente est passée à
« dans les deux premiers rangs », et la raison est écrite dans le registre
pour qu'un lecteur sache qu'elle a été raisonnée, pas contournée.

C'est exactement le geste que `plancher-qualite` interdit à un agent — ajuster
un seuil pour passer au vert. La différence tient à une chose, et une seule :
la raison est écrite, visible en revue, et le cas symétrique la contrôle.

## Questions ouvertes

- La mesure est lexicale. Elle ne verra jamais qu'un utilisateur dit
  « séance » là où la description dit « session » — sauf si le mot est écrit.
  L'étage comportemental, qui coûte des jetons, n'est pas porté.
- Le `contradicteur` ne vaut que par un **contexte neuf**. Dans la
  conversation où le code a été écrit, il relit ses propres conclusions. Le
  skill impose de l'annoncer comme dégradé ; reste à voir si un harness sait
  vraiment ouvrir une session neuve pour lui.
- Aucun des deux skills de relecture n'a servi sur un vrai diff.

## Synthèse IA

Le registre `IA/system/routage-attendu.md` a une propriété qu'il faut
entretenir : ses demandes doivent venir de vraies formulations. Une demande
imaginée par celui qui écrit la description teste la description contre
elle-même. La meilleure source est une demande qui a mal été routée en
conversation, reprise telle quelle.

## URLs sources

- https://github.com/addyosmani/agent-skills
