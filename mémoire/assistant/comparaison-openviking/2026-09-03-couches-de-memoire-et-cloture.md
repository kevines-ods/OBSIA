# 2026-09-03 — Faut-il plus de couches de mémoire ? Et clôture de session

Réponse mesurée à une question posée en session, puis application du point 6 de
[[2026-09-03-comparaison-openviking]].

## Statut
🟢 Tranché — pas de troisième couche. Skill `cloture-de-session` créé.

---

## Décisions

- **Aucune couche de description supplémentaire n'est ajoutée.** Les deux
  niveaux existants (sommaire d'agent → sommaire de projet → note) suffisent
  largement à la taille actuelle du coffre.
- **Seuil de réexamen fixé** : rouvrir la question quand la mémoire dépassera
  **~50 000 jetons** (soit environ 180 000 caractères, ×3,3 par rapport à
  aujourd'hui), ou quand `mémoire/<agent>/sommaire.md` dépassera ~4 000
  caractères — au-delà de trente projets environ.
- **Le vrai risque identifié est la taille des notes, pas le nombre de
  couches.** D'où le point 4 du skill `cloture-de-session` : une note de projet
  au-delà de ~6 000 caractères se découpe ou se résume.
- **Point 6 appliqué** sous forme de skill plutôt que de règle du contrat : la
  distillation est une **procédure**, pas une règle. Le §6 dit déjà *où* écrire ;
  le skill dit *comment* décider ce qui remonte.

---

## Évidence — les mesures du 2026-09-03

| Ensemble | Caractères | ≈ jetons | Part d'une fenêtre de 200k |
| --- | ---: | ---: | ---: |
| prompt système auto-chargé | 19 753 | 5 486 | 2,7 % |
| tous les `sommaire.md` (10) | 8 055 | 2 237 | 1,1 % |
| **mémoire entière (17 notes)** | **54 613** | **15 170** | **7,6 %** |

Parcours guidé vers une note précise — sommaire d'agent (1 424) + sommaire de
projet (488) + la note (956) — soit 2 868 caractères, **≈ 796 jetons**.

Taille moyenne : un sommaire fait 805 caractères, une note 3 212. Mais les plus
petites notes du coffre font 433 à 956 caractères : **plus petites que le
sommaire qui les décrit**. Pour celles-là, la couche d'index coûte déjà plus
cher que la lecture directe.

Répartition très inégale : la note d'analyse OpenViking pesait à elle seule
15 874 caractères, soit **29 % de toute la mémoire**.

---

## Interprétation

OpenViking construit L0/L1/L2 parce qu'il gère des milliers de documents qu'il
est **impossible** de tout charger : son propre banc d'essai revendique 34 à
91 % de jetons économisés en entrée. Le gain vient du fait que l'alternative
est inatteignable.

Ici, l'alternative est atteignable. Charger **toute** la mémoire — chaque note,
sans exception — coûte 7,6 % de la fenêtre. Il n'y a rien à économiser, donc
rien qu'une couche supplémentaire puisse faire gagner.

Le parcours guidé conserve un intérêt réel (796 jetons contre 15 170), et c'est
exactement ce que les deux niveaux actuels fournissent depuis le point 2. Une
**troisième** couche — un résumé sémantique par dossier, à la manière du
`.abstract.md` — ajouterait dix fichiers à maintenir, une génération à
déclencher, et une occasion de plus de diverger, pour un gain sous le seuil de
mesure.

Formulé autrement : le coût d'une couche est **fixe** (fichiers, script,
vérification, discipline), son gain est **proportionnel** à ce qu'elle évite de
charger. À 15 000 jetons de mémoire totale, le gain ne couvre pas le coût. À
50 000, la question redevient ouverte — d'où le seuil.

Le vrai risque n'est donc pas structurel mais rédactionnel : une note qui enfle
sature le contexte bien avant qu'un manque de couche ne se fasse sentir. Une
note de 15 900 caractères coûte plus cher que les dix sommaires réunis.

---

## Questions ouvertes

- [ ] Point 7 de l'analyse — sortir les gabarits de prompt du code Python —
      toujours classé « gain faible », toujours non fait.
- [ ] Le skill `cloture-de-session` s'appliquera-t-il réellement ? Une étape de
      fin de session est ce qui se saute le plus facilement. À réévaluer après
      quelques sessions : si elle est systématiquement oubliée, c'est qu'elle
      doit être déclenchée autrement.

---

## Synthèse IA

La question posée — le gain justifie-t-il la complexification — appelait des
chiffres, pas une opinion. Les chiffres disent non, et de loin : un facteur
treize sépare la mémoire actuelle de la fenêtre disponible.

Ce qui mérite d'être retenu d'OpenViking sur ce point n'est pas le nombre de
couches mais le **critère** : une couche se justifie quand ce qu'elle évite de
charger dépasse ce qu'elle coûte à maintenir. Ce critère se mesure ; il ne se
devine pas. Il donnera « oui » un jour, et le seuil est écrit.

## URLs sources

- Couches L0/L1/L2 et économies de jetons revendiquées :
  https://github.com/volcengine/OpenViking/blob/main/docs/en/concepts/03-context-layers.md
- Résultats de banc d'essai (LoCoMo, tau2-bench) :
  https://github.com/volcengine/OpenViking
