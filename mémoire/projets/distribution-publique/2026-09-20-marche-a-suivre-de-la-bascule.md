# 2026-09-20 — La marche à suivre pour séparer l'atelier de la distribution

Le catalogue de modules et les deux scripts sont fusionnés dans `main`. Reste
le geste qui n'est pas automatisable : couper le dépôt en deux sur GitHub.
Cette note est le mode d'emploi, écrite pour être relue froid, un jour où le
contexte de la séance aura disparu.

## Statut

🟡 Écrite, jamais exécutée. Les étapes 1 à 9 n'ont pas encore été jouées ; la
première exécution dira ce qui manque ici.

---

## Le point de départ

Un seul dépôt, `kevines-ods/OBSIA`, public depuis le 2026-08-29. Il porte tout :
le catalogue, la mémoire, les logs de session.

## Ce qu'on veut obtenir

| | Nom GitHub | Visibilité | Rôle |
| --- | --- | --- | --- |
| l'atelier | `OBSIA-atelier` | privé | on y travaille, il fait foi |
| la distribution | `OBSIA` | public | dérivé par `publier.py` |

**C'est le public qui garde le nom `OBSIA`.** Il est la vitrine : c'est lui
qu'on trouve, qu'on clone, qu'on cite. Le nom de l'atelier, personne ne le voit.

GitHub interdit deux dépôts homonymes chez un même propriétaire : l'un des deux
doit changer de nom, et ce choix-là est le bon.

## Les neuf étapes, dans l'ordre

1. **Fusionner tout ce qui est en cours.** Une bascule sur un dépôt qui a des
   branches en vol se paie.
2. **Récupérer la fusion en local** — `git checkout main && git pull origin main`
   depuis la racine du dépôt.
3. **Renommer sur GitHub** : Settings → *Repository name* → `OBSIA-atelier`.
4. **Passer en privé** : Settings → *Danger Zone* → *Change repository
   visibility* → Private.
5. **Corriger l'adresse distante en local** :
   `git remote set-url origin https://github.com/kevines-ods/OBSIA-atelier.git`,
   puis `git remote -v` pour vérifier.
6. **Créer le dépôt public, vide** — nom `OBSIA`, Public, **aucune case
   cochée** : ni README, ni .gitignore, ni licence.
7. **Cloner ce dépôt vide, hors du coffre Obsidian** — `~/OBSIA-public` par
   exemple. Git avertit qu'il a cloné un dépôt vide : c'est normal.
8. **Publier** — l'aperçu d'abord, qui n'écrit rien, puis l'exécution.
9. **Pousser** depuis le clone public. `publier.py` ne pousse jamais.

Les commandes exactes des étapes 8 et 9 vivent dans le README, section
« Public et privé » : les recopier ici les ferait diverger (§5).

## Les quatre pièges

- **Le remote se corrige avant de créer le nouveau dépôt** (étape 5 avant 6).
  GitHub redirige l'ancienne URL après un renommage, mais cette redirection
  **s'éteint dès qu'un nouveau dépôt prend le nom libéré**. Sans l'étape 5, on
  pousse un jour dans le public en croyant pousser dans l'atelier.

- **Le clone public ne va jamais dans le coffre Obsidian.** Il porterait un
  second exemplaire de chaque note, et la règle d'unicité des noms (§6)
  tomberait sur l'ensemble du coffre. `~/OBSIA-public`, ou n'importe où
  ailleurs.

- **Le nom du dossier local ne change pas.** Le dépôt distant s'appelle
  `OBSIA-atelier`, le dossier reste `OBSIA/` dans le coffre. Ce sont deux
  choses indépendantes, et rien dans le contrat ne casse.

- **Basculer en privé ne dépublie pas le passé.** Le §13.5 le dit : ce qui a
  été servi reste chez qui l'a cloné, et la mémoire figure dans l'historique
  public depuis fin août. Le dépôt public à créer, lui, part propre —
  `publier.py` écrit dans un clone neuf sans y verser l'historique de
  l'atelier.

## Les fois suivantes

Rien à recréer. On travaille dans l'atelier, et quand une fonctionnalité est
mûre, on rejoue `publier.py` puis on pousse depuis le clone public. C'est la
fenêtre de validation du §13.5 : rien ne franchit la frontière sans commande
explicite.

## Ce qui reste ouvert

- Le nom `OBSIA-atelier` n'est qu'une proposition ; `OBSIA-prive` ou
  `coffre-obsia` feraient l'affaire. Ce qui compte est que le public garde
  `OBSIA`.
- `publier.py` n'a jamais tourné contre un vrai dépôt public. La première
  exécution dira si le contrôle de fuite crie trop, ou pas assez.
