---
schema: 1
kind: skill
name: cartographie-du-coffre
description: Dresser la carte des connaissances du coffre parent — concepts de SAVOIRS, notes orphelines, doublons, tags hors vocabulaire, liens manquants. À charger pour faire le point sur la santé du coffre ou avant une réorganisation. Lit et propose, n'écrit rien.
type: outil
read_only: true
---

# Skill — Cartographie du coffre

Inventorie la santé des connaissances du coffre parent : qui est lié à qui,
ce qui est orphelin, ce qui fait doublon, ce qui sort du vocabulaire. Il
**lit et propose** — il n'écrit, ne déplace ni ne supprime rien. Les actions
qui découlent de ses conclusions passent par le skill `traitement-des-notes`
ou par un patch soumis à revue.

La règle d'ensemble est au §7 de `../../system/VAULT-CONTRACT.md`, qui fait foi.

## Périmètre

- Concepts de `../SAVOIRS/` (un fichier = un concept) ;
- croisement avec le vocabulaire contrôlé `../../system/tags-du-coffre-parent.md` ;
- rétroliens et liens Markdown portés par ces notes.

Le dépôt OBSIA étant cloné à la racine du coffre parent, les notes de
connaissance sont un cran au-dessus (`../SAVOIRS/`).

## Ce qu'on détecte

| Constat | Définition | Conséquence |
| --- | --- | --- |
| note **orpheline** | aucune autre note n'y pointe (`[[…]]`) | mal retrouvée : proposer des liens entrants |
| **doublon** probable | deux titres/concepts très proches | proposer la fusion, jamais la faire soi-même |
| **tag hors vocabulaire** | tag de la note absent du registre | signaler : à ajouter au registre ou à retirer |
| **lien manquant** | deux notes du même domaine sans lien mutuel | proposer des rétroliens |
| frontmatter absent/partiel | ni `type` ni `tags` | renvoyer vers `traitement-des-notes` / le passage rétroactif |

## Procédure

1. **Inventorier.** Lister les notes et leurs titres :

   ```bash
   ls ../SAVOIRS/
   ```

2. **Lister les liens et les orphelins.** Une note est orpheline si aucun
   fichier ne contient `[[TitreDeLaNote]]` vers elle. Chercher qui pointe vers
   chaque note :

   ```bash
   rg --glob "*.md" "\[\[cible\]\]" ../SAVOIRS ../PROJETS ../DOCUMENTS
   ```

3. **Repérer les doublons.** Normaliser les titres (minuscules, sans accents
   ni ponctuation) et rapprocher ceux qui se ressemblent — juger ensuite, ne
   jamais trancher seul.

4. **Contrôler les tags.** Pour chaque note, comparer ses tags au registre
   `../../system/tags-du-coffre-parent.md` ; lister ceux qui en sortent.

5. **Proposer les liens manquants.** À partir de la carte et des domaines de
   tags, suggérer les rétroliens qui relieraient des notes du même domaine.

## Sortie

Un rapport en langage clair, en quatre sections : notes orphelines, doublons
probables, tags hors vocabulaire, liens manquants proposés — avec, pour chaque
point, le chemin de la note. Rien n'est modifié.

## Garde-fous

- `read_only: true` : aucune écriture, aucun déplacement, aucune suppression.
- Ne pas recopier le contenu du coffre parent dans le rapport : il est privé,
  le dépôt est public (§4). On rapporte des **noms de notes et des constats**,
  pas des extraits.
- Une proposition n'est jamais une action : l'application passe par
  `traitement-des-notes` (zones du §7.3) ou par une demande à l'utilisateur.
