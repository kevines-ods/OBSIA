---
schema: 1
kind: skill
name: compilation-des-lecons
description: Faire redescendre les leçons accumulées dans `mémoire/*/expériences/` vers les skills que l'agent lit pour agir — une seule leçon à la fois, rejouée pour preuve, consignée au registre `IA/system/impact-des-skills.md`. À charger périodiquement, ou dès qu'une erreur se répète alors qu'une note la documente déjà. Ne rédige pas le skill : `createur-de-skill` le fait.
module: noyau
type: outil
read_only: false
---

# Skill — Compilation des leçons

Une leçon rangée dans `expériences/` ne change rien par elle-même : personne ne
la rouvre au moment d'agir. Ce qui est lu au moment d'agir, c'est le skill.
Tant que la leçon n'y est pas passée, elle sera réapprise au prochain échec.

Ce skill fait ce passage, et un seul à la fois.

## Procédure

### 1. Lister ce qui n'a jamais été compilé

```bash
for f in mémoire/*/expériences/*.md; do
  nom=$(basename "$f" .md)
  [ "$nom" = sommaire ] && continue
  grep -q "$nom" IA/system/impact-des-skills.md || echo "jamais compilée : $nom"
done
```

Le registre `IA/system/impact-des-skills.md` fait foi : une leçon qui n'y
figure pas n'a jamais été examinée, ce qui ne veut pas dire qu'elle doit
l'être.

### 2. N'en retenir qu'une

Deux critères, dans cet ordre :

- **elle a été éprouvée** — la note porte un constat réel, pas une supposition.
  Une leçon dont le `## Statut` n'affirme rien attend ;
- **elle a coûté deux fois** — un incident isolé peut rester une note. Ce qui
  se répète malgré une note existante est exactement ce que ce skill traite.

**Une seule par séance.** Deux skills modifiés dans le même patch, et quand
l'un casse plus rien ne dit lequel.

### 3. Trouver la cible réelle

La question est : *quel skill aurait évité ça ?* — pas *quel skill parle du
même sujet*. Pour le savoir sans le deviner, rejouer la demande telle qu'elle
s'est présentée le jour de l'incident :

```bash
python3 scripts/evaluer_routage.py --explique "la demande qui a mené à l'erreur"
```

Le skill qui sort en tête est celui qui aurait été chargé — donc celui à
modifier. Ce n'est pas toujours celui auquel on pense.

Trois issues, toutes légitimes :

| Ce qu'on trouve | Ce qu'on fait |
| --- | --- |
| aucun skill n'était en cause | on s'arrête, et on inscrit la leçon au registre en `sans objet` |
| un skill existant | on le modifie, étapes 4 à 7 |
| le geste n'a aucun skill | on le note comme skill à créer, **et on s'arrête là** |

Créer un skill est une autre décision, avec son propre cadrage. La glisser
dans une compilation de leçon, c'est la prendre sans l'avoir posée.

### 4. Séparer la règle du récit

Ce qui passe dans le skill est **la règle** : quoi faire, quoi vérifier, dans
quel ordre. Ce qui reste dans la note est **le récit** : le symptôme, la cause,
comment on l'a su, le message d'erreur trompeur.

Test de tri, phrase par phrase : **si je la retire du skill, l'agent refait-il
l'erreur ?** Si non, elle n'a rien à y faire — elle alourdit le contexte de
tout le monde et fera diverger la note et le skill à la première correction.

### 5. Écrire la modification

Charger `createur-de-skill` : c'est lui qui dit comment on écrit dans
`IA/skills/`. Ici, deux exigences de plus :

- **le patch est minimal** — on modifie la section concernée, on ne réécrit pas
  le skill à l'occasion ;
- si la modification touche la `description`, ajouter ou ajuster une ligne dans
  `IA/system/routage-attendu.md` : sans cela, la nouvelle formulation n'est
  couverte par aucun contrôle de déclenchement.

### 6. Rejouer, pas affirmer

Reproduire l'échec que la leçon décrit, appliquer la règle, montrer que ça
passe. C'est la seule preuve qui vaille, et c'est ce qui distingue une
compilation d'une réécriture de confort.

Quand l'échec n'est pas reproductible — matériel absent, service distant,
incident non rejouable — l'écrire tel quel au registre : **`non rejoué` est une
information ; `vérifié` à tort n'en est pas une.**

Puis les contrôles du coffre :

```bash
python3 scripts/verifier_coffre.py
python3 scripts/evaluer_routage.py
```

Ils vérifient la forme et le déclenchement. **Jamais le corps d'un skill** :
verts, ils ne disent rien de la justesse de ce qui vient d'être écrit.

### 7. Consigner des deux côtés

- une ligne dans `IA/system/impact-des-skills.md` — dossier `IA/system/`, donc
  **patch soumis à revue** (§2). Statut `appliqué`, et une date de `Revue` tant
  qu'aucun cas réel n'a confirmé ;
- une section `## Compilée dans un skill` à la fin de la note d'expérience, qui
  nomme le skill destinataire. Sans ce retour, la note laisse croire que sa
  leçon dort encore.

### 8. Si la modification se révèle fausse

`git revert` sur le skill, et la ligne du registre passe en `annulé` avec la
raison en clair. **La note d'expérience, elle, ne bouge pas.**

Une leçon reste vraie même quand la façon de l'appliquer était mauvaise.
L'effacer, c'est se condamner à la réapprendre.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « la note dit déjà tout, inutile de le répéter dans le skill » | la note n'est pas ouverte au moment d'agir. C'est exactement la panne qu'on répare |
| « tant qu'à faire, je compile les trois leçons d'un coup » | trois modifications dans un patch : la première qui casse emporte les deux autres dans le doute |
| « je recopie la note dans le skill, ce sera complet » | le skill enfle, et les deux versions divergent dès la première correction. La règle, pas le récit |
| « la note dit vérifié, pas besoin de rejouer » | vérifié un autre jour, sur une autre machine. Si tu ne rejoues pas, le registre doit dire `non rejoué` |
| « le vérificateur est vert, donc c'est bon » | il lit la forme et le déclenchement. Le corps d'un skill n'est relu par personne |
| « ça n'a pas marché, j'efface la leçon » | c'est l'application qui était mauvaise, pas la leçon. Effacée, elle revient par le même échec |
| « il n'y a pas de skill pour ça, j'en crée un tout de suite » | créer un skill se cadre. Le noter, et s'arrêter à la note |

## Contraintes

`IA/skills/` est en écriture directe pour un agent qui déclare
`createur-de-skill` ; `IA/system/` ne l'est pas. Les zones et le régime de
patch sont au §2 de `../system/VAULT-CONTRACT.md`, qui fait foi.
