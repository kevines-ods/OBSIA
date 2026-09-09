---
schema: 1
kind: skill
name: systeme-de-design
description: Proposer un système visuel cohérent et assumé — direction, typographie, palette, densité, mouvement — avec ce qui est conventionnel et ce qui est pris comme risque, puis produire `docs/DESIGN.md` et un aperçu HTML que l'utilisateur ouvre et regarde. À charger après le choix de la stack, pour tout projet ayant une interface visible. Inutile pour un outil sans interface.
type: outil
read_only: false
---

# Skill — Système de design

> **Adaptation.** Reprend `/design` de `naiersaidane/claude-mastery` (MIT),
> condensé et aligné sur les conventions du coffre.

Un design décidé écran par écran produit une interface qui n'a pas de visage.
Le système se décide **une fois**, avant le premier CSS, et chaque écran s'y
conforme ensuite.

L'agent est ici un consultant, pas un formulaire : il propose, il justifie,
il accepte d'être corrigé.

## Procédure

### 1. Une seule question de cadrage

Si `docs/DESIGN.md` existe : *« On met à jour, on repart de zéro, ou on
garde ? »* Sinon, lire `docs/CADRAGE.md` — utilisateur cible et problème y
sont déjà — et poser **une** question, celle qui gouverne tout le reste :

> « Qu'est-ce qu'on doit retenir de ce produit en trois secondes ? Un ressenti
> (« sobre »), un visuel (« le bleu presque noir »), une posture (« pour
> bricoleurs, pas pour managers »). Une phrase. »

Chaque décision qui suit sert cette phrase. Une décision qui ne la sert pas
est à retirer.

### 2. Proposer le système entier, d'un coup

Pas section par section : la cohérence ne se voit qu'ensemble.

```
DIRECTION    : <la direction> — <pourquoi, en une ligne>
TYPOGRAPHIE  : <titrage / texte / données> — 3 polices nommées, libres de préférence
COULEUR      : <approche> + palette en hexadécimal — dont le contraste vérifié
DENSITÉ      : <unité d'espacement + compacité> — pour qui, sur quel écran
MOUVEMENT    : <aucun / fonctionnel / expressif> — et ce qu'on gagne
```

Puis, explicitement, deux listes :

- **CONVENTIONNEL** — ce que tout le monde fait dans cette catégorie, et
  pourquoi c'est le bon choix ici. Une interface entièrement conventionnelle
  est correcte ; elle n'est jamais mémorable.
- **RISQUE** — un ou deux endroits où le produit gagne son propre visage. Pour
  chacun : ce que c'est, ce qu'on gagne, **ce que ça coûte**.

### 3. L'aperçu — non négociable

Écrire `docs/design-preview.html` : spécimen de typographie, nuancier avec les
valeurs hexadécimales, et **une maquette d'un écran réel** du projet. Puis
l'ouvrir :

```bash
xdg-open docs/design-preview.html      # KDE / Arch
```

La porte 5 n'est franchie que quand l'utilisateur a **vu** l'aperçu. Un
système validé sur sa description seule est validé sur un malentendu : les
mots « bleu profond » ne montrent pas le bleu.

### 4. Ajustements, puis écriture

Sur demande d'ajustement, proposer deux ou trois variantes **pour cette
section seulement**, puis re-vérifier la cohérence avec le reste et signaler
en une ligne ce qui ne colle plus. Régénérer l'aperçu si le changement se
voit. Écrire enfin `docs/DESIGN.md`.

## Règles

- **Polices libres par défaut**, servies depuis le dépôt et non depuis un
  service tiers : c'est une valeur du coffre, et ça évite une dépendance
  réseau à chaque chargement de page.
- Contraste vérifié, pas supposé : une palette élégante illisible au soleil ou
  pour un œil fatigué est une palette ratée.
- Le mode sombre se décide **maintenant**, pas après : rattraper un thème
  sombre sur des couleurs écrites en dur coûte plus cher que de partir avec
  des variables.
