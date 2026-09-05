# Un état qui ne vit que chez l'exécutant est perdu

Leçon générale, tirée du cas des tâches planifiées. Vaut pour toute
configuration qu'un agent installe hors du dépôt.

## Statut
🟢 Vérifiée — un skill agissait depuis des semaines sans laisser de trace.

---

## Le constat

Le skill `cron` créait des timers systemd dans `~/.config/systemd/user/` et
n'écrivait rien dans le coffre. Conséquences, toutes silencieuses :

- changer de machine ou réinstaller le système effaçait les tâches sans que
  rien ne signale ce qui manquait ;
- changer de harness laissait les timers en place mais appelait un programme
  disparu ;
- personne ne pouvait répondre à « qu'est-ce qui est censé tourner ? » sans
  interroger la machine — et seulement celle qui était allumée.

## La leçon

C'est le miroir de [[index-maintenus-a-la-main]] : là, une information dérivée
était saisie à la main ; ici, une information **de référence** n'était nulle
part. Même effet, dérive invisible.

La règle qui en sort : **ce qu'un agent installe hors du dépôt doit être
déclaré dans le dépôt.** Trois conditions pour que la déclaration serve :

| Condition | Sans elle |
| --- | --- |
| une **déclaration versionnée** de l'intention | la migration perd tout |
| une **clé de nommage** partagée (`obsia-<nom>`) | on ne sait pas rapprocher déclaration et instance |
| une **procédure de réconciliation** | l'écart se creuse sans qu'on le voie |

La déclaration ne porte que l'intention, jamais l'état : un identifiant
d'instance ou un nom de machine vieillit, et le dépôt est public.

## Portée

Vaut au-delà des tâches planifiées — tout ce qu'un agent laisse sur un système
et qui devra être retrouvé plus tard : unités systemd, entrées de proxy,
montages, règles de sauvegarde. Poser la question avant d'agir : *si cette
machine disparaît demain, qu'est-ce que le coffre sait encore ?*
