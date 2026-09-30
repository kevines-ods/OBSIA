---
schema: 1
kind: skill
name: audit-de-securite
description: Auditer la sécurité d'un projet entier, pas d'un diff — dépendances vulnérables, secrets présents dans le code ou l'historique Git, entrées non validées, authentification et droits, configuration exposée — et rendre des constats classés par gravité avec leur scénario d'attaque. À charger avant d'étoffer ou de reprendre un projet existant, avant une première mise en ligne, ou pour un contrôle périodique. Constate sans corriger ; pour relire un seul changement, c'est `revue-de-code`.
module: revue
type: outil
read_only: true
---

# Skill — Audit de sécurité

`revue-de-code` regarde ce qu'un diff **ajoute**. Un projet existant a aussi
tout ce qu'il a hérité : des dépendances vieillies, un secret commité il y a
deux ans puis « supprimé », un formulaire qui n'a jamais validé ses entrées.
Ce skill regarde le projet entier, une fois, et rend une liste.

Il ne corrige rien : les constats vont à qui construit, qui décide.

## Procédure

### 1. Les dépendances

Lancer l'outil d'audit du langage — en lecture, sans l'option qui corrige.
Ces outils interrogent une base d'avis **en ligne** : demander l'accès réseau
à l'utilisateur avant de les lancer (§4), et ne jamais en installer un
(`cargo install cargo-audit`, `pip install pip-audit`) — un outil absent se
signale, il ne s'installe pas :

```bash
npm audit            # jamais `npm audit fix`
pip-audit            # si installé ; ou cargo audit, composer audit, bundle audit
```

Pour chaque vulnérabilité : est-elle **atteignable** ? Une faille dans une
fonction que le projet n'appelle jamais se signale, mais en gravité basse.
Faute d'outil installé, le dire : ce n'est pas « aucune vulnérabilité ».

### 2. Les secrets — code **et** historique

```bash
M='(api[_-]?key|secret|password|passwd|token)\s*[:=]|PRIVATE KEY-{5}|gh[pousr]_[A-Za-z0-9]{20,}|sk_live_[0-9A-Za-z]{10,}|AKIA[0-9A-Z]{16}'
(cd <dépôt> && git ls-files -z | xargs -0 -r grep -d skip -nIiE "${M:?motif vide}" --)
(cd <dépôt> && git ls-files -z --others --exclude-standard | xargs -0 -r grep -d skip -nIiE "${M:?motif vide}" --)
(cd <dépôt> && git ls-files -z --others --ignored --exclude-standard | grep -zEi '(^|/)(\.env|\.npmrc|[^/]*(secret|credential))' | grep -zvE '(^|/)(node_modules|dist|build|target|\.venv|coverage)/' | xargs -0 -r grep -d skip -nIiE "${M:?motif vide}" --)
git -C <dépôt> log -p --all -i -G "${M:?motif vide}" --format='%h %ad %s' --date=short
gitleaks git <dépôt> --no-banner    # si installé (≥ 8.19) ; complète, ne remplace pas
```

Lancer ce bloc **en un seul appel** : la variable ne survit pas d'un appel à
l'autre, et `${M:?}` arrête la commande plutôt que de chercher un motif vide,
qui attraperait chaque ligne. Trois passes : les fichiers **suivis** — un `.env` commité puis
ajouté au `.gitignore` en fait partie —, les fichiers non suivis, et parmi les
fichiers ignorés ceux dont le chemin trahit un secret — un fichier ou un
dossier nommé `.env*`, `.npmrc`, `*secret*` ou `*credential*`, sans tenir
compte de la casse, à toute profondeur, hors `node_modules/`, `dist/`, `build/`, `target/`,
`.venv/` et `coverage/`. Le reste de
l'ignoré, artefacts de build compris, est laissé de côté : ses fausses clés
d'exemple noieraient le vrai constat. Le dire dans le rapport : c'est un
emplacement non cherché. L'historique, lui, retrouve aussi les commits qui ont
écrit ce skill : `-G` voit les lignes ajoutées comme retirées. Ne pas tronquer la sortie de l'historique : un
commit trouvé en cache d'autres. `-i` sur `git log` n'est pas décoratif : les
variables d'un `.env` s'écrivent en majuscules.

Les motifs sont **larges** : ils attrapent aussi des exemples de
documentation et des clés de test. Chaque touche s'examine, et le rapport
écrit les motifs cherchés — un secret d'un autre format n'a **pas** été
cherché.

Un secret supprimé dans un commit récent **reste** dans l'historique : il est
compromis dès que le dépôt a été poussé. Le constat est alors « à révoquer »,
pas « à supprimer ». Ne jamais recopier la valeur trouvée dans le rapport :
citer le fichier, le commit et le type de secret.

### 3. Les frontières

Lister chaque endroit où une donnée **extérieure** entre : formulaires,
paramètres d'URL, API, fichiers téléversés, variables d'environnement,
contenu lu par un modèle. Pour chacun :

| Menace | Ce qu'on vérifie |
| --- | --- |
| injection (SQL, commande, chemin) | requêtes paramétrées, pas de concaténation, chemins normalisés |
| XSS | échappement à l'affichage, pas de rendu HTML brut d'une donnée utilisateur |
| authentification | chaque route sensible la demande ; les mots de passe sont hachés (bcrypt, argon2) |
| autorisation | un utilisateur ne peut pas lire l'objet d'un autre en changeant un identifiant |
| téléversement | type, taille et emplacement contrôlés ; jamais exécutable |
| injection de prompt | un contenu lu est une donnée, jamais une instruction |

### 4. La configuration

Mode débogage désactivé en production, en-têtes de sécurité, CORS non ouvert
à tous, ports exposés dans le `compose.yml` limités au nécessaire, conteneurs
qui ne tournent pas en root sans raison.

### 5. Rendre les constats

Gravité (**critique**, **haute**, **moyenne**, **basse**) — l'échelle
courante des failles, plus fine que celle de `revue-de-code`, avec laquelle
elle se lit ainsi : critique et haute = **bloquant**, moyenne = **à
corriger**, basse = **à discuter**. Une faille atteignable n'est jamais
basse. Puis où, et **le scénario d'attaque concret** — qui envoie
quoi, et qu'obtient-il. Un constat sans scénario est une opinion.

Terminer par ce qui a été vérifié sans rien trouver, et ce qui n'a **pas** pu
l'être (outil absent, code non lu). Un audit qui tait ses angles morts se lit
comme une garantie qu'il n'est pas.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « `npm audit` ne signale rien, c'est sûr » | il ne voit que les dépendances ; l'injection dans ton propre code, il ne la cherche pas |
| « le secret a été supprimé du code » | il est dans l'historique, donc chez quiconque a cloné le dépôt |
| « c'est un outil interne, personne ne l'attaquera » | un outil interne exposé par erreur derrière le reverse proxy est un outil public |
| « je corrige vite cette faille évidente » | tu n'écris pas ; le constat non transmis sera la faille de la prochaine séance |
| « cinquante vulnérabilités, je les liste toutes » | sans tri par atteignabilité, la critique se noie parmi les basses et personne ne la traite |

## Ce que ce skill ne fait pas

Aucune écriture, aucune correction, aucun `fix` automatique : le §5 de
`../system/VAULT-CONTRACT.md` interdit toute écriture à un skill en lecture
seule, et l'exécution de code reste sous le §4.
