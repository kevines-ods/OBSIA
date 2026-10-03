# travail-en-parallele.md — plusieurs agents sur un même dépôt

La procédure derrière le §2.1 de `VAULT-CONTRACT.md`. Le contrat garde les
**règles** ; ce fichier garde les **commandes** et leurs raisons, qui ne
servent qu'au moment de travailler sur une branche (§5 : une information vit à
un seul endroit).

Le principe tient en une phrase : **l'arbre principal est à tout le monde, un
worktree n'est qu'à sa séance.**

## Commencer un travail

Depuis l'arbre principal, sans y changer de branche :

```bash
git fetch origin
git worktree add ~/obsia-worktrees/<nom-agent>-<sujet> -b <nom-agent>/<sujet> origin/main
cd ~/obsia-worktrees/<nom-agent>-<sujet>
```

Jamais sous `/tmp` : un dossier temporaire se vide au redémarrage, et le
worktree part avec lui — ce qui n'est pas commité est perdu.

Tout se fait ensuite dans ce dossier : édition, régénération, vérifications,
commit, poussée. Le crochet de pré-commit y est actif comme ailleurs —
`core.hooksPath` est une configuration du dépôt, partagée par tous ses
worktrees.

Avant de créer un worktree, `git worktree list` dit qui travaille déjà, et sur
quoi. Un worktree ou une branche préfixés du nom d'un autre agent sont à lui :
on ne les modifie pas, on ne les supprime pas, même fusionnés. On le signale.

## Avant de pousser

```bash
git fetch origin
git rebase origin/main
python3 scripts/regenerate_index.py
python3 scripts/verifier_coffre.py
python3 -m unittest discover -s tests
```

Une autre séance a pu fusionner pendant qu'on travaillait. Reprendre la branche
sur la branche par défaut **avant** d'ouvrir la pull request évite de livrer un
conflit à l'utilisateur. Un conflit sur un fichier généré ne se résout jamais à
la main : on prend la version de la branche par défaut, puis on régénère.

## Jamais une PR sur la branche d'une autre PR

Une pull request s'ouvre **toujours sur la branche par défaut**. Si un
travail dépend d'une PR encore ouverte, on attend qu'elle soit fusionnée,
puis on reprend la branche sur `origin/main` et on ouvre la PR. Une PR
ouverte sur la branche d'une autre est fusionnée dans cette branche, et pas
dans `main`, dès que la première est fusionnée avant elle. GitHub ne la
rebascule que si la branche de base est supprimée, et rien ne le signale.
Si l'on empile malgré tout, on vérifie après fusion que le contenu est
dans `origin/main`.

## Publier

`scripts/publier.py` exporte `HEAD`. Dans l'arbre principal, `HEAD` est ce
qu'une autre séance y a laissé ; on publie donc depuis un worktree détaché sur
la branche par défaut distante :

```bash
git fetch origin
git worktree add --detach ~/obsia-worktrees/<nom-agent>-publication origin/main
cd ~/obsia-worktrees/<nom-agent>-publication
python3 scripts/publier.py --cible ~/OBSIA-public   # aperçu
```

## Finir

Une fois la pull request ouverte, le worktree n'a plus d'usage :

```bash
git worktree remove ~/obsia-worktrees/<nom-agent>-<sujet>
```

La branche locale peut rester jusqu'à la fusion ; elle se supprime ensuite.
On ne retire que **ses propres** worktrees.

## Activer la garde sur une machine

Le crochet refuse un commit dans l'arbre principal et un nom de branche sans
préfixe d'agent, mais seulement là où on le demande :

```bash
git config core.hooksPath .githooks          # une fois par clone
git config obsia.arbresSepares true          # sur une machine où travaillent des agents
```

La seconde ligne n'est pas posée par défaut : un clone de la distribution, où
une seule personne travaille, n'a pas à s'imposer des worktrees. Sans elle, le
crochet n'applique que ce qui vaut partout — jamais de commit sur la branche
par défaut.

Contournement ponctuel, en connaissance de cause : `git commit --no-verify`.

## Si un commit a atterri au mauvais endroit

Il se répare **par les références**, sans toucher à l'arbre de travail :

```bash
git branch -f <nom-agent>/<sujet> <commit>     # la branche reprend le commit
git update-ref refs/heads/main origin/main     # la branche par défaut revient
```

Jamais `reset --hard` : le commit est déjà écrit, le déplacer ne coûte rien,
l'effacer coûterait tout.
