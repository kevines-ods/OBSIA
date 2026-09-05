# taches-index.md — Index des tâches planifiées

| Tâche | Quand | Fuseau | Mode | Agent | Active | Description |
|---|---|---|---|---|---|---|
| [revue-hebdomadaire-du-coffre](../tâches/revue-hebdomadaire-du-coffre.md) | `0 9 * * 1` | Europe/Paris | agent | assistant | oui | Régénérer index et sommaires, vérifier la cohérence du coffre, et réconcilier le registre des tâches avec ce qui tourne réellement. |

> Le registre `IA/tâches/` **déclare** ; rien ne s'instancie tout seul.
> Une tâche listée ici n'est pas forcément planifiée sur la machine
> courante : charger le skill `cron` pour instancier ou réconcilier
> (cf. `VAULT-CONTRACT.md` §12).

> Fichier **généré** par `scripts/regenerate_index.py` depuis les
> frontmatters, qui font foi. Ne pas éditer à la main (§11).
