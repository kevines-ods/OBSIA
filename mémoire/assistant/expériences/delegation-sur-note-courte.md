# Déléguer une note courte déjà lue ne rapporte rien

Leçon réutilisable sur la délégation à un modèle local. Vaut pour toute tâche
qu'on confie à un modèle dont il faut ensuite relire le résultat.

## Statut
🟢 Vérifiée le 2026-09-26 — un cas réel, constaté par l'utilisateur.

---

## Le constat

Consigne : résumer une note de `-SAVOIRS/` d'environ une page en déléguant au
modèle local, puis vérifier. Le cas remplissait les trois critères que le
skill `delegation-locale` posait alors : consigne fermée, aucun savoir
extérieur, erreur visible à la relecture.

Le résultat : 21 s d'appel et trois puces exactes mais floues, dont deux à
réécrire. Pour les vérifier, il avait fallu relire la note en entier. Le
résumé final a été rédigé par l'agent principal. L'utilisateur l'a relevé :
par rapport à une exécution de bout en bout par l'agent, l'appel n'a rien
apporté.

## La cause

Le test de délégation ne regardait pas le **coût de la vérification**. Sur
une pièce unique et courte, vérifier coûte autant que faire : la source doit
être lue en entier dans les deux cas. L'appel n'ajoute alors que son attente
et une passe de correction.

## La règle qui en sort

Déléguer seulement si vérifier coûte nettement moins que faire soi-même :
un lot contrôlé par échantillon, ou une sortie vérifiable mécaniquement
(JSON valide, valeur présente dans la source). Compilée dans
`delegation-locale` comme quatrième critère du test.
