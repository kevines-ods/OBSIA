# Un vérificateur vert ne prouve que ce qu'il regarde

Leçon réutilisable sur les contrôles automatiques. Vaut pour tout script de
validation, dans ce coffre comme ailleurs.

## Statut
🟢 Vérifiée le 2026-09-09 — trois erreurs réelles trouvées dans un coffre que
son propre vérificateur déclarait cohérent.

---

## Le constat

`scripts/verifier_coffre.py` sortait en 0, sans le moindre avertissement. Un
audit manuel a pourtant trouvé, le même jour, trois chemins qui ne menaient
nulle part — dont le registre des tags cité par le skill dont c'est la raison
d'être.

La cause n'était pas un bug : c'était le **périmètre**. Le contrôle ne
reconnaissait qu'une forme de chemin — celle qui part de la racine du dépôt,
`IA/skills/x.md`. Or le coffre écrit ses chemins autrement :

| Forme | Employée où | Contrôlée avant |
| --- | --- | --- |
| `IA/skills/x.md` | index, contrat | oui |
| `../system/VAULT-CONTRACT.md` | **tous les skills et agents** | non |
| `python3 scripts/x.py` dans un bloc de code | **instructions de tâches** | non |

Les deux formes non couvertes étaient les plus employées, et les plus
dangereuses : la première casse quand un skill passe de la forme plate à la
forme dossier, la seconde s'exécute au déclenchement d'une tâche.

## Comment on l'a su

En cassant volontairement une copie jetable du coffre, puis en relançant le
vérificateur. Trois chemins faux, réponse : « Coffre cohérent », code 0. La
même manipulation après correction : trois erreurs, code 1.

C'est la seule preuve qui vaille. Lire le code d'un contrôle dit ce qu'il
*prétend* faire ; le nourrir d'une faute connue dit ce qu'il fait.

## La leçon

Un contrôle vert répond à une question plus étroite qu'on ne croit. Avant de
s'y fier, se demander **quelles formes de la faute il ne verra pas** — et le
mesurer, plutôt que de le déduire.

Corollaire aggravant : la documentation affirmait que ces chemins étaient
contrôlés (§6 et §11 du contrat). Une promesse de contrôle inexacte est pire
que pas de contrôle du tout, parce qu'elle éteint la vigilance qui aurait
compensé.

## Application

- tester un contrôle en lui soumettant la faute qu'il doit attraper, à chaque
  fois qu'on élargit son périmètre ;
- écrire dans la documentation ce que le contrôle couvre **et** ce qu'il
  écarte volontairement — ici, les chemins du coffre parent, invisibles depuis
  le dépôt ;
- se méfier d'un vérificateur qui n'a jamais rien trouvé.
