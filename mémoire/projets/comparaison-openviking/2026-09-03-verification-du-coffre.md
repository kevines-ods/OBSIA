# 2026-09-03 — Vérification automatique du coffre

Application du point 4 de [[2026-09-03-comparaison-openviking]] : donner au
contrat un moyen de se faire respecter.

## Statut
🟢 Appliqué — deux scripts, un workflow CI, contrat §11 ajouté.

---

## Décisions

- **`scripts/regenerate_index.py`** remplace le script jetable utilisé au point
  1. Les deux index sont désormais générés, avec un mode `--verifier`.
- **`scripts/verifier_coffre.py`** confronte les fichiers entre eux. N'écrit
  rien, sort en code 1.
- **`.github/workflows/verifier-coffre.yml`** le lance à chaque poussée et sur
  chaque PR.
- **Aucune dépendance.** Bibliothèque standard de Python uniquement — le coffre
  ne doit dépendre d'aucune installation pour être vérifiable. Le workflow ne
  fait donc pas de `pip install`.
- **§11 ajouté au contrat plutôt qu'inséré.** Les §1 à §10 sont référencés
  depuis `HISTORIQUE.md`, `assistant.md`, `prompt-fondateur.md`,
  `generer_prompt.py` et les sommaires : renuméroter aurait cassé une vingtaine
  de renvois pour un gain nul.
- **Pas de détection de secrets dans le vérificateur.** Le coffre parle
  légitimement de « mot de passe » et « jeton d'API » dans ses skills : un
  balayage du dépôt entier ne produirait que des faux positifs. Le contrôle du
  README, qui porte sur `git diff --cached`, reste le bon outil.

---

## Évidence — ce que le vérificateur contrôle, et la preuve qu'il le fait

Chaque contrôle a été mis en défaut volontairement, puis le coffre restauré.
Les huit ont déclenché une erreur et un code de sortie 1 :

| Faute injectée | Détectée |
| --- | --- |
| `description: >` (scalaire replié) | oui — message nommant la valeur obtenue |
| `name: cronos` dans `cron.md` | oui, plus l'effet de bord : le skill `cron` devient introuvable |
| `skills: a, b` au lieu d'une liste | oui |
| agent déclarant `proxmoxx` | oui |
| note dupliquée dans `brouillon/` | oui, avec les deux chemins |
| index modifié à la main | oui |
| note modifiée sans régénérer le sommaire | oui |
| `read_only` supprimé | oui |

Le coffre revient au vert après restauration — vérifié.

Le deuxième cas est instructif : renommer un skill produit **deux** erreurs,
l'incohérence locale et la référence cassée chez l'agent. C'est le
recoupement entre fichiers qui a de la valeur, pas la validation isolée.

---

## Interprétation

Le contrôle le plus utile n'est pas la validation de frontmatter — un
frontmatter cassé se voit vite — mais la **fraîcheur des fichiers générés**.
C'est lui qui aurait attrapé les erreurs du point 1 des mois plus tôt.

Le mécanisme est l'équivalent pauvre du `pending_child_changes` d'OpenViking,
qui marque un résumé en retard sur son contenu. OpenViking le résout par des
files asynchrones et un serveur ; ici, comparer le fichier généré à ce que le
script produirait suffit, parce que la génération est déterministe et
instantanée. Un dépôt Git n'a pas besoin de cohérence *éventuelle* : il peut
exiger la cohérence *immédiate*, et refuser la poussée sinon.

Limite assumée : le vérificateur contrôle la **forme et la cohérence**, jamais
le fond. Il ne dira pas qu'une description est mauvaise, seulement qu'elle est
absente, repliée ou divergente. Le jugement reste humain.

---

## Questions ouvertes

- [ ] Ajouter un crochet Git local (`pre-commit`) appelant les trois scripts,
      pour ne pas découvrir l'échec en CI ? À peser : un crochet non versionné
      s'oublie, un crochet versionné doit être installé à la main.
- [ ] Le vérificateur doit-il exiger une structure minimale dans les notes de
      mémoire — un chapeau, puis `## Statut` — pour que les sommaires soient
      toujours bons ? Question laissée ouverte au point 2.

---

## Synthèse IA

Le point 4 était classé « effort moyen, gain fort ». Le gain s'est révélé
supérieur : les erreurs trouvées aux points 1 et 2 n'étaient pas des accidents
mais la conséquence prévisible d'un dépôt où rien ne vérifiait rien. Trois
fichiers dérivés existaient, deux étaient faux.

Le coffre décrit désormais ses propres règles **et** les fait appliquer. C'est
la différence entre un contrat et une intention.

## URLs sources

- `freshness` et `pending_child_changes` :
  https://github.com/volcengine/OpenViking/blob/main/docs/en/concepts/03-context-layers.md
