# 2026-08-26 — Automatisation des tâches bureautiques

Faire exécuter à `assistant` des tâches bureautiques récurrentes — documents,
tableurs, présentations — déclenchées à heure fixe.

## Statut
🟡 En attente — piste ouverte, aucune tâche planifiée à ce jour.

---

## Décisions

- La compétence bureautique est portée par le skill **`bureautique`**, qui
  s'appuie sur `python-docx`, `openpyxl`, `python-pptx` et LibreOffice — tous
  libres.
- Le déclenchement à heure fixe passe par le skill **`cron`**, c'est-à-dire des
  timers systemd utilisateur, sans droits root.
- Un seul agent est concerné : **`assistant`**. Le coffre ne compte pas d'autre
  agent, et n'en nomme aucun (`VAULT-CONTRACT.md` §1).

## Évidence

Cette note citait à l'origine le skill `officecli` et un second agent, nommé.
Ni l'un ni l'autre n'existe :

- `officecli` a été **écarté** — binaire propriétaire sans sources publiées,
  installé par `curl … | bash`. Le motif du refus et son remplacement sont
  consignés dans `IA/skills/bureautique.md` et dans
  [[licences-et-logiciel-libre]].
- L'agent nommé n'a jamais eu de fichier dans `IA/agents/`. C'est exactement
  le mécanisme décrit au §1 du contrat : un nom cité finit par passer pour une
  existence.

Corrigé le 2026-09-04, à la suite d'un audit de cohérence du coffre.

## Interprétation

Toute exécution de code reste en sandbox (`VAULT-CONTRACT.md` §4). Une tâche
planifiée est une action différée : le preview du §2 s'applique avant sa
création, et `cron` impose de lister l'existant avant d'ajouter quoi que ce
soit.

## Questions ouvertes

- [ ] Quelles tâches bureautiques méritent réellement d'être planifiées ?
      Aucune n'est identifiée à ce jour — la piste est ouverte, pas engagée.

## URLs sources

- (aucune — note interne)
