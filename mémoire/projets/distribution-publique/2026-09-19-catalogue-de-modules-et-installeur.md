# 2026-09-19 — Le coffre devient un catalogue, et le public un dérivé du privé

Le coffre décrivait *quoi* faire sans connaître de harness, mais restait taillé
pour une machine : Proxmox, Traefik, Docker, Arch, un coffre Obsidian nommé
`Mon coffre`. Il s'installait en entier ou pas du tout. Deux changements le
rendent distribuable : un **catalogue de modules** qu'on retient à la carte, et
un **miroir public dérivé** du dépôt privé.

## Statut

🟢 Appliqué et vérifié — `verifier_coffre.py`, `evaluer_routage.py`,
`generer_prompt.py` sortent en 0 sur le catalogue complet ; une installation
par copie réduite à `noyau,revue` a été construite, vérifiée et repassée par
les mêmes contrôles. `publier.py` n'a pas encore été confronté à un vrai clone
public.

---

## Le déclencheur

Demande de l'utilisateur : rendre son dépôt privé, en cloner une version
publique, et disposer d'un système qui « n'installe pas tout mais selon des
réponses du système ou de l'utilisateur ».

Trois arbitrages ont été posés d'emblée, parce qu'ils changeaient tout le
reste :

| Question | Réponse retenue |
| --- | --- |
| Qui fait foi entre privé et public ? | **Le privé.** Le public en est un export produit par script. |
| Comment n'installer que l'utile ? | **Les deux** — catalogue avec manifeste d'activation, *et* installation par copie. |
| Que peut faire l'installeur sur la machine ? | **Sonder puis confirmer.** |

## Décisions

- **Un module regroupe ce qui n'a de sens qu'ensemble.** Quatorze modules,
  déclarés dans `IA/system/modules/`. Le découpage ne suit pas les dossiers
  mais les **renvois entre skills** : `pdf` et `bureautique` se renvoient l'un
  à l'autre, `diagnostic-linux` garde `remediation-linux`, `conteneurs-docker`
  et `traefik` se partagent un diagnostic par couche. Séparer un couple ne
  donne pas une chaîne plus courte, il donne une chaîne cassée qui s'arrête
  sans rien dire.

- **`mise-en-ligne` a quitté `construction` pour un module `deploiement`.**
  Le vérificateur l'a imposé : un skill de `construction` disait de charger
  `conteneurs-docker`, d'un module que `construction` n'entraînait pas. Fondu
  dans `construction`, il aurait imposé Docker à qui construit un outil en
  ligne de commande.

- **Quatre formes de sonde, et pas une cinquième** : `commande:`, `fichier:`,
  `distribution:`, `parent:`. Aucune n'exécute de commande arbitraire et aucune
  n'ouvre le réseau. On installe un catalogue qu'on n'a pas encore lu : un
  fichier du catalogue qui déclencherait du code en serait le vecteur.

- **Une sonde ne décide jamais seule.** Elle constate que `docker` est
  installé ; elle ne sait pas si l'utilisateur veut gérer des conteneurs. Elle
  propose un défaut, la question tranche. Un module sans sonde — `documents`,
  `revue`, `recherche-web` — n'est pas mal fait : il est indécidable depuis la
  machine, et le dire vaut mieux que le deviner.

- **Deux modes d'installation, et la différence porte sur les frontmatters.**
  En place, rien n'est réécrit : les fichiers écartés restent sur le disque,
  seuls les fichiers générés se réduisent, et `git checkout -- IA` remet tout.
  En copie, les déclarations d'agents sont réduites, parce que les fichiers
  manquent réellement et qu'un agent qui les déclarerait ferait échouer le
  vérificateur de la cible.

- **Absence de profil = catalogue complet.** C'est l'état du dépôt de
  distribution et celui sous lequel la CI vérifie. Sans cette convention, la CI
  n'aurait contrôlé qu'une installation particulière, et les modules écartés
  auraient pourri sans que rien ne le signale.

- **Le nom du coffre parent devient une convention d'écriture.** `Mon coffre/`
  reste ce qu'on écrit partout dans le dépôt ; le nom réel vit dans
  `obsia.local.yml`. Un dépôt public ne peut pas connaître le nom que chacun
  donne à son coffre, mais il lui en faut un pour en parler — sans quoi chaque
  skill inventerait le sien.

## Ce que le vérificateur a appris à voir

Trois contrôles ont dû apprendre à distinguer le catalogue de son installation,
et c'est la première installation réduite qui l'a montré — pas la relecture.

- **La règle d'unicité des noms (§6) a attrapé une collision** entre le module
  `sauvegardes` et le skill du même nom. Renommé `controle-des-sauvegardes`.
  La leçon vaut pour tout module à venir : son nom vit dans le même espace de
  noms que les notes.

- **Chemin cité, agent nommé, module sans déclaration** : ces trois contrôles
  échouaient en masse sur une copie réduite, parce que le contrat cite
  `IA/skills/cron/cron.md` que personne n'est obligé d'installer. Ils ne sont
  plus bloquants quand `obsia.local.yml` porte `mode: copie` — et ils le
  restent partout ailleurs, y compris en mode « en place », où rien n'est
  retiré du disque. L'intégrité du catalogue se vérifie là où le catalogue est
  entier.

- **Une attente de routage sur un skill écarté est sans objet, pas en échec.**
  Mais seulement en installation réduite : sans profil, un skill absent du
  registre reste une erreur, sinon une faute de frappe passerait inaperçue.

## Ce qui reste ouvert

- `publier.py` n'a tourné que contre un clone factice. Le premier vrai passage
  dira si le contrôle de fuite crie trop ou pas assez.
- Le sens unique privé → public se paie : une correction proposée sur le public
  se reporte à la main. C'est un coût accepté, pas un oubli.
- Le découpage en quatorze modules n'a jamais été confronté à quelqu'un d'autre
  que son auteur. C'est la seule manière de savoir s'il tombe au bon endroit.
