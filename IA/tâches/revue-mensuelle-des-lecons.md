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
actif: false
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

`exécutant: local` : elle lit `mémoire/` et écrit des patchs dans un clone du
coffre. Un planificateur distant n'aurait rien sous la main.

`actif: false` tant que le skill n'a pas tourné une fois en entier, de bout en
bout, sur une vraie leçon. Déclencher une procédure jamais éprouvée, c'est
découvrir ses défauts un 1er du mois, sans personne devant l'écran.

## Instruction

Place-toi à la racine du coffre OBSIA. Deux temps, dans cet ordre — les revues
d'abord, parce qu'une modification non statuée fausse le jugement sur la
suivante.

**1. Statuer sur les revues échues.**

Lis `IA/system/impact-des-skills.md`. Pour chaque ligne au statut `appliqué`
dont la date de `Revue` est passée, tranche :

- un cas réel a montré depuis que le skill modifié fait mieux → `confirmé`,
  la date de revue disparaît ;
- rien ne l'a confirmée → la modification n'a pas fait ses preuves. Prépare son
  annulation (`git revert` du commit concerné, statut `annulé`, raison en
  clair) **sans jamais toucher la note d'expérience** : la leçon reste vraie,
  c'est son application qui ne l'était pas ;
- la confirmation est en cours et vérifiable bientôt → repousse la date **une
  seule fois**, en écrivant pourquoi. Une revue repoussée deux fois est une
  revue qu'on n'ose pas trancher : annule.

**2. Compiler au plus une leçon.**

Charge le skill `compilation-des-lecons`
(`IA/skills/compilation-des-lecons.md`) et applique sa procédure du début à la
fin, **sur une seule leçon**. Sa première étape liste ce qui n'a jamais été
examiné.

S'il n'y a rien à compiler, ou rien d'assez éprouvé pour l'être, dis-le et
arrête-toi là. Une tâche qui ne trouve rien à faire a bien travaillé ; en
inventer est le seul vrai échec possible ici.

**Rapport.** Trois points : les revues statuées et comment, la leçon compilée
et vers quel skill, ce qui reste en attente et pourquoi.

Ne fusionne rien toi-même. `IA/` passe par patch soumis à revue (§2) — y
compris l'annulation d'une modification, qui est un changement comme un autre.
