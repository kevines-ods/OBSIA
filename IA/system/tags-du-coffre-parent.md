# Tags du coffre parent — vocabulaire contrôlé

> **Statut : fait foi** pour les tags des notes du coffre parent (`SAVOIRS/`,
> `EN-VRAC/` et les notes classées vers `PROJETS/`, `DOCUMENTS/`,
> `PERSONNELS/`). Règle d'ensemble : `IA/system/VAULT-CONTRACT.md` §7.5.

## Principe

Les tags servent la **recherche**. Un tag hors liste, généré librement, ne
relie rien et surcharge : c'est ce qui est arrivé avec des tags ajoutés au fil
par des IA, sans cohérence. On utilise donc un **vocabulaire contrôlé** :

- une note ne porte que des tags de cette liste ;
- un tag nouveau s'ajoute **ici**, par patch soumis à revue — jamais improvisé
  dans une note ;
- cette liste vit dans OBSIA (versionné) pour que chaque harness et chaque
  LLM la retrouve, quel que soit le coffre : c'est la portabilité.

Écriture d'un tag : minuscules, sans espace. Le tiret est admis
(`home-assistant`, `reverse-proxy`). Les accents sont **écrits** (`réseau`,
`préférence`, `sécurité`) : un vocabulaire à moitié accentué se cherche deux
fois.

## Type d'une note (frontmatter `type`)

| Valeur | Note |
| --- | --- |
| `concept` | une connaissance — `SAVOIRS/` |
| `revue` | revue d'article, de blog, transcription — `DOCUMENTS/` |
| `projet` | note d'un projet — `PROJETS/` |
| `personnel` | contexte personnel — `PERSONNELS/` |
| `note` | toute autre note classée |

## Vocabulaire — tags existants

Regroupés par domaine pour la lisibilité ; c'est la liste qui fait foi, pas le
groupement.

| Domaine | Tags |
| --- | --- |
| Système | `linux`, `hardware`, `homelab`, `docker`, `proxmox`, `nas`, `stockage`, `sauvegarde` |
| Réseau | `réseau`, `reverse-proxy` |
| Domotique | `home-assistant` |
| IA | `ia`, `memory`, `transcription` |
| Logiciel | `software` |
| Personnel | `personnel`, `partage`, `préférence` |

## Tags candidats — **pas encore utilisables**

Ces mots reviennent souvent et feraient sans doute de bons tags. Ils ne sont
**pas** dans le vocabulaire tant que l'utilisateur ne les y a pas validés :
tant qu'un tag figure ici et non dans la table ci-dessus, un agent ne le pose
sur aucune note et l'outillage le compte comme hors vocabulaire.

> `obsidian`, `obsia`, `automation`, `git`, `github`, `conteneurs`,
> `sécurité`, `documentation`

Rencontrer l'un d'eux dans une note existante se **signale** — comme n'importe
quel tag hors liste. Le faire passer dans la table demande une validation de
l'utilisateur, par la procédure ci-dessous.

C'est volontairement rigide : « à valider au fil » revenait à autoriser
l'improvisation sous un autre nom, et l'improvisation est exactement ce que ce
registre existe pour empêcher.

## Procédure d'ajout d'un tag

1. Vérifier qu'aucun tag existant ne convient déjà (c'est le cas le plus
   fréquent : un « nouveau » tag est souvent un doublon).
2. Proposer l'ajout **dans la table du vocabulaire**, par patch soumis à revue,
   en le rangeant dans le domaine le plus proche. Ajouter un mot à la liste des
   candidats ne l'autorise pas : seule la table fait foi.
3. Une fois ajouté, l'utiliser dans les nouvelles notes ; le passage
   rétroactif sur les notes existantes reste optionnel.
