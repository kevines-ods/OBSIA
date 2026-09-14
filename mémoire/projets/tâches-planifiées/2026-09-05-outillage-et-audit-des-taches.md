# 2026-09-05 — Outillage des tâches, et l'audit qui a suivi

Le passage du registre aux timers reposait sur la seule discipline de lecture.
Il est outillé par `appliquer_taches.py`. L'audit demandé ensuite a trouvé neuf
omissions, dont cinq chemins morts qu'aucun contrôle ne voyait.

## Statut
🟢 Livré et fusionné — script, contrôle des chemins cités, CI élargie.

Le registre lui-même est décrit dans
[[2026-09-05-registre-des-taches-planifiees]].

## Décisions

- **La réconciliation est outillée pour `exécutant: local`** :
  `IA/skills/cron/scripts/appliquer_taches.py`. Aperçu par défaut — c'est le
  preview qu'impose le §2 — et `--appliquer` pour exécuter.
- **Ce script dépend de systemd, et c'est assumé.** Il ne pouvait donc pas
  vivre dans `scripts/`, qui promet de n'exiger aucune installation pour
  vérifier le coffre. Sa place est dans le skill qui s'en sert, qui passe en
  forme dossier pour l'accueillir (§5).
- **La commande qui lance un agent vit hors dépôt**, dans
  `~/.config/obsia/appliquer.conf`. Le coffre ne nomme aucun harness (§3) ;
  sans cette configuration, le script refuse d'instancier une tâche
  `mode: agent` plutôt que d'en poser une inerte.
- **Ce qu'il retire est archivé hors du dépôt**, sous
  `~/.local/share/obsia/archive/`. Une unité systemd porte des chemins de la
  machine et le dépôt est public (§9) : l'esprit du §2 — rien n'est détruit —
  est tenu sans publier ce qui n'a pas à l'être.
- **Le vérificateur contrôle les chemins cités et les liens Markdown** de
  `IA/` et de la racine, et s'arrête là : `mémoire/` est un récit, où une note
  ancienne cite légitimement un état révolu. Le contrôle vise ce qui **agit**.
  Leçon consignée dans [[index-maintenus-a-la-main]].

## Évidence

- Conversion cron → `OnCalendar` validée par `systemd-analyze calendar` sur
  huit expressions, dont `*/15 * * * *` → `*-*-* *:0/15:00` et
  `0 18 * * 1-5` → `Mon..Fri *-*-* 18:00:00`. Les champs numériques sont
  produits dans la forme normale de systemd (`*-*-01`, pas `*-*-1`) : sinon la
  relecture croit à un écart.
- Les six verdicts essayés sur un `HOME` bidon : à créer, à jour, à corriger,
  à retirer, DOUBLON, ORPHELINE. Le doublon est retiré et archivé ;
  l'orpheline est laissée en place.
- Sans `commande_agent` configurée, le script refuse et n'écrit rien.
- Audit : neuf omissions corrigées — cinq chemins morts laissés par le passage
  en forme dossier, `tâche` absent des valeurs de `kind` au §5, `exécutant`
  absent du prompt généré, l'en-tête de `IA/README.md` qui ignorait la section
  qu'il liste, le schéma du brouillon resté à un OBSIA sans tâches.

## Interprétation

Le chemin le plus dangereux était celui de l'instruction de la tâche
elle-même : au déclenchement du lundi, l'agent aurait cherché un fichier
absent, sans conversation pour rattraper. Une instruction auto-suffisante l'est
d'autant moins que ses chemins ne sont vérifiés par rien.

## Questions ouvertes

- Le script ne sait pas retirer une instance orpheline : il la signale et
  s'arrête là. Volontaire — reste à voir si c'est vivable à l'usage.
- Rien n'a été instancié sur une machine réelle : la configuration locale et
  le premier `--appliquer` restent à faire côté utilisateur.

## Synthèse IA

Outiller un geste ne suffit pas : il faut aussi outiller la vérification de ce
qui le décrit. Le script a été écrit en une passe et fonctionnait ; c'est
l'audit qui a trouvé les vrais dégâts, tous dans la prose autour du code.
