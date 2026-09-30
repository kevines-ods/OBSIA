---
schema: 1
kind: skill
name: migration-de-donnees
description: Faire évoluer le schéma d'une base de données ou le format de fichiers d'un projet existant sans perdre de données — sauvegarde vérifiée d'abord, migration versionnée et réversible, répétée sur une copie avant la vraie, contrôle des comptes après. À charger dès qu'une évolution touche une table, une colonne, un index ou un format de données déjà en usage. N'applique jamais une migration sur des données réelles sans sauvegarde restaurable.
module: construction
type: outil
read_only: false
---

# Skill — Migration de données

Le code se corrige par un nouveau commit. Des données perdues ne se corrigent
pas. Une migration est donc la seule étape d'une évolution où l'on prépare le
retour **avant** l'aller.

## Procédure

### 1. Sauvegarder, et le prouver

Charger `sauvegardes`. Une sauvegarde compte quand elle a été **restaurée**
sur une copie, pas quand le fichier existe. Noter son emplacement et sa date
dans la PR.

### 2. Écrire la migration versionnée

Avec l'outil du projet (Alembic, Django migrations, Prisma, Flyway,
`knex`…), jamais à la main dans une console. Chaque migration a :

- un **aller** et un **retour** (`upgrade`/`downgrade`, `up`/`down`) ;
- un nom qui dit ce qu'elle fait : `ajout_colonne_code_promo`.

Quand le retour est impossible (suppression d'une colonne pleine, conversion
avec perte), l'écrire en toutes lettres dans la migration et dans la PR : ce
n'est plus une migration réversible, c'est une opération irréversible, et le
retour passe par la sauvegarde.

### 3. Découper les changements dangereux

Un renommage ou une suppression se fait en **plusieurs livraisons**, pour que
l'ancienne et la nouvelle version du code tournent sur le même schéma :

1. ajouter la nouvelle colonne ; le code écrit dans les deux ;
2. recopier l'existant ; le code lit la nouvelle ;
3. supprimer l'ancienne, une fois la précédente livraison éprouvée.

Chaque étape est une tranche et une PR.

### 4. Répéter sur une copie

Restaurer la sauvegarde dans une base jetable, y jouer l'aller, **puis le
retour, puis l'aller** encore. Mesurer la durée : une migration de dix
minutes sur une table verrouillée est une interruption de service à annoncer.

### 5. Contrôler après

Avant et après, compter ce qui doit se conserver :

```sql
SELECT count(*) FROM commandes;                -- même nombre avant et après
SELECT count(*) FROM commandes WHERE total IS NULL;  -- aucune valeur perdue
```

Des comptes qui diffèrent arrêtent tout : on revient en arrière, on ne
« corrige » pas à chaud.

### 6. Appliquer pour de vrai

Seulement après accord explicite de l'utilisateur, avec la sauvegarde du jour
et la commande de retour sous les yeux. Si la migration part avec une mise en
ligne, l'ordre est : sauvegarde (celle de `mise-en-ligne`), migration jouée
et comptes contrôlés, **puis** déploiement du nouveau code, puis vérification.
Le retour arrière de `mise-en-ligne` ne couvre que le code : écrire à côté la
commande de retour de la migration.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « la sauvegarde de cette nuit suffit » | tant qu'elle n'a pas été restaurée, tu ne sais pas si elle contient la table |
| « le `downgrade` ne servira jamais » | il sert le jour où la migration est déjà en production et que le code qui l'accompagne plante |
| « c'est un simple renommage de colonne » | l'ancien code qui tourne encore pendant le déploiement lit une colonne qui n'existe plus |
| « je l'ai testée sur ma base de développement vide » | dix lignes de test ne révèlent ni la durée ni les valeurs nulles de cent mille lignes réelles |
| « un petit `UPDATE` à la main pour rattraper » | il n'est ni versionné ni rejouable, et la prochaine installation n'aura pas ces données |

## Ce que ce skill ne fait pas

Il ne restaure jamais par-dessus l'original et ne supprime aucune
sauvegarde — ce sont les règles de `sauvegardes`. Le travail sur le dépôt
suit le §3 de `../system/VAULT-CONTRACT.md`.
