# Démarrage rapide

[English](GETTING-STARTED.md) | **Français**

De zéro à une première conversation avec un agent d'OBSIA, en cinq étapes.
Il te faut seulement `git` et Python 3 : rien d'autre à installer. Obsidian est
pratique, mais pas obligatoire.

## 1. Créer ton coffre et y placer OBSIA

Ton **coffre** est le dossier qui contiendra tes notes et ta mémoire. OBSIA se
place **directement dedans**, pas dans un sous-dossier.

Pas encore de coffre ? Crée-le, puis place OBSIA dedans :

```bash
mkdir -p ~/"Mon coffre" && cd ~/"Mon coffre"
git clone https://github.com/kevines-ods/OBSIA
```

Tu as déjà un coffre (par exemple un coffre Obsidian) ? Va dedans, puis clone :

```bash
cd "/chemin/de/ton coffre"
git clone https://github.com/kevines-ods/OBSIA
```

Ne clone pas OBSIA directement dans ton dossier personnel : l'installeur
refusera, sans rien écrire.

La suite de ce guide appelle ce dossier `Mon coffre/`, quel que soit son vrai
nom. Si tu utilises Obsidian, ouvre-le sur le coffre entier, pas sur `OBSIA/`
seul. Les dossiers de notes (`0-SAVOIRS/`, `0-EN-VRAC/`…) se créent au fur et
à mesure.

## 2. Voir ce que ta machine a déjà

```bash
cd OBSIA
python3 scripts/installer.py --sonder
```

Cette commande n'écrit rien. L'installeur regarde ce qui est déjà installé
(Docker, systemd, Proxmox…) pour te proposer les bons choix à l'étape suivante.

## 3. Installer

```bash
python3 scripts/installer.py              # pose les questions, montre ce qui sera fait, n'écrit rien
python3 scripts/installer.py --appliquer  # installe
```

L'installeur te pose une question par module (« Veux-tu que les agents
sachent… ? »). Réponds selon ce que tu veux qu'ils sachent faire, même si
l'outil n'est pas encore installé chez toi. À la fin, il a créé :

- **`Mon coffre/AGENTS.md`** : les instructions qu'un harness lit au
  démarrage, à la racine du coffre. Ne le modifie pas à la main : il est refait
  à chaque installation ;
- **`Mon coffre/0-PERSONNELS/profil-utilisateur.md`** et
  **`Mon coffre/0-MEMOIRES/`** : le début de ta mémoire. Ce qui s'y trouve déjà
  n'est jamais écrasé ;
- **`OBSIA/obsia.local.yml`** : tes réponses, propres à ta machine.

Tu changes d'avis ? Relance la même commande. Pour revenir à tout le
catalogue : `python3 scripts/installer.py --tout --appliquer`.

## 4. Lancer ton harness depuis le coffre

Lance-le **toujours depuis `Mon coffre/`**, jamais depuis `OBSIA/` : c'est là
que se trouve `AGENTS.md`, et c'est de là que les agents atteignent tes notes.

```bash
cd ..        # depuis OBSIA/, remonter dans le coffre
```

| Harness | Ce qu'il faut faire en plus |
| --- | --- |
| Claude Code | créer `Mon coffre/CLAUDE.md` avec la seule ligne `@OBSIA/CLAUDE.md` (Claude Code lit ce fichier à la place d'`AGENTS.md`) |
| OpenCode | créer `opencode.json` : bloc à copier-coller dans sa fiche |
| Codex | rien. Il lit `AGENTS.md` (limite de taille : un catalogue complet en utilise un peu plus des trois quarts) |
| Goose | garder l'extension `developer` active |
| DeepSeek Harness | rien. Il lit `AGENTS.md` |
| AionUi | faire lire le contrat par la règle de l'assistant (voir sa fiche) |

Chaque harness a sa fiche dans `IA/system/adaptateurs-harness/`. Elle explique
aussi comment brancher les outils (MCP) et où mettre tes clés : **jamais dans
`OBSIA/`**.

## 5. Vérifier qu'OBSIA est bien chargé

Pose ces deux questions à l'agent :

1. « Quels agents connais-tu, et où vivent les notes de connaissance ? »
   Il doit citer les agents d'OBSIA (assistant, administrateur, batisseur…)
   et le dossier `0-SAVOIRS/`.
2. « Que fais-tu si un skill dont tu as besoin est introuvable ? »
   Il doit répondre qu'il te le dit, et non qu'il improvise. C'est la règle
   « Un échec se dit » du contrat.

S'il répond de façon vague, il n'a pas lu ses instructions. Vérifie
qu'`AGENTS.md` existe dans `Mon coffre/` et que tu as bien lancé le harness
depuis ce dossier. Avec Claude Code, vérifie aussi qu'aucun autre `CLAUDE.md`
ne traîne dans un dossier au-dessus du coffre : il passerait en priorité.

## Ensuite

- **Parle à l'agent `assistant`** pour commencer : il range tes notes, tient
  ta mémoire et te dirige vers le bon agent. La liste des agents et leur rôle
  est dans `IA/system/agents-index.md`.
- **Après avoir ajouté ou modifié un skill**, refais `AGENTS.md` sans repasser
  les questions : `python3 scripts/installer.py --rejouer --appliquer` (depuis
  `OBSIA/`).
- **Pour contribuer à OBSIA** : `python3 scripts/verifier_coffre.py` (depuis
  `OBSIA/`) avant de proposer une modification. OBSIA et ton coffre ont chacun leur propre
  historique Git : une modification d'OBSIA se propose par pull request, ta
  mémoire s'enregistre directement.
- **Pour comprendre comment tout fonctionne** : `README.md`, puis le contrat
  (`IA/system/VAULT-CONTRACT.md`).
