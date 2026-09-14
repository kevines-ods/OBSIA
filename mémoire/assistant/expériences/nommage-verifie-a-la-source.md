# Un nom enregistré d'après une description n'est pas un nom vérifié

Leçon générale, tirée du coffre parent. Vaut pour tout identifiant qu'on
recopie sans pouvoir le confronter à la chose nommée.

## Statut

🟢 Vérifiée — six jours de documentation fausse, sur des noms que des
commandes exécutaient.

---

## Le constat

Le 8 septembre, l'utilisateur réorganise son coffre : `0-PROJETS`,
`1-CONCEPTS`, `2-RESSOURCES`, `0-EN VRAC` disparaissent. L'entrée
d'historique enregistre la nouvelle structure : `PROJETS/`, `DOCUMENTS/`,
`SAVOIRS/`…

Les vrais noms étaient `-PROJETS/`, `-DOCUMENTS/`, `-SAVOIRS/`. Seul le
préfixe **numérique** était tombé ; le tiret est resté. La déduction
— « les préfixes disparaissent » — était raisonnable et fausse.

174 occurrences se sont propagées dans 20 fichiers, dont des commandes qu'une
tâche planifiée exécute au déclenchement. Personne ne l'a vu pendant six jours.

## Pourquoi rien ne l'a détecté

`verifier_coffre.py` contrôle les chemins cités — c'est même une leçon déjà
tirée dans ce coffre. Mais il ne voit que le dépôt. Le coffre parent est hors
du dépôt, et le §11 l'écarte explicitement : le vérificateur ne peut pas
ouvrir un dossier qui n'existe que sur la machine de l'utilisateur.

L'angle mort n'est donc pas un oubli à corriger, c'est une **frontière**. Un
contrôle automatique s'arrête là où s'arrête ce qu'il peut lire.

## La leçon

> **Un nom obtenu par déduction est une hypothèse. Un nom obtenu en regardant
> la chose est un fait. Les deux s'écrivent pareil, et rien ne les distingue
> une fois écrits.**

D'où la règle : quand une chose nommée est **hors de portée du contrôle
automatique**, son nom se demande ou se vérifie à la source — il ne se déduit
pas d'une description de changement. Et quand il a été déduit, l'écrire :
« d'après ce que tu m'as dit » vaut avertissement pour le lecteur suivant.

Le signal à reconnaître : on écrit un identifiant qu'on n'a **jamais lu**
soi-même, seulement entendu décrire. Deux questions suffisent alors — *puis-je
le vérifier maintenant ?* et *si je me trompe, qu'est-ce qui le dira ?* Quand
la seconde réponse est « rien », c'est le moment de demander.

## Le cas particulier du tiret initial

Le renommage a livré un second piège, celui-là mécanique : un argument qui
commence par `-` est lu comme une **option** par la quasi-totalité des
commandes Unix.

| Ce qui casse | Ce qui marche |
| --- | --- |
| `rg "motif" -SAVOIRS` | `rg "motif" ../-SAVOIRS` |
| `--dossier -SAVOIRS` (argparse refuse) | `--dossier=-SAVOIRS` |

Vérifié par exécution, pas supposé. Un préfixe `../` ou `./` désamorce le
tiret, puisque l'argument ne commence alors plus par lui. Règle écrite au §7
du contrat.

## Généralisation

Un nom est une donnée comme une autre : il a une source, et cette source est
soit la chose elle-même, soit quelqu'un qui la décrit. La seconde est
faillible, et sa faillibilité ne laisse aucune trace dans le résultat.
