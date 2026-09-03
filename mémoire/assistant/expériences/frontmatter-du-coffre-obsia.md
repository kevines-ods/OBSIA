# Frontmatter du coffre — pièges vérifiés

Leçon réutilisable sur le lecteur de frontmatter d'OBSIA. À relire avant de
toucher au frontmatter d'un agent ou d'un skill.

## Statut
🟢 Vérifiée le 2026-09-03 sur un coffre jetable.

---

## Le piège principal : le scalaire replié

`description: >` suivi de lignes indentées **ne fonctionne pas**. La
description prend pour valeur le caractère `>` lui-même.

```yaml
description: >
  Ligne un.
  Ligne deux.
```

produit dans le prompt système :

```
- **plie** [lecture seule] — >
```

**Cause.** `lire_frontmatter()` de `scripts/generer_prompt.py` est un analyseur
minimal, pas un parseur YAML : il fait `cle, _, valeur = nu.partition(":")` et
stocke `valeur` telle quelle. Les lignes de continuation, dépourvues de `:`,
tombent dans `if ":" not in nu: continue` et sont perdues.

**Règle.** Une `description` tient sur **une seule ligne physique**, quelle que
soit sa longueur. Celles du coffre font entre 233 et 301 caractères. Les
virgules, tirets cadratins et deux-points passent sans dommage — testés.

## Autres formes que l'analyseur ne gère pas

Il couvre les scalaires simples et les listes à tirets, rien d'autre. Donc pas
de listes en ligne (`skills: [a, b]`), pas de guillemets multi-lignes, pas
d'ancres YAML.

Le piège déjà documenté dans le README reste valable : `skills: a, b` vaut une
**chaîne de caractères**, pas une liste — et rien ne le signalait jusqu'à
l'ajout de `scripts/verifier_coffre.py`.

## Comment tester sans risque

Monter un faux coffre et pointer le générateur dessus :

```bash
mkdir -p /tmp/essai/IA/agents /tmp/essai/IA/skills
# y déposer un skill de test, puis :
python3 scripts/generer_prompt.py --racine /tmp/essai
```

L'option `--racine` sert exactement à ça : vérifier une hypothèse sur le
format sans toucher au coffre réel.
