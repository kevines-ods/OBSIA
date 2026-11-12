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

## Raccourcir les attentes

```bash
python3 raccourcir.py videos/5-contradicteur.mp4
```

Rien n'est coupé : là où l'écran ne bouge plus pendant plus de huit secondes,
le milieu de l'attente est accéléré. Un sous-agent qui travaille quatre minutes
tient alors en moins d'une.

## Les scènes

| Scène | Ce qu'elle montre | Question posée |
| --- | --- | --- |
| `1-accueil` | les agents, et l'état du coffre trouvé au démarrage | « Qu'est-ce que tu peux faire pour moi dans ce coffre ? » |
| `2-reprise` | le chantier retrouvé par son carnet | « Où en est mon projet de serre ? » |
| `3-prudence` | une commande douteuse expliquée, pas lancée | « Je peux la lancer ? » |
| `4-rangement` | l'aperçu avant l'écriture, puis le rangement | « Montre-moi d'abord comment tu rangerais mes notes en vrac » |
| `5-contradicteur` | le `contradicteur` appelé en sous-agent, qui relit sans modifier | « @contradicteur relis mon plan d'arrosage » |
| `6-visionnaire` | le `visionnaire` appelé en sous-agent, une idée confrontée à la vision | « @visionnaire … est-ce que ça va dans le sens du projet ? » |
| `7-secret` | un mot de passe (inventé) refusé dans une note | « Note que le mot de passe du wifi est… » |
| `8-memoire` | une préférence retenue, retrouvée dans une séance neuve | « Retiens que… », puis `/new` |

Les deux sous-agents sont déclarés par `tourner.sh` dans l'`opencode.json` du
coffre fictif : leur prompt pointe la fiche de `IA/agents/`, rien n'est recopié.

Une scène est un fichier `scenes/<nom>.tape` : pour en ajouter une, copier la
plus proche et changer la question.

## Limites

- **Le modèle ne répond jamais deux fois pareil** : refaire la prise qui ne
  plaît pas.
- **La fin d'une réponse** se repère à la ligne `Build · <modèle> · <durée>`
  qu'opencode affiche. Pour une seconde question dans la même scène, ce repère
  est déjà à l'écran : l'attente est alors une durée fixe, à ajuster
  (`4-rangement`). `/new` vide l'écran et rend le repère fiable (`8-memoire`).
- **Un modèle peut agir sans attendre l'accord** : à « Range mes notes », une
  prise a tout classé d'un coup. La question de `4-rangement` demande donc
  l'aperçu d'abord.
- **Quota atteint** : opencode affiche une fenêtre « Free limit reached » et la
  prise est perdue. `tourner.sh` s'arrête sur l'échec.
