---
schema: 1
kind: tâche
name: publication-hebdomadaire
description: Publier le dépôt public depuis le dépôt privé chaque lundi — aperçu lu et rapporté avant toute écriture, jamais de poussée directe.
module: planification
mode: agent
quand: "0 10 * * 1"
fuseau: Europe/Paris
exécutant: local
agent: administrateur
actif: true
---

# Tâche — Publication hebdomadaire

## Intention

Le dépôt public est dérivé à sens unique du dépôt privé (§13.5) : rien ne
part tout seul, et c'est ce qui crée la fenêtre de validation. La contrepartie
se paie en retard : sans passage régulier, l'écart grandit en silence — la
première fois, il a fallu douze jours et quarante-sept pull requests pour
s'en apercevoir. Un passage hebdomadaire le tient sous la journée.

Le lundi à 10 h, juste après la revue hebdomadaire du coffre : le public
reçoit l'état que la revue vient de constater cohérent.

`mode: agent` parce que publier n'est pas mécanique : l'aperçu se lit, une
trouvaille se juge, et le sens unique exclut toute synchronisation de fond.
`exécutant: local` parce que la publication a besoin des clones des deux
dépôts sous la main — un planificateur distant n'aurait rien à publier.

## Instruction

Charge d'abord `IA/system/installation-et-publication.md` — la procédure fait
foi, et ses garde-fous sont appliqués par le code. Puis :

1. **Prépare** : mets le clone du dépôt privé à jour, et publie depuis un
   *worktree* détaché sur sa branche par défaut distante — jamais depuis
   l'arbre principal, jamais sous `/tmp`
   (`IA/system/travail-en-parallele.md`, section « Publier »).
2. **Vérifie la liste locale des noms interdits** (`~/.config/obsia/
   noms-interdits`, hors dépôt) : elle doit exister et être remplie. Ne
   jamais en afficher le contenu. Si elle manque : arrête-toi et rapporte-le.
3. **Lance l'aperçu** — `python3 scripts/publier.py --cible <clone local du
   dépôt public>` — et rapporte le compte de fichiers, les exclusions et
   toute alerte **avant** d'écrire quoi que ce soit.
4. **Si l'aperçu est propre** : relance avec `--appliquer --commit`, pousse
   le commit de la cible sur une branche `publication/AAAA-MM-JJ` du dépôt
   public, et ouvre une pull request sur sa branche par défaut. Jamais de
   poussée directe sur la branche par défaut, jamais de fusion sans
   vérification verte.
5. **Si l'aperçu signale** une trouvaille ou un avertissement : corrige la
   source ou rapporte — `--forcer` ne se décide pas seul, et il ne franchit
   jamais une clé privée, un jeton connu ni un chemin de la machine. Un nom
   de la liste locale est un avertissement à rapporter, pas une fuite à
   forcer.

Rapporte en clair : fichiers publiés, zones vidées et fichiers suivis non
publiés, trouvailles et avertissements, la pull request ouverte. Consigne le
geste au carnet du chantier (§9).
