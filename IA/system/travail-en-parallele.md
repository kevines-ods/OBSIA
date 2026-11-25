# travail-en-parallele.md — plusieurs agents sur un même dépôt

La procédure derrière le §2.1 de `VAULT-CONTRACT.md`. Le contrat garde les
**règles** ; ce fichier garde les **commandes** et leurs raisons, qui ne
servent qu'au moment de travailler sur une branche (§5 : une information vit à
un seul endroit).

Le principe tient en une phrase : **l'arbre principal est à tout le monde, un
worktree n'est qu'à sa séance et à son chantier.** Autrement dit : **un chantier,
un worktree** — deux chantiers ne partagent jamais le même dossier, même menés le
même jour par le même agent.

## Commencer un travail

Depuis l'arbre principal, sans y changer de branche :

```bash
git fetch origin
git worktree add ~/obsia-worktrees/<nom-agent>-<sujet> -b <nom-agent>/<sujet> origin/main
cd ~/obsia-worktrees/<nom-agent>-<sujet>
```

Jamais sous `/tmp` : un dossier temporaire se vide au redémarrage, et le
worktree part avec lui — ce qui n'est pas commité est perdu.

**Une seule racine, `~/obsia-worktrees/`, pour tous les dépôts** — produit,
interface, dépôt extérieur —, à plat : `~/obsia-worktrees/<nom-agent>-<sujet>`.
Ni un dossier par dépôt, ni un dossier caché dans le coffre : c'est le seul
dossier qu'une interface ouvre à l'écriture d'un agent (le préfixe
`<nom-agent>-` dit à qui il est), et le seul que `ranger_worktrees.py` signale
comme rangé.

Un **nouveau chantier** ouvre une branche **et** un worktree neufs : le worktree
d'un chantier précédent ne se réutilise jamais, même pour un sujet voisin. Dans
les commandes ci-dessus, `<sujet>` nomme donc le **chantier**, pas la séance, et
le dossier ne sert qu'à lui — de son ouverture jusqu'à la fusion de sa pull
request (§« Finir »).
On repart de `origin/main`, sinon la branche hérite du travail inachevé du chantier
d'avant.

**Est un nouveau chantier** toute demande qui ouvre ou change le dossier
`0-PROJETS/<projet>/<chantier>/` — son carnet et son résumé (§6). Un nom de
chantier différent = un worktree différent, sans exception. **Dans le doute,
c'est un nouveau chantier** ; et si le doute persiste, le demander avant de
réutiliser un worktree. Une **séance sans chantier** (§6) qui touche le dépôt
ouvre elle aussi son propre worktree, nommé d'après le sujet du jour — jamais celui d'un chantier
précédent.

Tout se fait ensuite dans ce dossier : édition, régénération, vérifications,
commit, poussée. Le crochet de pré-commit y est actif comme ailleurs —
`core.hooksPath` est une configuration du dépôt, partagée par tous ses
worktrees.

Avant de créer un worktree, `git worktree list` dit qui travaille déjà, et sur
quoi. Un worktree ou une branche préfixés du nom d'un autre agent sont à lui :
on ne les modifie pas, on ne les supprime pas. On le signale. Seule exception :
un worktree **fusionné et propre** n'est plus un travail ; n'importe quel agent
le retire, avec sa branche locale, par `ranger_worktrees.py` et par lui seul —
jamais par un `git worktree remove` à la main (§« Finir »).

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

Le worktree sert jusqu'à la **fusion** : les corrections de relecture s'y
font. Une fois la pull request fusionnée, il n'a plus d'usage. Le ménage se
fait pour tous d'un coup, **depuis l'arbre principal du dépôt produit**, les
autres dépôts touchés (interface, dépôt extérieur) passés en argument :

```bash
git -C <depot> fetch --prune origin                          # pour chaque dépôt
python3 scripts/ranger_worktrees.py . <depot> ...            # aperçu
python3 scripts/ranger_worktrees.py . <depot> ... --appliquer
```

Il ne retire un worktree que si sa branche est celle d'un agent, porte au moins
un commit à elle, descend de la branche par défaut distante, et si le dossier
est propre (ni modification, ni fichier non suivi, ni fichier ignoré hors des
caches qui se refont), non verrouillé et sans activité depuis une heure — puis
sa branche locale, si elle pointe encore sur la tête jugée fusionnée. Un
worktree **neuf**, encore vide sur `origin/main`, reste donc en place, comme une
tête détachée (publication, rebase en cours). Il ne force jamais, et dit chaque refus de git. Une branche
abandonnée sans fusion (PR fermée) ne passe pas par lui : elle se retire à la
main, par son agent ou sur accord de l'utilisateur.

Côté distant, la branche d'une PR fusionnée se supprime d'elle-même si le dépôt
l'a réglé (`delete_branch_on_merge` sur GitHub) ; à régler sur chaque dépôt où
travaillent des agents.

## Les dépôts extérieurs

Le §2.1 vaut pour le dépôt produit ; le §3 du contrat l'étend à tout dépôt
extérieur sur lequel un agent `read_only: false` travaille : **l'arbre
principal d'un dépôt extérieur reste sur sa branche par défaut — il ne fait
que s'y mettre à jour ; tout travail se fait dans un worktree lié.** Un clone
de déploiement appartient au service qui le lit : une séance qui y change de
branche, même « juste pour un essai », fait tourner ce service sur une
branche de travail non relue — l'incident du 2026-11-16, où l'arbre de
déploiement d'une interface s'est retrouvé sur la branche d'une séance.

Deux objets, deux gestes — un dépôt extérieur se regarde d'abord sous
l'un ou l'autre :

- le **dépôt de contribution**, où la séance apporte un changement : worktree
  lié, branche `<agent>/<sujet>`, pull request — les commandes du § «
  Commencer un travail » ci-dessous ;
- le **clone de déploiement**, que lit un service (ex. le garde-fou du
  lanceur d'une interface) : il n'ouvre jamais de worktree de travail ni de
  branche — seules y passent `fetch` puis `pull --ff-only`, et le service
  relancé ensuite ; si le déploiement exige un changement, il se fait
  **ailleurs**, dans le dépôt de contribution, et le clone le suit par sa
  mise à jour.

Mise à jour de l'arbre principal, sans en changer la branche :

```bash
git -C <depot> fetch origin
git -C <depot> pull --ff-only
```

Tout travail y ouvre un worktree, les commandes du § « Commencer un travail »
ci-dessus, depuis le dépôt extérieur : worktree hors `/tmp`, un chantier une
branche, PR sur la branche par défaut du dépôt visé.

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
