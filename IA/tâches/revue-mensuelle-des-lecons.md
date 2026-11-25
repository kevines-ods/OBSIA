---
schema: 1
kind: tâche
name: revue-mensuelle-des-lecons
description: Statuer sur les modifications de skill dont la date de revue est passée — confirmer ou annuler — puis compiler au plus une leçon accumulée. Une par mois, jamais deux.
module: planification
mode: agent
quand: "0 11 1 * *"
fuseau: Europe/Paris
exécutant: local
agent: assistant
actif: true
---

# Tâche — Revue mensuelle des leçons

## Intention

Le skill `compilation-des-lecons` sait faire redescendre une leçon dans un
skill, mais rien ne le déclenche : il attend qu'on pense à lui, ce qui est
exactement la panne qu'il répare. Cette tâche est ce qui y pense.

Elle porte aussi la moitié qu'on oublie toujours : **relire les modifications
déjà faites**. Le registre `IA/system/impact-des-skills.md` donne à chacune une
date de revue ; sans passage régulier, cette colonne ne veut rien dire et tout
reste indéfiniment `appliqué`.

Mensuelle, parce qu'une leçon par mois est déjà plus que le rythme auquel le
coffre en produit — sept en six mois. Plus fréquent, la tâche tournerait à
vide ; plus rare, les revues échues s'empileraient.

`exécutant: local` : elle lit les leçons du coffre parent
(`Mon coffre/0-MEMOIRES/*/expériences/`) et écrit des patchs dans un clone du
dépôt produit. Un planificateur distant n'aurait rien sous la main.

Activée le 2026-09-26 sur décision de l'utilisateur, **avant** que le skill
ait tourné une fois en entier sur une vraie leçon. Le premier déclenchement
sert donc d'épreuve : son rapport est à relire avec soin, parce qu'une
procédure jamais éprouvée découvre ses défauts sans personne devant l'écran.

## Instruction

Place-toi à la racine du dépôt produit. Deux temps, dans cet ordre — les
revues d'abord, parce qu'une modification non statuée fausse le jugement sur la
suivante.

**1. Statuer sur les revues échues.**

Lis `IA/system/impact-des-skills.md` — le tableau, pas la colonne seule : un
statut se lit avec la date de `Revue` qui l'accompagne. Pour chaque ligne au
statut `appliqué` **ou `proposé`** dont la date de `Revue` est passée, tranche :

- un cas réel a montré depuis que le skill modifié fait mieux → `confirmé`,
  la date de revue disparaît ;
- rien ne l'a confirmée → la modification n'a pas fait ses preuves. Prépare son
  annulation (`git revert` du commit concerné, statut `annulé`, raison en
  clair) **sans jamais toucher la note d'expérience** : la leçon reste vraie,
  c'est son application qui ne l'était pas ;
- la confirmation est en cours et vérifiable bientôt → repousse la date **une
  seule fois**, en écrivant pourquoi. Une revue repoussée deux fois est une
  revue qu'on n'ose pas trancher : annule.

Pour les `proposé` échues, le trancher ne doit pas attendre un cas réel — elles
n'ont pas encore vécu. Vérifie le sort réel de la proposition :

- fusionnée depuis dans `main` → `appliqué`, et la ligne prend une date de
  revue à un mois ;
- jamais partie, PR fermée, branche morte → `annulé`, la raison en clair ; la
  note d'expérience reste, c'est l'application qui ne fut pas ;
- dépassée par l'existant (la règle qu'elle proposait est déjà là) → `sans objet`.

**2. Compiler au plus une leçon.**

Charge le skill `compilation-des-lecons`
(`IA/skills/compilation-des-lecons.md`) et applique sa procédure du début à la
fin, **sur une seule leçon**. Sa première étape liste ce qui n'a jamais été
examiné.

S'il n'y a rien à compiler, ou rien d'assez éprouvé pour l'être, dis-le et
arrête-toi là. Une tâche qui ne trouve rien à faire a bien travaillé ; en
inventer est le seul vrai échec possible ici.

**Rapport.** Quatre points : les revues statuées et comment, la leçon compilée
et vers quel skill, ce qui reste en attente et pourquoi, et **l'état du stock** —
combien de leçons jamais examinées dans `0-MEMOIRES/*/expériences/` (celles
qui ne figurent pas au registre), et l'âge de la plus ancienne. Sans compteur,
« une par mois » ne draine rien : le flux d'entrée qui dépasse le rythme se
voit ici, avant de se sentir.

Ne fusionne rien toi-même. `IA/` passe par patch soumis à revue (§2) — y
compris l'annulation d'une modification, qui est un changement comme un autre.

**Livraison.** Le patch vit sur une branche dédiée d'un worktree propre,
committée — rien de plus. La tâche n'ouvre jamais de PR et ne pousse jamais
vers le dépôt distant : ouvrir la PR est le geste de qui relit, jamais le sien.
Une branche candidate encore sans PR au cycle suivant est déclarée morte dans
le rapport, et sa leçon retourne au stock : le silence n'est pas une décision.
