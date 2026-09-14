# 2026-09-03 — Sous-types de mémoire

Application du point 3 de [[2026-09-03-comparaison-openviking]] : ouvrir dans
la mémoire un espace pour ce qui est **durable et transversal**, à côté des
notes de projet datées.

## Statut
🟢 Appliqué — contrat §6 et §10.3 réécrits, cinq notes durables créées.

---

## Décisions

- **Trois emplacements durables**, non datés : `profil-utilisateur.md` (un seul
  fichier, mis à jour sur place), `préférences/<sujet>.md`,
  `expériences/<sujet>.md`. Les notes de projet datées ne changent pas.
- **Non datés, délibérément.** Une préférence qui change se corrige ; elle ne
  s'empile pas en versions successives. Seules les notes de projet portent une
  date, parce qu'elles racontent une chronologie.
- **Règle de repli explicite** : dans le doute, écrire dans le projet. Une note
  de projet se distille plus tard vers `préférences/` ou `expériences/` ;
  l'inverse fait perdre le contexte.
- **Pas de `identity.md` ni de `soul.md`**, contrairement à OpenViking. Le ton
  et les principes de l'agent vivent déjà dans `IA/agents/assistant.md` ; les
  dupliquer créerait deux sources de vérité, ce que le contrat interdit.
- **Noms explicites plutôt que génériques.** `profil-utilisateur.md`, et non
  `profil.md` : le §6 exige l'unicité des noms de notes dans tout le **coffre
  parent**, et `profil.md` y entrerait presque sûrement en collision.

---

## Évidence

**Le manque était réel.** Avant ce changement, un fait stable — distribution
CachyOS, environnement KDE, orientation logiciel libre, niveau en codage —
n'avait aucun emplacement. Il finissait noyé dans une note datée d'un projet,
et se redemandait à chaque session.

**Ce qui a été écrit, et d'où ça vient** :

| Note | Origine |
| --- | --- |
| `profil-utilisateur.md` | déclaré par l'utilisateur en session |
| `préférences/licences-et-logiciel-libre.md` | trois refus déjà actés dans `IA/skills/` |
| `préférences/style-des-reponses.md` | déclaré par l'utilisateur |
| `expériences/frontmatter-du-coffre-obsia.md` | test conduit le 2026-09-03 |
| `expériences/index-maintenus-a-la-main.md` | trois erreurs trouvées le 2026-09-03 |

Le bloc « Infrastructure » de `profil-utilisateur.md` est explicitement marqué
**déduit des skills, non confirmé** : `proxmox.md` parle d'un hôte
hyperviseur, `conteneurs-docker.md` d'une VM Debian, `traefik.md` d'un reverse
proxy devant elle. Rien de tout cela n'a été dit par l'utilisateur ; la note le
signale et demande confirmation, plutôt que d'inscrire une supposition comme un
fait.

**Le générateur de sommaires a dû être ajusté.** Il désignait la note la plus
récente d'un dossier par sa date ; les dossiers durables n'en ont pas. Repli
ajouté sur la première note, et colonne renommée « Entrée représentative ».

---

## Interprétation

Le vrai gain n'est pas le fichier `profil-utilisateur.md` mais la **règle de
routage** du §6 : sans elle, les trois dossiers se rempliraient au hasard et
`préférences/` deviendrait un fourre-tout. Le tableau « ce qu'on a appris →
destination » est la partie qui devra tenir dans le temps.

Le risque connu est la dérive inverse : tout classer en « durable » parce que
c'est plus valorisant qu'une note de projet. D'où la règle de repli — le doute
va au projet, pas au durable.

---

## Questions ouvertes

- [ ] Confirmer ou corriger le bloc « Infrastructure » de
      `profil-utilisateur.md` : hôte Proxmox, VM Debian, Docker, Traefik.
- [ ] Faut-il une étape de distillation en fin de session — relire la note de
      projet et en remonter ce qui mérite `préférences/` ou `expériences/` ?
      C'est le point 6 de l'analyse, non traité à ce jour.

---

## Synthèse IA

OpenViking distingue neuf types de mémoire ; trois ont été repris, ceux qui
correspondent à un manque constaté. Les six autres — `entities`, `events`,
`trajectories`, `cases`, `identity`, `soul` — auraient été des dossiers vides
ou des doublons de fichiers existants.

Ce n'est pas de la prudence : un dossier vide dans un coffre est un coût, parce
qu'il faut décider à chaque écriture s'il s'applique.

## URLs sources

- Types de mémoire d'OpenViking :
  https://github.com/volcengine/OpenViking/blob/main/docs/en/concepts/02-context-types.md
