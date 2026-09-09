# 2026-09-03 — Comparaison OBSIA / OpenViking

Point d'entrée du projet : ce qu'est OpenViking, ce qu'OBSIA lui a pris, ce
qu'il a refusé de lui prendre. Les sept observations brutes sont dans
[[2026-09-03-openviking-observations]] ; chaque piste retenue a sa propre note
de mise en œuvre, listées plus bas.

## Statut
🟢 Analyse close. Six des sept pistes ont été appliquées entre le 2026-09-03 et
le 2026-09-05 ; la septième est écartée. Découpée le 2026-09-09 : elle pesait
15 886 caractères, plus du double du seuil de `cloture-de-session`.

---

## Ce qu'est OpenViking

`volcengine/OpenViking` — « base de données de contexte auto-évolutive pour
agents IA ». Volcengine (ByteDance), AGPLv3, ~10k étoiles en 1,5 mois. Serveur
Rust + Python, index vectoriel, CLI `ov`, studio web, déploiement Docker/Helm.

Le point commun avec OBSIA est frappant : OpenViking **refuse lui aussi le
modèle RAG « soupe de vecteurs »** et organise le contexte comme un système
de fichiers hiérarchique, adressable, lisible. Il découpe le contexte en
trois types — **Resource / Memory / Skill** — exactement la trichotomie
qu'OBSIA appelle ressource externe / mémoire / skill.

La divergence est tout aussi nette : OpenViking est une **infrastructure
serveur** (AGFS, index vectoriel, files asynchrones, LLM appelé à l'écriture
pour résumer). OBSIA est un **contrat en Markdown** que n'importe quel harness
lit. OpenViking a besoin d'être déployé ; OBSIA a besoin d'être lu.

Conséquence : on ne copie pas son architecture, on copie **ses conventions de
fichiers**, qui sont sa vraie trouvaille.

---

## Interprétation — ce qui valait la peine d'être copié

Classé à l'époque par rapport valeur / effort. Rien n'exigeait de serveur,
d'index vectoriel ni d'appel LLM : ce sont des conventions de fichiers. La
colonne de droite dit ce qu'il en est advenu — le détail vit dans la note de
mise en œuvre, pas ici, pour que les deux ne divergent pas.

| # | Piste | Effort estimé | Suite donnée |
|---|---|---|---|
| 1 | Descriptions « quoi + quand + quand pas » | très faible | [[2026-09-03-descriptions-de-skills]] |
| 2 | `sommaire.md` enrichi = un vrai L1 | faible | [[2026-09-03-sommaires-enrichis]] |
| 3 | Sous-types de mémoire | faible | [[2026-09-03-sous-types-de-memoire]] |
| 4 | Validation du coffre en CI | moyen | [[2026-09-03-verification-du-coffre]] |
| 5 | Skill-dossier avec `references/` | moyen | [[2026-09-03-skill-dossier-et-crochet]] |
| 6 | Archive **et** distillation en fin de session | moyen | [[2026-09-03-couches-de-memoire-et-cloture]] |
| 7 | Gabarits de prompt hors du code Python | moyen | **jamais reprise** — ci-dessous |

### La piste 7, restée ouverte

Le texte du prompt système est **codé en dur** dans `construire_prompt()` de
`scripts/generer_prompt.py` : modifier une consigne, c'est modifier du Python.
OpenViking en fait des gabarits YAML versionnés, éditables sans toucher au
code.

Classée « gain faible » dès l'analyse, et toujours estimée telle : le coffre a
un seul agent et un seul prompt système, donc la mutualisation que des
gabarits apporteraient n'a rien à mutualiser. À rouvrir le jour où un second
agent existera — pas avant.

---

## Ce qu'il ne faut PAS copier

- **L'index vectoriel, AGFS, le serveur Rust, Helm, Docker.** Ils contredisent
  frontalement la promesse du README d'OBSIA : « pas de base de données, pas de
  format propriétaire ; le coffre se lit et s'édite à la main ». Un coffre
  Obsidian n'a pas besoin d'être déployé.
- **La génération LLM des L0/L1 à l'écriture.** Coûteuse, asynchrone, elle
  exige un serveur et des files d'attente. OBSIA extrait les mêmes résumés de
  façon déterministe, depuis le titre et le statut déjà écrits dans ses notes.
- **Multi-tenant, ACL, chiffrement, quotas, WebDAV.** Réponses à un problème
  d'hébergeur multi-clients. OBSIA a un utilisateur.
- **Les 24 fichiers d'API et le SDK.** OBSIA n'expose pas d'API : il expose des
  fichiers.
- **`identity.md` / `soul.md`.** Techniquement copiables, mais ils décrivent le
  ton et la personnalité de l'assistant — ce qu'OBSIA place déjà, et mieux,
  dans `IA/agents/assistant.md`. Les dupliquer créerait deux sources de vérité,
  ce que le contrat interdit.

---

## Licence

OpenViking : **AGPLv3** pour le projet principal, Apache 2.0 pour `crates/ov_cli`
et `examples/`. OBSIA : **AGPL-3.0-or-later**.

Aucun obstacle : AGPLv3 → AGPLv3 est identique, et Apache 2.0 → AGPLv3 est une
compatibilité admise dans ce sens uniquement — y compris pour reprendre du
texte de documentation, à condition de citer la source (§8).

Réserve : les conventions décrites ici sont des **idées d'organisation**, pas
du code. Les reprendre ne crée pas d'œuvre dérivée. Copier littéralement un
fichier YAML de gabarit, si.

---

## Synthèse IA

OpenViking et OBSIA ont eu la même intuition — le contexte d'un agent est une
arborescence de fichiers, pas un nuage de vecteurs — et l'ont poussée à deux
échelles opposées : une infrastructure serveur d'un côté, un contrat Markdown
de l'autre.

Ce qu'OBSIA a de meilleur, OpenViking ne l'a pas : un contrat unique qui fait
foi, une séparation nette agent / skill / MCP, et l'indépendance vis-à-vis de
tout harness.

Ce qui manquait à OBSIA tenait en une phrase : **ses index savaient où sont
les choses, pas ce qu'elles valent.** Ni `sommaire.md` ni `skills-index.md` ne
permettait de décider sans ouvrir. La couche L0/L1 était la réponse, copiable
sans une ligne d'infrastructure : les résumés étaient déjà dans les notes, il
suffisait de les remonter.

Second manque, plus discret : **le contrat n'était vérifié par rien.** Un dépôt
dont toutes les règles reposent sur la bonne volonté du lecteur dérive. C'est
la piste qui a le mieux vieilli — elle a fini par trouver des erreurs qu'aucune
relecture humaine n'avait vues.

---

## URLs sources

Regroupées dans [[2026-09-03-openviking-observations]], avec l'évidence
qu'elles étayent.
