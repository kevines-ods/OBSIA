# Démo OBSIA — coffre de test piloté par opencode

Ce dossier produit la vidéo de démonstration d'OBSIA : un coffre de notes
factices (PROJETS, SAVOIRS, courrier inter-agents, tâches planifiées) exploré
par le harness **opencode**.

## Ce qu'on y voit

- `demo.gif` — la vidéo (≈ 19 s), rendue depuis l'enregistrement terminal ;
- `demo.cast` — le même enregistrement au format asciinema : `asciinema play demo.cast`
  le rejoue dans un vrai terminal.

La session montre, dans l'ordre : la racine du coffre, l'`AGENTS.md` généré par
l'installeur, puis une session `opencode run` qui parcourt `0-PROJETS/` (résumé
d'un projet, carnet), lit le courrier dans `_MAINTENANCE/courrier/` et **y
écrit une lecture datée**, ouvre le registre privé `0-PROJETS/tâches-planifiées/`,
et termine dans `0-SAVOIRS/`.

> **Honnêteté de la démo.** Sans clé d'API de modèle dans l'environnement
> d'enregistrement, les outils du harness (lecture, écriture, shell) se sont
> **réellement exécutés** sur le coffre ; seules les réponses du modèle sont
> scriptées, par `mock-modele.py` (un serveur OpenAI-compatible local sur
> `127.0.0.1:8090`). Avec une vraie clé, la même session se rejoue sans le mock
> — voir plus bas.

## Rejouer la démo scriptée (aucune clé requise)

Prérequis : `git`, `python3`, `opencode` (`npm install -g opencode-ai` ou
`curl -fsSL https://opencode.ai/install | bash`), et pour le rendu GIF :
`pip install pyte pillow` et une police monospace TTF.

```bash
# 1. Monter le coffre de test
mkdir -p ~/coffre-demo && cd ~/coffre-demo
git clone https://github.com/kevines-ods/OBSIA
cd OBSIA
python3 scripts/installer.py --appliquer --modules noyau,planification,messagerie,construction
cd ..
python3 OBSIA/demo/semer-coffre.py .        # sème les fausses notes

# 2. Brancher opencode sur le faux modèle
cp OBSIA/demo/opencode-demo.json opencode.json

# 3. Enregistrer
python3 OBSIA/demo/mock-modele.py &          # le « cerveau » scripté, 127.0.0.1:8090
python3 OBSIA/demo/enregistrer-demo.py "$PWD" demo.cast
kill %1

# 4. (optionnel) Rendre en GIF
python3 OBSIA/demo/rendre-gif.py demo.cast demo.gif
```

`rendre-gif.py` attend la police à `/tmp/jetbrains-mono.ttf` ; pour un autre
chemin : `POLICE=/chemin/mono.ttf python3 OBSIA/demo/rendre-gif.py …`.

## Refaire une vraie vidéo, avec un vrai modèle

Le déroulé est identique ; seul le « cerveau » change.

1. Montez le coffre et semez-le comme ci-dessus (étapes 1 et 2, en remplaçant
   `opencode-demo.json` par une configuration pointant votre fournisseur —
   voir la fiche `IA/system/adaptateurs-harness/opencode.md`, §5 : la fenêtre
   de contexte déclarée doit couvrir le prompt OBSIA, 65 536 au minimum pour
   un petit modèle local).
2. Remplacez la commande `opencode run` de `session-demo.sh` par la même
   commande sans `-m obsia-mock/mock-brain` (ou avec votre modèle), et lancez
   l'enregistrement sans le mock :

```bash
python3 OBSIA/demo/enregistrer-demo.py "$PWD" demo.cast
```

3. Enregistrez à l'écran (OBS, ou un simple `asciinema play` filmé), ou
   restez au GIF : `rendre-gif.py` ne dépend pas du modèle.

## Fichiers

| Fichier | Rôle |
| --- | --- |
| `demo.gif`, `demo.cast` | la vidéo produite et sa source rejouable |
| `semer-coffre.py` | crée les fausses notes dans un coffre fraîchement installé |
| `mock-modele.py` | serveur OpenAI-compatible local : réponses scriptées, outils réels |
| `session-demo.sh` | le déroulé filmé : shell de contexte + `opencode run` |
| `enregistrer-demo.py` | capture la session sous PTY en `.cast` asciinema v2 |
| `rendre-gif.py` | convertit le `.cast` en GIF animé |
| `opencode-demo.json` | configuration opencode à poser à la racine du coffre |
