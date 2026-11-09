# secrets-solutions.md — comment appliquer le §4 du contrat

> **Statut : proposition validée pour le stockage machine (§4), l'emplacement de
> la clé et l'audit (§9 points 1, 2 et 4). Deux points restent ouverts : la
> couche famille et la grammaire de désignation.** Rédigée par l'agent
> `batisseur`, session d'équipe Homelab du 2026-10-11, **Étape 2** du plan
> (solutions techniques), amendée par l'agent `assistant` le 2026-10-16
> (magasin machine : `SOPS`+`age`) puis par l'agent `administrateur` le
> 2026-11-03 (licences vérifiées à la source, emplacement et sauvegarde de la
> clé, audit en signalement). Elle **applique le §4** de
> `VAULT-CONTRACT.md` : les principes n'ont pas de note à eux — le §4 les
> porte et ne se recopie nulle part (§5). Cette note ne fixe donc aucune
> règle, elle propose *comment* appliquer le §4.

## 0. Ce que la session demande

| # | Question (session §2 et §3) | Axe |
| --- | --- | --- |
| 1 | Comment **désigner** les secrets ? | Désignation |
| 2 | Où **stocker** les valeurs (dossier protégé ? `SOPS`+`age` ? `Vault` ?) ? | Stockage |
| 3 | Comment les **utiliser** (stockage, désignation, utilisation — §3) ? | Utilisation |
| 4 | Comment **auditer** automatiquement l'absence de secrets ? | Audit |
| 5 | Comment **masquer** les IPs / noms de domaine en export ? | Masquage |

## 1. Critères de choix (écrits d'avance)

Repris de `choix-de-la-stack`, élargis par la finalité Homelab déjà validée :

| Critère | Source | Ce qu'on refuse |
| --- | --- | --- |
| Licence libre | méthode | un outil verrouillé |
| Souveraineté — aucun tiers non choisi | **F3** | un service qui envoie un secret chez un fournisseur |
| Sobriété — pas un service de plus | **F4** | un démon à faire tourner, sauvegarder et surveiller |
| Coût d'entretien | méthode | un composant qui rouille faute de mains |
| Reprise en main réelle | méthode | une boîte noire qu'on ne sait pas réparer |
| Sauvegarde 3-2-1 du magasin | `sauvegardes` | un magasin non sauvegardé = perte totale |
| Ouverture à la famille | **F2** | un schéma que seul l'auteur sait ouvrir |

## 2. Ce qui existe déjà dans OBSIA (à ne pas refaire)

L'inventaire change la réponse : **l'outillage d'audit existe déjà**, à deux étages.

| Élément | Rôle | Frontière |
| --- | --- | --- |
| `VAULT-CONTRACT.md` §4 | la règle — **lue au contrat**, jamais recopiée ailleurs (§5) | règle |
| `scripts/garde_secrets.py` | **pre-commit du dépôt de données** : refuse, dans ce qu'un commit *ajoute*, une valeur en forme de secret, un jeton isolé à forte entropie, un bloc base64 | **mémoire privée** |
| `scripts/publier.py` (contrôle de fuite) | bloque à la **publication** : courriel, IP privée, nom d'hôte interne | **frontière publique** |
| `skills/configuration-mcp.md` | les secrets des MCP vivent en **variables d'environnement**, hors dépôt | usage |
| Leçon `0-MEMOIRES/administrateur/expériences/un-secret-se-cache-dans-ce-qui-le-decrit.md` | une valeur retirée reste ailleurs : rotation, purge des exports, régénération des index | méthode |

**Conséquence décisive.** Le garde ne confond **pas** les deux frontières : il laisse
passer une IP privée et un nom d'hôte interne dans la mémoire privée (légitimes),
et c'est `publier.py` qui les masque vers le public. Toute solution ci-dessous
**respecte cette séparation** — c'est aussi la réponse la plus juste à la question 5.

## 3. Désignation — nommer sans révéler

| Façon | Exemple | Révèle la valeur ? | Portable hors Obsidian | Désigne l'emplacement du magasin | Verdict |
| --- | --- | --- | --- | --- | --- |
| Lien Obsidian | `[[Credentials — Telegram]]` | non | non | non | **à éviter** : crée une note qui *attire* la valeur |
| Nom de variable | `TELEGRAM_BOT_TOKEN` | non | oui | non | bon pour **l'usage**, pas pour dire **où** |
| Chemin canonique | `secret/homelab/telegram/bot/token` | non | oui | **oui** | **recommandé** |
| Chemin + empreinte | `secret/…` + `sha256:3f9a1c2e` | non | oui | oui | recommandé : prouve une rotation sans révéler |

**Proposition — une grammaire stable, une seule :**

```
secret/<cible>/<objet>/<clé>      minuscules, séparateur « / », sans espace
  cible : un rôle, jamais un nom d'hôte ni un alias
          hyperviseur | stockage | messagerie | nuage | vpn
  objet : api | bot | db | admin | …
  clé   : token | password | key
```

- Une note n'écrit **que** le chemin (où) et, si utile, le **nom de variable** (comment
  c'est exposé à l'agent) — jamais la valeur.
- À côté du chemin, une **empreinte** (`sha256` tronqué à 8 caractères hexadécimaux)
  permet de vérifier que le secret en place est toujours celui qu'on croit, et de
  **dater une rotation**, sans jamais montrer la valeur. C'est le prolongement direct
  de la leçon « un secret se cache dans ce qui le décrit ».

**Exemple (aucune valeur) :**

> Le jeton du bot Telegram vit sous `secret/homelab/telegram/bot/token`
> (empreinte `sha256:3f9a1c2e`). Le script d'alerte le lit dans la variable
> `TELEGRAM_BOT_TOKEN` ; il n'est écrit dans aucune note.

## 4. Stockage — où vit la valeur

| Candidat | Licence | Service en plus ? | Chiffré au repos | Désignation = chemin | Entretien | Famille | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Dossier protégé + `.env` en `0600` | aucun logiciel | non | non (permissions FS) | non | très faible | moyen | **repli**, pas la cible |
| `pass` (password-store, GPG) | libre — **GPL-2.0+** | non (CLI seul) | oui (GPG) | **oui** | faible, mais clé GPG à gérer | faible (partager la clé GPG) | écarté : GPG ajoute une clé à créer, sauvegarder et faire tourner, sans bénéfice ici |
| **`SOPS` + `age`** | libre — **MPL-2.0** (`sops` v3.13.3) / **BSD-3-Clause** (`age` v1.3.2) | non (CLI seul) | oui (`age`) | non (clé dans un YAML) | **plus faible** : une seule paire de clés `age`, pas de trousseau GPG | faible/moyen | **recommandé — couche machine** |
| HashiCorp `Vault` | **BUSL-1.1** (IBM, ≥ 1.15.0) | **oui** (serveur) | oui | via API | **élevé** | moyen | **écarté** (F4) |
| **KeePassXC** (`.kdbx`) | libre — **GPL-2.0+** (2.8.0) | non (fichier) | oui | non | faible | **bon** | **recommandé — couche humaine** |
| Vaultwarden | libre — **AGPL-3.0** | **oui** | oui | via UI/API | moyen | **bon** | à évaluer **quand F2 arrive** — l'AGPL se déclenche à l'**accès réseau**, pas à la distribution : à ne pas exposer hors du LAN sans le savoir |

*Licences vérifiées au dépôt le 2026-11-03 (`LICENSE`/`COPYING` lus à la source,
`license.spdx_id` de l'API GitHub), versions = dernier tag publié ce jour-là —
skill `verification-aux-sources`. La version d'octobre était « à confirmer » :
la session n'avait pas de réseau.*

**Décision — deux couches ; une clé n'a qu'un seul lieu :**

1. **Couche machine** (agents, conteneurs, MCP) : **`SOPS`+`age`**, retenu sur
   `pass` — `age` se limite à une paire de clés à sauvegarder, sans trousseau
   GPG ni agent GPG à faire tourner, ce qui réduit l'entretien (critère
   méthode). Les fichiers chiffrés vivent dans le dossier de configuration
   d'OBSIA (§5) : le fichier commun, et le fichier propre à un service qui
   saisit lui-même des secrets ; la désignation du §3
   (`secret/<cible>/<objet>/<clé>`) sert de clé dans ces YAML, même si elle ne
   pointe plus vers un chemin de magasin comme avec `pass`.
2. **Couche humaine** (l'utilisateur, puis la famille — F2) : un fichier
   **KeePassXC**. `Vaultwarden` n'entre que si F2 arrive vraiment, et il compte alors
   comme **un service de plus** (à évaluer contre F4).

**Emplacement et sauvegarde — décidé par Kev le 2026-11-03 :**

- La **clé** `age` (privée) vit **sur la VM `ia`**, dans
  `~/.config/sops/age/keys.txt`, en `0600` — **hors** du coffre parent,
  **hors** du dépôt OBSIA, jamais dans un *worktree*, jamais dans un dossier
  suivi par Git ou par une synchronisation.
- Les **fichiers chiffrés** `SOPS` peuvent, eux, être versionnés avec
  l'infra : c'est tout l'intérêt de `SOPS` par rapport à `pass`.
- La clé **entre dans la sauvegarde 3-2-1** (`sauvegardes`) — une clé perdue,
  ce sont tous les fichiers chiffrés qui deviennent illisibles. Elle ne passe
  **pas** par `restic-cachyos` (elle n'est pas sur CachyOS) : `ia` est un
  invité Proxmox, donc son disque relève du `vzdump --all 1` de la campagne
  USB, comme les autres invités (`Homelab — sauvegardes`).
- **Preuve à faire après création de la clé** : une sauvegarde jamais
  restaurée est une hypothèse. Restaurer `~/.config/sops/age/keys.txt` depuis
  le snapshot PBS, et le consigner — ne pas se contenter de croire que `--all`
  l'englobe.

## 5. Utilisation — se servir d'un secret sans le faire sortir

**Où vit le magasin** (le contrat, §4, le nomme par son rôle ; le chemin exact est
ici, hors du noyau, pour qu'il ne parte pas dans les `AGENTS.md` engendrés) :

| Élément | Emplacement | Droits |
| --- | --- | --- |
| Fichier chiffré des secrets | `~/.config/obsia/secrets.enc.yaml` | `0600` |
| Règles de chiffrement | `~/.config/obsia/.sops.yaml` (`path_regex: .*`, clé `age` publique) | `0600` |
| Clé privée `age` | `~/.config/sops/age/keys.txt` | `0600` |

**Fichier propre à un service** (décision de Kev, 2026-11-09) — pour un service
qui *saisit* des secrets (une interface où l'on entre une clé) :

| Élément | Emplacement | Droits |
| --- | --- | --- |
| Fichier chiffré d'un service | `~/.config/obsia/<service>.secrets.enc.yaml` | `0600` |

- **Une clé n'a qu'un lieu.** Le fichier du service ne porte que ce que le service
  saisit ; le fichier commun, ce que l'utilisateur range avec `sops`. Le contrôle
  revient au **lanceur** (le script qui appelle `sops exec-env`, et qui détient la
  clé privée) : avant de lancer, il compare les **noms** des deux fichiers ; un nom
  présent dans les deux → il refuse de lancer et nomme la variable et les deux
  fichiers, jamais la valeur. Le service, lui, ne voit qu'un environnement et ne
  peut pas faire ce contrôle.
- **Il ne s'édite que par le service.** Le service le réécrit **entier** depuis ce
  qu'il a reçu au démarrage plus la saisie, chiffré avec la seule clé `age`
  **publique** : sans clé privée, il ne peut pas fusionner une entrée ajoutée à la
  main, qui serait perdue. On n'y range rien avec `sops`.
- **Création à l'installation** : un geste unique de l'utilisateur crée le fichier
  du service, chiffré et vide à une variable près — un **témoin** non secret
  (`OBSIA_FICHIER_DE_SERVICE=1`) que le service réécrit toujours. Sans fichier,
  `sops exec-env` ne lance rien : l'installation le dit et donne la commande.
- **Aucune écriture sans injection.** Témoin absent de l'environnement (fichier non
  injecté, `sops` absent) : le service refuse toute saisie — jamais un fichier
  réécrit vide ou amputé, jamais une valeur en clair à la place.
- **Écriture sûre** : chiffrement par flux (aucun clair sur disque, même
  temporaire), puis fichier temporaire et `rename` — une coupure ne laisse jamais
  un fichier tronqué.
- **Injection** : `sops exec-env` au démarrage, le fichier commun puis celui du
  service. **Sauvegarde** : il entre dans la 3-2-1 comme la clé `age` (§4).
- **Ce que ça protège, et pas plus** : aucune valeur en clair sur disque, et un
  fichier commun que le service n'écrit jamais. Tant que le service tourne sous
  le compte qui détient `~/.config/sops/age/keys.txt`, il **peut** lire la clé
  privée et déchiffrer le fichier commun : l'isolation demande un utilisateur
  système dédié (geste de l'utilisateur, `sudo`), étape ultérieure.
- Vérifié le 2026-11-09 (`sops` 3.13.3, clé jetable) : `sops --encrypt --age
  <publique>` chiffre sans clé privée, et `sops exec-env` injecte le résultat.

Une désignation `secret/<cible>/<objet>/<clé>` nomme une entrée, jamais un chemin :
`<cible>` est un rôle (hyperviseur, stockage, messagerie, nuage, vpn…), jamais un
nom d'hôte ni un alias de machine.

Règles, dans l'ordre :

1. **Jamais sur la ligne de commande** : elle finit dans `history`, dans `ps` et
   dans les journaux.
2. **Jamais recopié** dans une note, un carnet, un journal ou un message — §4.
3. **Injection par flux ou par environnement**, jamais par argument :
   `sops exec-env`, `--env-file`, `EnvironmentFile=` de systemd, ou variable
   d'environnement posée par le harness (cf. `configuration-mcp`).
4. **Ne jamais afficher** : au plus, calculer une **empreinte** pour comparer.
5. Un secret lu par un agent est **utilisé et oublié** : il ne reste pas dans la
   séance, il n'entre pas dans un résumé.

**Exemples (aucune valeur n'y figure) :**

- *Registre de conteneurs* : `sops exec-env secrets.enc.yaml 'docker login --password-stdin …'`.
- *Base Nextcloud* : le mot de passe est fourni au conteneur par fichier ou variable
  d'environnement, jamais en `-p`.
- *Alerte Telegram* : le script lit `$TELEGRAM_BOT_TOKEN` dans son environnement ;
  c'est le harness (hors dépôt) qui le pose, l'agent ne le voit pas.
- *Appel réseau* : le coffre n'a **aucun accès réseau implicite** (§4) ; un secret
  qui sert à un appel sortant est **demandé explicitement**.

## 6. Audit — deux étages, et ce qui manque

| Étage | Frontière | Outil existant | Ce qui manque |
| --- | --- | --- | --- |
| 1 | mémoire privée | `garde_secrets.py` (pre-commit) | il ne voit que ce qu'un commit **ajoute** ; un secret **déjà présent** — ou posé hors pre-commit — passe |
| 2 | public | `publier.py` (contrôle de fuite) | pas de **test** qui prouve qu'une IP privée / un courriel / un hôte interne d'une note ne sortent pas dans l'artefact publié |

**Propositions :**

1. **Étage 1 — un scan intégral récurrent, en lecture seule.** Une **tâche
   planifiée** (registre `IA/tâches/`, skill `cron`) relance le garde sur *tout* le
   dépôt de données et sur le coffre parent, pas seulement sur le diff. Elle
   **signale**, elle ne corrige pas : la correction d'un secret déjà présent appelle
   une **rotation** (la leçon l'exige — retirer la valeur ne suffit pas).
2. **Étage 2 — un test du contrôle de fuite** (skill `plancher-qualite`) : une note
   piégée portant une IP privée, un courriel et un hôte interne, puis vérification
   que l'artefact publié ne les contient pas.
3. **Option à évaluer** : un scanner de secrets sur l'**historique Git** d'OBSIA
   (`gitleaks`, `detect-secrets`) pour trouver un secret jamais retiré de
   l'historique. **Non vérifié dans cette session** (réseau indisponible).

**Responsabilités (`session §3`) :** celui qui écrit un secret ne l'audite pas — le
garde le fait, par code. **Qui corrige** : l'utilisateur pour la **rotation** (lui
seul détient la valeur), l'agent pour la **purge** et la **régénération des index**.

## 7. Masquage — masquer à la frontière, pas dans les notes

**Principe : le coffre garde la vérité ; le masquage se fait au moment où l'on
sort du coffre.**

*Ce principe n'est plus une proposition : il est au contrat depuis le
2026-11-03. Le §9 amendé autorise le carnet à porter adresse IP privée, nom
d'hôte interne, URL interne et identifiant, et réserve ces quatre choses à la
sortie — PR, note publiée, dépôt produit. Le §7.1 a suivi, et `~/.config/obsia/noms-interdits`
ne garde que la frontière publique.*

- **À rejeter** : écrire `nextcloud.{domaine}.fr` *dans la note*. Cela dégrade la
  note, pousse à deux vérités (celle de la note, celle du réel) et ne protège rien
  tant que la note reste privée.
- **À faire** : `publier.py` masque/bloque déjà IP privée, courriel, hôte interne.
  On étend le **vocabulaire de substitution** à l'usage interne
  (`<domaine>`, `<ip-lan>`, `<chemin-nas>`) et on l'applique **au moment de
  générer** un artefact public, avec un **preview** avant écriture (§7.4).
- **Rapports et alertes** (Telegram, résumés, messages) : toute valeur rencontrée
  est masquée par défaut — c'est déjà la règle du §4 ; le masquage n'est pas une
  option d'export, c'est le régime par défaut de tout ce qui sort.
- **Exports publics** (ex. `git-hub`) : IP publiques et noms de domaine publics
  masqués **eux aussi** par défaut.

## 8. Architecture cible

```
   Utilisateur ──► KeePassXC (.kdbx)           [couche humaine]
                      │  (plus tard, si F2 : Vaultwarden)
   Agents / services ──► SOPS + age            [couche machine] — SEUL dépôt des valeurs
                           │  injection : sops exec-env / EnvironmentFile
                           ▼
                       scripts, conteneurs, MCP (harness, hors dépôt)

   Garde :  garde_secrets.py (mémoire privée)  +  publier.py (frontière publique)
```

## 9. Décisions restant à prendre (Administrateur / Visionnaire)

1. ~~Magasin machine~~ — **tranché : `SOPS`+`age`** (décision utilisateur, 2026-10-16).
2. ~~Emplacement et sauvegarde~~ — **tranché le 2026-11-03** : la clé `age` vit sur la VM `ia`, dans `~/.config/sops/age/keys.txt` en `0600`, hors du coffre et hors d'OBSIA, et elle **entre dans la 3-2-1** par le snapshot PBS de la VM (§4).
3. **Couche famille** : KeePassXC maintenant, Vaultwarden quand F2 arrive ?
4. ~~Audit~~ — **tranché le 2026-11-03 : oui, en signalement seulement.** La tâche planifiée relance le garde sur **tout** le dépôt, pas sur le diff d'un commit ; elle **signale** et ne bloque jamais — une adresse IP privée et un nom d'hôte interne restent légitimes dans la mémoire privée.
5. ~~Désignation~~ — **tranché le 2026-11-09** : la grammaire `secret/<cible>/<objet>/<clé>` est retenue et passe dans le contrat (§4, bloc `regle-secrets`), donc dans chaque `AGENTS.md` engendré. Le bloc ne pouvait pas nommer le chemin du magasin : `chemins_absolus` interdit toute racine absolue, `~/` comprise, dans la règle copiée ; le chemin exact vit au §5 de cette note.

## 10. Réserves (honnêteté des sources)

1. **Réseau indisponible à la rédaction initiale** : les MCP `searxng` et l'outil de
   lecture d'URL ont échoué (erreur de transport). Les faits de **licence** ont été
   vérifiés depuis, le 2026-11-03, au dépôt et par `verification-aux-sources`
   (§3) — y compris la correction `Vaultwarden` : **AGPL-3.0**, pas GPL-3.0.
   Restent non vérifiés à la source : les options exactes de `sops exec-env` et
   la page `man` des *credentials* systemd.
2. Cette note propose ; elle ne tranche que les points 1, 2 et 4 du §9. La règle reste le §4 du contrat.
