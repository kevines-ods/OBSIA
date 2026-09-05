# 2026-09-05 — Registre des tâches planifiées

Les tâches récurrentes n'existaient que sous forme de timers systemd, hors du
coffre : changer de harness ou de machine les perdait sans que rien ne le
signale. Elles sont désormais déclarées dans `IA/tâches/`, qui fait foi.

## Statut
🟢 Livré — registre, contrat §12, skill `cron` réécrit, contrôles en CI.

## Décisions

- **Le registre est la source de vérité, l'instance est jetable.** Un fichier
  `IA/tâches/<nom>.md` déclare l'intention ; le timer systemd ou le
  planificateur du harness n'en est qu'une instance, recréable.
- **Clé de rapprochement : `obsia-<name>`.** Toute instance porte ce nom, quel
  que soit l'exécutant. Sans convention de nommage, aucune réconciliation
  n'est possible : on ne sait pas dire quel timer correspond à quelle
  déclaration.
- **Le registre déclare une intention, jamais un état.** Ni identifiant
  d'instance, ni nom de machine, ni date de dernier déclenchement : ça
  vieillit mal, et le dépôt est public. L'état se lit chez l'exécutant.
- **`quand` s'écrit en cron à 5 champs, entre guillemets.** C'est la notation
  que tous les exécutants comprennent ou savent traduire. Les guillemets ne
  sont pas décoratifs : `*/15 * * * *` non quoté est une ancre YAML invalide,
  qu'aucun lecteur YAML réel n'accepte — le lecteur maison du coffre, lui, la
  laisse passer, d'où le contrôle explicite.
- **Deux modes.** `commande` (shell, aucun modèle) tourne partout et survit à
  tout ; `agent` a besoin d'un harness. La distinction dit d'avance ce qu'un
  changement d'outillage met en danger.
- **`IA/tâches/` n'est pas une zone d'écriture directe** : créer ou modifier
  une tâche passe par patch, comme le reste de `IA/`.

## Évidence

- `IA/skills/cron.md` d'avant écrivait directement dans
  `~/.config/systemd/user/` sans rien inscrire dans le coffre : aucune trace
  de la tâche côté OBSIA.
- Le vérificateur détecte bien les quatre erreurs qui rendent une tâche
  silencieusement inopérante — essai fait sur une copie jetable du coffre :
  `actif` non booléen, `quand` non quoté, agent inexistant, corps sans
  `## Instruction`.
- `python3 scripts/generer_prompt.py` fait désormais apparaître les tâches
  déclarées : un harness neuf apprend leur existence par le prompt système.

## Interprétation

Le problème n'était pas l'absence d'un skill `cron` — il existait — mais le
fait qu'il agissait sans déclarer. C'est le même schéma que les index
maintenus à la main : une information qui n'existe qu'à un seul endroit,
hors de portée du vérificateur. Voir [[un-etat-non-declare-est-perdu]].

## Questions ouvertes

- La réconciliation est décrite mais pas outillée : elle se fait à la lecture,
  écran par écran. Un script `scripts/reconcilier_taches.py` (lecture seule,
  affichant le tableau des écarts) serait le prolongement naturel, mais il
  devrait interroger systemd — donc dépendre d'un exécutant, ce que le coffre
  évite jusqu'ici.
- Rien ne couvre encore la portabilité des **conversations** : la mémoire en
  est le substitut, l'historique brut reste chez le harness.

## Synthèse IA

Trois choses rendent une tâche portable : elle est déclarée dans le dépôt, elle
porte un nom stable qui permet de la retrouver chez n'importe quel exécutant,
et son instruction est auto-suffisante. Le reste — systemd, cron, planificateur
distant — est interchangeable par construction.
