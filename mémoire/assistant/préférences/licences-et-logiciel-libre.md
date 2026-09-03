# Licences et logiciel libre

Préférence structurante, à appliquer sans redemander confirmation.

## Statut
🟢 Établie — vérifiée par trois décisions déjà prises dans le coffre.

---

## La règle

**Outils libres exclusivement.** Vérifier la licence de tout skill, script ou
dépendance avant de l'intégrer. Une licence incompatible avec l'AGPL n'entre
pas dans le coffre.

OBSIA est sous **AGPL-3.0-or-later**. Le copyleft est délibéré : un dérivé
reste libre, y compris s'il n'est jamais distribué mais seulement exposé à
travers un réseau (§13 de la licence).

## Évidence — trois refus déjà actés

- `IA/skills/bureautique.md` écarte `officecli` : binaire propriétaire, sans
  sources publiées, installé par `curl … | bash` depuis un domaine tiers.
  Remplacé par `python-docx`, `openpyxl`, `python-pptx` et LibreOffice.
- `IA/skills/pdf.md` a été **réécrit à neuf** plutôt que traduit : le skill
  d'origine était sous licence propriétaire et ne pouvait pas être republié
  dans un dépôt public, même traduit.
- `IA/skills/cron.md` a abandonné un binaire propre à une autre application au
  profit des timers systemd utilisateur, natifs et sans droits root.

## Interprétation

Le motif récurrent n'est pas « éviter le propriétaire par principe » mais
**garder le coffre auditable et reproductible** : un binaire sans sources ne
peut être ni vérifié, ni corrigé, ni porté. Les trois substitutions ci-dessus
ont chacune coûté du travail et ont chacune été faites quand même.

Corollaire à retenir : lors d'un import depuis un catalogue de skills, la
licence se vérifie **avant** la traduction, pas après.
