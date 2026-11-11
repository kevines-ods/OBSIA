# Vidéos de démonstration

De quoi tourner de courtes vidéos d'OBSIA dans opencode : une vraie séance,
un vrai modèle, des questions tapées à vitesse humaine. Rien n'est simulé ;
seule la frappe est automatisée, par [VHS](https://github.com/charmbracelet/vhs).

## Ce qu'il faut

`vhs`, `ttyd`, `ffmpeg` et `opencode`. Sur Arch ou CachyOS :

```bash
sudo pacman -S vhs ttyd ffmpeg
```

Aucune clé n'est nécessaire avec les modèles gratuits d'opencode
(`opencode models | grep free`). Leur quota est court : quelques questions par
modèle, puis plusieurs heures d'attente. Changer de modèle contourne la panne.

## Tourner

```bash
./tourner.sh                 # toutes les scènes
./tourner.sh 2-reprise       # une seule
OBSIA_DEMO_MODELE=opencode/glm-5.3-flash-free ./tourner.sh 3-prudence
```

Les vidéos arrivent dans `videos/`, qui n'est pas versionné. Avant chaque
scène, `monter_coffre_fictif.sh` refait le coffre fictif dans `~/demo-obsia` :
un clone de ce dépôt, l'`AGENTS.md` de l'installateur et des notes inventées.
Aucune donnée réelle n'y entre.

## Les scènes

| Scène | Ce qu'elle montre | Question posée |
| --- | --- | --- |
| `1-accueil` | les agents, et l'état du coffre trouvé au démarrage | « Qu'est-ce que tu peux faire pour moi dans ce coffre ? » |
| `2-reprise` | le chantier retrouvé par son carnet | « Où en est mon projet de serre ? » |
| `3-prudence` | une commande douteuse expliquée, pas lancée | « Je peux la lancer ? » |
| `4-rangement` | l'aperçu avant l'écriture, puis le rangement | « Range mes notes en vrac » |

Une scène est un fichier `scenes/<nom>.tape` : pour en ajouter une, copier la
plus proche et changer la question.

## Limites

- **Le modèle ne répond jamais deux fois pareil** : refaire la prise qui ne
  plaît pas.
- **La fin d'une réponse** se repère à la ligne `Build · <modèle> · <durée>`
  qu'opencode affiche. Pour une seconde question dans la même scène, ce repère
  est déjà à l'écran : l'attente est alors une durée fixe, à ajuster
  (`4-rangement`).
- **Quota atteint** : opencode affiche une fenêtre « Free limit reached » et la
  prise est perdue. `tourner.sh` s'arrête sur l'échec.
