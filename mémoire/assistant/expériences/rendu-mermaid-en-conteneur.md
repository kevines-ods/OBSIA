# Rendre du Mermaid dans un conteneur demande --no-sandbox

Leçon réutilisable sur le skill `mermaid`. Vaut pour toute machine sans
session graphique : conteneur, VM Debian, exécution en CI.

## Statut
🟢 Vérifiée le 2026-09-03 lors d'un test du workflow du coffre.

---

## Le constat

`mermaid-cli` s'installe et se lance sans problème via `npx`, mais la
génération échoue à l'étape suivante : l'outil pilote un Chromium par
Puppeteer, et ce Chromium refuse de démarrer sous l'utilisateur `root` d'un
conteneur. L'erreur ne parle pas de Mermaid, elle vient de
`@puppeteer/browsers/lib/launch.js` — d'où le temps perdu à chercher au mauvais
endroit.

## La manœuvre qui marche

Passer un fichier de configuration Puppeteer à l'option `-p` :

```bash
echo '{"args":["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"]}' > pptr.json
npx -y @mermaid-js/mermaid-cli -p pptr.json -i diagramme.mmd -o diagramme.svg
```

Les trois options ne servent pas la même chose :

| Option | Ce qu'elle évite |
| --- | --- |
| `--no-sandbox` | le bac à sable de Chromium, indisponible en conteneur |
| `--disable-gpu` | la recherche d'une carte graphique absente |
| `--disable-dev-shm-usage` | le `/dev/shm` minuscule des conteneurs |

Sur le poste CachyOS avec KDE, aucune de ces options n'est nécessaire : il y a
une vraie session graphique et un utilisateur non privilégié.

## La leçon

Un skill qui appelle un outil web sous le capot hérite des contraintes de cet
outil. Le prérequis à vérifier n'est pas « la commande est-elle installée »
mais « la commande arrive-t-elle jusqu'au bout sur cette machine ».

## Conséquence pour le coffre

La plupart du temps la question ne se pose pas : `IA/skills/mermaid.md` demande
de préférer le **bloc Mermaid brut** au SVG dans une note du coffre, et
Obsidian rend ce bloc lui-même, sans Chromium. Le rendu SVG n'est utile que
pour un export hors coffre — un README GitHub, par exemple.
