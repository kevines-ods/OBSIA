---
schema: 1
kind: skill
name: cadrage-produit
description: Figer le besoin dans un document versionné en huit sections (Problème, Utilisateur cible, Solution, User stories numérotées, Critères de succès, Hors périmètre, Décisions produit, Notes) et créer le dépôt du projet s'il n'existe pas encore. À charger une fois l'accord obtenu par interrogation-du-besoin, jamais avant. Produit `docs/CADRAGE.md` dans le dépôt du projet, validé section par section.
type: outil
read_only: false
---

# Skill — Cadrage produit

> **Adaptation.** Reprend `/cadre` de `naiersaidane/claude-mastery` (MIT),
> traduit et aligné sur les conventions du coffre. Le document s'appelle
> `CADRAGE.md` — c'est ce qu'on nomme ailleurs un PRD.

Ce qui n'est pas écrit n'est pas cadré. Un accord oral se dissout dès la
première difficulté technique, et chacun se souvient de la version qui
l'arrange.

## 1. Le dépôt du projet — à créer ici s'il n'existe pas

Le projet vit dans `Mon coffre/PROJETS/<nom-du-projet>/`, dépôt git à part
entière. Le coffre OBSIA ne contient jamais le code d'une application (§3).

```bash
mkdir -p "$HOME/Mon coffre/PROJETS/<nom-du-projet>/docs"
git -C "$HOME/Mon coffre/PROJETS/<nom-du-projet>" init
```

Rien n'est poussé sur GitHub à ce stade : une idée abandonnée ne laisse pas
de dépôt vide derrière elle. La publication a lieu à la porte 8, par
`livraison-git`.

**Rappeler à l'utilisateur, une fois, à la création :** ajouter
`PROJETS/<nom-du-projet>/` aux *Fichiers exclus* d'Obsidian (Options →
Fichiers et liens). Sans ça, le Markdown du dépôt et de ses dépendances entre
dans la recherche du coffre, et l'unicité des noms de notes (§6) casse dès le
deuxième projet.

## 2. Si `docs/CADRAGE.md` existe déjà

Le lire. Croiser avec ce qui vient d'être compris et n'interroger que sur les
écarts. Confronter les contradictions plutôt que les absorber : *« Tu avais
tranché X, ce qu'on vient de dire suggère Y — on garde lequel ? »*

## 3. Rédiger, puis faire valider section par section

Écrire le document complet dans la conversation d'abord, selon le gabarit
ci-dessous. L'utilisateur valide ou corrige **une section à la fois** ; sur
correction, ne re-poster que la section touchée. Une fois tout validé
seulement, écrire le fichier.

```markdown
# Cadrage — <nom du projet>

## Problème
Ce que vit l'utilisateur : la friction, le contexte, pourquoi maintenant.
En prose, à la troisième personne.

## Utilisateur cible
Profil et contexte d'usage, assez précis pour se représenter une personne réelle.

## Solution
Ce que le produit permet de faire, du point de vue de qui s'en sert.
Pas comment c'est construit.

## User stories
Liste numérotée US-1, US-2… au format « En tant que <acteur>, je veux
<fonctionnalité>, afin de <bénéfice> ». Couvre le parcours principal, les
états vides, les erreurs, les cas limites.

## Critères de succès
Vérifiables : un événement observable ou une mesure. Jamais un jugement
intérieur (« comprend », « identifie »).

## Hors périmètre
Ce qu'on refuse explicitement. C'est cette section qui protège du
sur-engineering — la bâcler, c'est accepter la dérive.

## Décisions produit
Comportement visible : limites chiffrées, états vides, format d'affichage,
messages d'erreur. Test mental : si l'utilisateur ne peut pas observer la
différence à l'usage, ça n'a rien à faire ici.

## Notes
Risques, dépendances, hypothèses. « Rien à signaler. » si rien.
```

## 4. Écrire et confirmer

`docs/CADRAGE.md` dans le dépôt du projet, puis un commit. Confirmer en une
ligne le chemin écrit.

## Règles

- Le vocabulaire est celui de l'utilisateur, **verbatim**. Traduire ses mots
  en jargon lui fait perdre son propre projet.
- Aucune technologie nommée, aucun chemin de fichier, aucun extrait de code :
  la technique se décide à la porte 4, et un cadrage qui la contient
  interdit de la rediscuter.
- Aucun trou laissé en « à préciser ». Un trou dans le cadrage est un trou
  qu'on comblera par une supposition au moment de coder.
