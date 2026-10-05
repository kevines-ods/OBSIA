---
schema: 1
kind: skill
name: controle-de-cap
description: Vérifier qu'un plan, une décision, un choix technique ou un changement va dans le sens de la finalité du projet — relire la note `— vision`, puis rendre pour chaque objet un verdict rapproche, neutre, éloigne ou ferme une porte, avec le scénario qui le justifie. À charger à chaque moment clé d'un projet où le visionnaire est consulté. Ne juge pas la qualité d'un changement, seulement sa direction.
module: noyau
type: outil
read_only: true
---

# Skill — Contrôle de cap

## Procédure

1. **Relire la note** `<projet> — vision.md`, à la racine du dossier du
   projet (§7.3) — celle du grand projet pour un chantier. Si
   elle manque, s'arrêter et charger `extrapolation-des-finalites`.
2. **Isoler l'objet.** Demander ce qui est présenté — un plan, une stack, un
   diff, une décision — et le lire **sans** le raisonnement qui y a mené.
   Un objet résumé par celui qui l'a produit arrive déjà jugé.
3. **Rendre un verdict par objet**, jamais un verdict global :

   | Verdict | Quand |
   | --- | --- |
   | **rapproche** | la finalité déclarée est plus proche après qu'avant |
   | **neutre** | ni l'un ni l'autre — la plupart des changements le sont, et c'est normal |
   | **éloigne** | du travail part vers une finalité rejetée, ou vers aucune |
   | **ferme une porte** | une porte à garder ouverte devient impossible ou coûteuse à rouvrir |

4. **Justifier par un scénario.** « Dans six mois, si <finalité> se réalise,
   ce choix oblige à <conséquence> ». Sans scénario concret, ne pas rendre le
   verdict.
5. **Pour « ferme une porte », chiffrer l'alternative.** Ce que coûterait de
   la garder ouverte. Si ce coût dépasse celui de la tranche, le dire : c'est
   à l'utilisateur de choisir entre la porte et le coût, pas au visionnaire.
6. **Signaler une vision périmée.** Si l'objet montre que la finalité a
   changé, ne pas juger contre l'ancienne : proposer une révision.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « tout est neutre, rien à signaler » | possible, et c'est un résultat ; mais dire ce qu'on a confronté à quelles portes, sinon personne ne sait si on a regardé |
| « ce code est mal écrit, je le signale aussi » | le verdict de qualité noie celui de direction ; c'est le rôle du `contradicteur` |
| « ça ferme une porte, il faut refuser » | le visionnaire ne refuse rien ; il chiffre ce que la porte coûte et rend la main |
| « je vois bien où il veut aller, j'adapte la vision en passant » | une vision qui suit le travail ne juge plus rien ; la révision passe par l'utilisateur |
