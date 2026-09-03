# Un index maintenu à la main finit par mentir

Leçon générale, tirée d'un cas concret. Vaut pour tout fichier qui **décrit**
d'autres fichiers.

## Statut
🟢 Vérifiée — trois erreurs réelles trouvées en une session.

---

## Le constat

`IA/system/skills-index.md` et `IA/system/agents-index.md` étaient maintenus à
la main, en parallèle des frontmatters qu'ils décrivaient. Deux textes, deux
vérités, aucune confrontation. Régénérer les index depuis les frontmatters a
fait tomber trois erreurs d'un coup, invisibles jusque-là :

1. **`skills-index.md` attribuait `proxmox` et `traefik` à l'agent
   `assistant`**, qui ne les déclarait pas dans sa liste `skills`. L'index
   affirmait une capacité que l'agent n'avait pas.
2. **`mermaid` annonçait une sortie ASCII** que le corps du même fichier
   déclare absente de `mermaid-cli`. La description contredisait le skill.
3. **Les liens des `sommaire.md` ne pointaient nulle part** : écrits
   relativement à la racine du dépôt alors qu'ils vivent dans un dossier
   imbriqué. Personne ne les avait cliqués.

## La leçon

Un fichier dérivé doit être **généré**, et sa fraîcheur **vérifiée**. Sinon il
diverge silencieusement de sa source, et plus il est ancien, plus on lui fait
confiance à tort.

Trois niveaux, dans cet ordre :

| Niveau | Moyen | Coût |
| --- | --- | --- |
| Écrire à la main | rien | dérive garantie |
| Générer | un script | la dérive redevient possible dès qu'on oublie de lancer le script |
| Générer **et** vérifier | script + contrôle en CI | la dérive devient impossible à pousser |

Le deuxième niveau ne suffit pas : `regenerate_sommaire.py` existait depuis le
début, et les liens qu'il produisait étaient faux depuis le début.

## Application dans le coffre

- `scripts/regenerate_index.py` régénère les deux index depuis les
  frontmatters ;
- `scripts/regenerate_sommaire.py --verifier` signale un sommaire périmé sans
  rien écrire ;
- `scripts/verifier_coffre.py` refuse un coffre incohérent, et tourne en CI à
  chaque poussée.

## Généralisation

Avant d'écrire un fichier qui en décrit d'autres, se poser la question : d'où
vient l'information ? Si elle existe déjà ailleurs, ce fichier doit être
produit, jamais saisi.
