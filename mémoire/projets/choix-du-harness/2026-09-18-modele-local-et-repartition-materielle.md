# 2026-09-18 — Modèle local : c'est le contexte qui décide, pas la quantification

La question posée était « Qwen3-8B en Q6 ou en Q8 ? ». La réponse est qu'aucune
des deux ne convient, et que la quantification est la plus petite variable du
problème. Ce qui tranche, c'est la taille du contexte qu'OBSIA impose avant
d'avoir commencé à travailler.

## Statut

🟡 Analyse faite, **rien d'installé, rien mesuré sur machine**. Un script
d'épreuve est livré avec cette note ; aucun modèle n'y est encore passé.

---

## Décisions

- **Qwen3-8B est écarté comme agent pilote.** Son contexte natif est de 32 k
  tokens ; le coffre en consomme davantage avant la première action utile. Ce
  n'est pas un jugement de qualité, c'est une contrainte arithmétique.
- **Q6 ou Q8 n'est pas le bon curseur.** L'écart entre les deux est marginal
  face à l'écart entre deux tailles de modèle. À modèle fixé, prendre `Q6_K` et
  dépenser la mémoire économisée en contexte.
- **Spark-X2.5-4B devient le candidat à éprouver.** Contexte natif de 1 M
  tokens, outillage agentique, Apache 2.0 — conforme aux valeurs de
  [[profil-utilisateur]]. Publié le 2026-09-01 : **candidat, pas retenu**.
- **Vulkan plutôt que ROCm** sur la carte du poste de travail (RDNA 4). Plus
  rapide d'après les mesures publiées, et sans pile logicielle à installer.
- **Répartition par machine, décalquée du partage entre harness** : les tâches
  planifiées tournent sur la VM sans carte graphique, en processeur seul ; le
  poste de travail sert le travail interactif lourd.
- **Une tâche planifiée se sécurise en fermant son chemin d'écriture**, pas en
  réduisant le nombre de skills qu'elle charge. Voir l'interprétation.
- **`revue-des-notes-du-coffre` ne sera pas confiée à un petit modèle en
  l'état** : elle sera d'abord transformée en productrice de previews.
- **`scripts/evaluer_modele.py` est livré** : sept pièges du contrat, joués
  contre un point d'accès compatible OpenAI.

## Évidence

Trois natures distinctes, à ne pas confondre.

**Mesuré ici, sur le dépôt** (`wc -c`, le 2026-09-18) :

| Ce qui est chargé en permanence | Octets |
| --- | --- |
| `CLAUDE.md` | 516 |
| `IA/system/VAULT-CONTRACT.md` | 43 286 |
| les trois index générés | 20 195 |
| **total** | **63 997** |

Soit de l'ordre de **19 000 tokens** — estimation par comptage de caractères,
pas une mesure au tokenizer. En y ajoutant le fichier de l'agent, deux ou trois
skills et les définitions d'outils MCP, une session s'ouvre autour de 30 à 35 k
tokens. Le prompt réduit que produit `scripts/generer_prompt.py` pèse 17 428
octets : il porte les index et la méthode, **pas le contrat**.

**Lu dans la documentation de l'éditeur**, non répliqué :

- Spark-X2.5-4B — 4 milliards de paramètres, contexte natif de 1 048 576
  tokens, plus de 200 langues, Apache 2.0. Architecture d'attention hybride :
  une couche d'attention complète pour trois couches à fenêtre glissante. [1][2]
- Scores annoncés, en mode « thinking » : IFEval 93,0 · IFBench 75,0 ·
  BFCL-V4 65,1 · τ²-bench 75,1 · MCP-Atlas 54,6. [1]
- Versions minimales : llama.cpp **b10828+**, Ollama **v0.34.1+**. En dessous,
  l'architecture `spark2_5` n'est pas reconnue. [3]

**Mesuré par des tiers**, sur la carte exacte du poste :

- ROCm couvre `gfx1200` depuis la 7.2 (janvier 2026), formalisé en 10.0 (août
  2026). Mais le backend **Vulkan de llama.cpp est plus rapide que son propre
  backend ROCm** sur RDNA 4 — de +3 % à +20 % selon le modèle et le test. [4][5][6]

## Interprétation

**Le coffre est lourd en contexte, et c'est une conséquence de sa qualité.**
Le contrat fait 43 Ko parce qu'il énonce ses raisons plutôt que ses seules
règles — c'est ce qui le rend relisable, et c'est ce qui le rend coûteux. On ne
peut pas à la fois vouloir un contrat qui s'explique et un modèle qui tient
dans 32 k tokens. Le choix a été fait il y a longtemps ; il se paie ici.

**Restreindre une tâche à un seul skill supprime une erreur sur deux.**
L'erreur de routage disparaît — le modèle ne peut plus charger le mauvais
skill. L'erreur d'exécution reste entière : il peut toujours écrire au mauvais
endroit ou inventer un nom d'agent, puisque le contrat est chargé quoi qu'il
arrive. Ce qui supprime réellement le risque est ailleurs, et le coffre le
faisait déjà sans le nommer : `revue-hebdomadaire-du-coffre` dit « ne corrige
rien de toi-même, prépare un patch ». Le modèle ne casse rien parce qu'on lui a
retiré le moyen de casser, pas parce qu'on lui a fait la leçon.

**Le classement des trois tâches suit cette logique, pas la difficulté :**

| Tâche | Verdict pour un petit modèle | Ce qui décide |
| --- | --- | --- |
| `revue-hebdomadaire-du-coffre` | ✅ à tenter en premier | écriture déjà interdite par la tâche ; le pire échec est un rapport médiocre |
| `revue-des-notes-du-coffre` | ⚠️ à transformer d'abord | déplace des fichiers dans un coffre parent **sans Git** |
| `revue-mensuelle-des-lecons` | ❌ jamais | le jugement (confirmer / annuler) est toute la tâche |

La transformation de la deuxième ne demande aucune règle nouvelle : le §7.4
impose déjà un preview consigné dans `_maintenance/`. Il suffit d'arrêter la
tâche là. Le modèle propose, l'utilisateur applique.

**Le matériel arrange les choses plus qu'il ne les contraint.** La VM dédiée à
l'IA n'a pas de carte graphique, et le poste qui en a une n'est pas toujours
allumé. Un modèle de 4 milliards de paramètres en Q6 tient dans 3,3 Go et
tourne en processeur seul à une vitesse basse mais suffisante pour un travail
qui s'exécute sans témoin. Une tâche qui se déclenche le lundi à 9 h n'a pas
besoin d'être rapide ; elle a besoin de se déclencher. Faire dépendre ces
tâches d'une machine éteinte les aurait fait échouer en silence.

## Synthèse IA

Le motif se répète d'une note à l'autre de ce projet : **ce qui protège le
coffre, ce n'est pas la consigne, c'est l'impossibilité**. La note du
2026-09-13 le relevait pour les permissions du harness, où `read_only: true`
cesse d'être une phrase que l'agent peut ignorer. On retrouve exactement la
même chose ici, à un autre étage : une tâche qui interdit d'écrire vaut mieux
qu'un modèle à qui on demande de ne pas écrire.

Corollaire inconfortable : le choix du modèle importe moins qu'il n'y paraît
dans les zones où le chemin d'écriture est fermé, et beaucoup plus partout
ailleurs. C'est un argument pour fermer davantage de chemins, pas pour acheter
un plus gros modèle.

Reste une réserve que le script livré ne lèvera pas. L'attention par fenêtre
glissante rend un très long contexte accessible **en lecture** ; elle ne
garantit pas qu'une quarantaine de règles lues au début soient toutes
appliquées à la fin. Or c'est précisément ce que le contrat demande. Les
scores annoncés viennent de l'éditeur, le modèle a deux semaines, et rien de
tout cela n'a tourné sur la machine.

## URLs sources

1. https://huggingface.co/XHToken/Spark-X2.5-4B
2. https://github.com/XHToken/Spark-X2.5
3. https://huggingface.co/XHToken/Spark-X2.5-4B-GGUF
4. https://www.glukhov.org/llm-hosting/comparisons/amd-rocm-vs-vulkan-llm-hosting/
5. https://vachsark.com/blog/vulkan-beats-rocm/
6. https://github.com/parsapp/rx9060xt-llm-benchmarks
