# 2026-09-14 — Le coffre parent ne s'appelait pas comme la doc le disait

Trois changements liés : les dossiers du coffre parent reprennent leur nom
réel (préfixe `-`), `-PROJETS/` s'ouvre à une note de suivi tenue par l'agent,
et le partage public/privé des notes de projet est écrit.

## Statut

🟡 Appliqué et vérifié côté dépôt — les quatre scripts sortent en 0. **Non
éprouvé sur le coffre réel** : aucune session n'a encore écrit une note de
suivi ni lancé une commande sur `-SAVOIRS/`. C'est là que se verra si le
tiret pose d'autres problèmes.

---

## Le déclencheur

Question de l'utilisateur : « les agents ne peuvent pas écrire dans -PROJETS à
la racine du coffre ? ». Le tiret, écrit deux fois, n'était pas une coquille.

## Décisions

- **Les dossiers du coffre parent s'appellent `-PROJETS/`, `-DOCUMENTS/`,
  `-PERSONNELS/`, `-SAVOIRS/`, `-EN-VRAC/`.** La doc disait les mêmes noms sans
  tiret depuis le 8 septembre. 174 occurrences corrigées dans 20 fichiers.

- **Un chemin qui commence par `-` est lu comme une option.** `rg "x" -SAVOIRS`
  échoue, `--dossier -SAVOIRS` est refusé par argparse (vérifié). Trois formes
  imposées au §7 : `../-SAVOIRS`, `"$HOME/Mon coffre/-SAVOIRS"`,
  `--dossier=-SAVOIRS`. Deux appels du skill `traitement-des-notes` étaient
  cassés par le renommage et ont été corrigés.

- **`-PROJETS/<nom-du-projet> — résumé.md`** : une note de suivi vivante par
  projet, créée et tenue par l'agent, mise à jour sur place. Seule exception à
  la protection des notes de `-PROJETS/`, et pour une raison précise : c'est la
  seule note dont l'agent est l'auteur. Le suffixe ` — résumé` rend la
  propriété visible sans ouvrir le fichier.

- **Elle vit à côté du dépôt git, jamais dedans** : le dossier du dépôt est
  exclu de l'index d'Obsidian, une note posée à l'intérieur serait invisible à
  la recherche et aux rétroliens.

- **Partage public/privé écrit (§7.3.1)** : `mémoire/projets/` ne porte que les
  chantiers **sur le coffre** ; un projet de l'utilisateur va dans
  `-PROJETS/`. Le test : *est-ce que ça décrit le coffre ?*

- **Un skill `configuration-mcp`** traduit les fiches `IA/MCP/` en
  configuration réelle chez un harness, et vérifie chaque serveur par un appel
  réel. Déclaré par `assistant`.

## Évidence

- `HISTORIQUE.md` §8 septembre : « Les noms `0-PROJETS`, `1-CONCEPTS`… ne
  décrivent plus rien de réel » — l'entrée enregistrait la chute du préfixe
  **numérique**, et a conclu à tort que le tiret tombait aussi.
- `argparse` refuse `--dossier -DOCUMENTS` et accepte `--dossier=-DOCUMENTS` :
  vérifié par exécution, pas supposé.
- `.gitignore` ne couvrait ni `mcp.json` ni `.mcp.json` : une configuration
  remplie posée dans le dépôt aurait été committée.

## Interprétation

L'erreur de nommage n'a pas été détectée en six jours parce que **rien ne
pouvait la détecter** : le coffre parent est hors du dépôt, et
`verifier_coffre.py` ne voit que ce qui est versionné. Le §11 l'écarte
explicitement. C'est un angle mort structurel, pas un oubli.

Quant à l'écriture dans `-PROJETS/`, la règle d'origine confondait deux
protections : empêcher un agent d'écraser les notes de l'utilisateur, et
l'empêcher d'écrire tout court. La première est nécessaire, la seconde le
poussait à ranger des résumés de projet dans un dépôt public.

## Questions ouvertes

- **Aucun contrôle ne peut valider les noms du coffre parent.** La seule parade
  serait une commande lancée sur la machine de l'utilisateur, hors du dépôt.
  Non résolu, assumé.
- Le nom de la note de suivi (` — résumé`) n'est pas contrôlé non plus :
  `verifier_coffre.py` ne voit pas le coffre parent.
- `configuration-mcp` n'a jamais été exécuté : écrit d'après les fiches et les
  gabarits, jamais sur un harness réel.

## Synthèse IA

Les trois demandes de l'utilisateur pointaient chacune un défaut réel, et
aucune n'était formulée comme un signalement de bug.
