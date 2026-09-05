---
schema: 1
kind: tâche
name: revue-hebdomadaire-du-coffre
description: Régénérer index et sommaires, vérifier la cohérence du coffre, et réconcilier le registre des tâches avec ce qui tourne réellement.
mode: agent
quand: "0 9 * * 1"
fuseau: Europe/Paris
exécutant: local
agent: assistant
actif: true
---

# Tâche — Revue hebdomadaire du coffre

## Intention

Les fichiers générés du §11 se périment en silence, et une tâche instanciée sur
une machine puis oubliée devient invisible. Un passage hebdomadaire remet les
deux en cohérence tant que l'écart est petit.

`exécutant: local` parce qu'elle a besoin d'un clone du coffre sous la main :
un planificateur distant n'aurait rien à régénérer.

C'est aussi la tâche de référence du registre : celle sur laquelle vérifier que
la chaîne déclaration → instanciation → réconciliation fonctionne.

## Instruction

Place-toi à la racine du coffre OBSIA et exécute, dans cet ordre :

```bash
python3 scripts/regenerate_sommaire.py
python3 scripts/regenerate_index.py
python3 scripts/verifier_coffre.py
```

Charge ensuite le skill `cron` (`IA/skills/cron.md`) et applique sa section
« Réconcilier » entre `IA/tâches/` et les tâches réellement planifiées sur
cette machine.

Rapporte en clair, en trois points : les fichiers régénérés, les erreurs et
avertissements du vérificateur, les écarts de réconciliation.

Ne corrige rien de toi-même. Si un fichier généré a changé ou si le
vérificateur sort en erreur, prépare un patch et soumets-le — `IA/` passe par
revue (§2).
