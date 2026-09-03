# 2026-09-03 — Forme dossier des skills, et crochet de pré-commit

Application du point 5 de [[2026-09-03-comparaison-openviking]], plus le
crochet Git laissé en question ouverte au point 4.

## Statut
🟢 Appliqué — forme dossier reconnue et contrôlée, crochet versionné. Aucun
skill converti : aucun n'en a besoin aujourd'hui.

---

## Décisions

- **Le point d'entrée s'appelle `<nom>.md`, pas `SKILL.md`.** Deux règles du
  contrat l'imposent : le §5 veut que le fichier porte le `name`, et le §6
  l'unicité des noms de notes dans le coffre parent. Douze fichiers `SKILL.md`
  rendraient les rétroliens Obsidian ambigus.
- **Rien n'est converti.** Le plus gros skill fait 187 lignes, pour un seuil de
  découpage fixé à 500 par `createur-de-skill`. Convertir aujourd'hui
  ajouterait de l'indirection sans rien gagner.
- **`scripts/` et `assets/` sortent du balayage des noms** : ce sont du code et
  des gabarits, pas des notes du coffre. `references/` y reste, puisqu'il
  contient des notes.
- **Le crochet vit dans `.githooks/`, versionné**, et s'active par
  `git config core.hooksPath .githooks`. Un crochet dans `.git/hooks/` n'est
  pas versionné et se perd au clone suivant ; celui-ci se lit, se revoit et se
  corrige comme le reste.
- **Le crochet ne modifie rien.** Il appelle `verifier_coffre.py` et refuse le
  commit en rappelant la commande de régénération. Un crochet qui réécrit des
  fichiers pendant un commit produit des surprises.

---

## Évidence

**La documentation se contredisait.** `createur-de-skill.md` décrivait depuis
le début une arborescence `nom-du-skill/SKILL.md`, alors que les douze skills
du coffre sont des fichiers plats `<nom>.md` et que le §5 exige `name` = nom du
fichier. Personne ne pouvait suivre les deux à la fois. La contradiction est
levée en faveur des règles du contrat.

**La forme dossier a été essayée pour de vrai**, sur un skill jetable
`essai-dossier/` créé puis supprimé :

| Cas | Résultat |
| --- | --- |
| dossier bien formé | collecté, indexé avec le lien `../skills/essai-dossier/essai-dossier.md`, présent dans le prompt |
| `references/` non cité depuis le corps | avertissement |
| point d'entrée renommé `SKILL.md` | erreur, code 1 |

**Le crochet a été essayé pour de vrai** : commit accepté sur coffre sain ;
commit refusé après avoir renommé `name: mermaid` en `mermaidz`, avec les trois
erreurs affichées et `HEAD` inchangé.

Incident au passage : pour restaurer le fichier cassé, `git checkout -- <f>`
n'a rien fait, parce qu'il restaure depuis l'**index** — lequel contenait déjà
la version cassée à cause du `git add -A` précédent. Il fallait
`git restore --source=HEAD --staged --worktree <f>`.

---

## Interprétation

Le point 5 est le seul de la liste dont le gain est **différé** : il ne corrige
rien aujourd'hui, il évite un blocage plus tard. C'est aussi le seul où
l'implémentation valait surtout pour ce qu'elle a révélé — une documentation
qui décrivait une structure que le coffre n'utilisait pas et que ses propres
règles interdisaient.

Le renoncement à `SKILL.md` a un coût réel : un skill OBSIA n'est plus
directement importable dans un outil qui attend cette convention, et
réciproquement. Le coût est jugé inférieur à celui de rétroliens ambigus dans
le coffre parent, et un renommage à l'import réglerait la question en une
ligne de script si le besoin apparaît.

---

## Questions ouvertes

- [ ] Écrire ce script de conversion `<nom>.md` ↔ `SKILL.md` le jour où un
      skill doit être échangé avec un outil tiers ?
- [ ] Le crochet devrait-il proposer de régénérer lui-même les fichiers
      périmés, au lieu de seulement afficher la commande ?

---

## Synthèse IA

Cinq points sur sept de l'analyse sont appliqués. Il reste le 6 — distiller la
mémoire en fin de session — et le 7 — sortir les gabarits de prompt du code
Python, classé « gain faible » et toujours vrai.

Le fil commun des cinq : le coffre énonçait des règles que rien ne vérifiait,
et documentait par endroits des conventions qu'il n'appliquait pas. Ce qui a
été copié à OpenViking, ce n'est pas son architecture — c'est l'idée qu'un
contexte doit pouvoir être jugé avant d'être lu, et qu'un fichier dérivé doit
être produit puis contrôlé.

## URLs sources

- Structure d'un skill chez OpenViking (forme `SKILL.md` + `references/`) :
  https://github.com/volcengine/OpenViking/blob/main/docs/en/concepts/02-context-types.md
