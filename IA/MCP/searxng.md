---
schema: 1
kind: mcp
name: searxng
description: Recherche web via une instance SearXNG auto-hébergée — méta-moteur qui interroge plusieurs moteurs sans tracer l'appelant. À charger pour le dernier étage de la cascade du skill `recherche`, quand le coffre et les sites de confiance n'ont pas la réponse.
type: tool
transport: stdio
permission: elevated
---

# MCP — SearXNG

Un serveur MCP branché sur une instance **SearXNG auto-hébergée**. SearXNG est
un méta-moteur : il interroge plusieurs moteurs, agrège les résultats, et ne
trace pas l'appelant. Le serveur expose la recherche à l'agent ; il ne stocke
rien.

Implémentation de référence : `ihor-sokoliuk/mcp-searxng`. D'autres serveurs
MCP SearXNG existent ; le nom du paquet et la commande de lancement dépendent de
celui que vous retenez, et l'entrée du gabarit est à ajuster en conséquence.

Gabarit de config prêt à copier : `IA/MCP/mcp.example.json`, entrée `searxng`,
où l'URL fictive est à remplacer par celle de votre instance.

## Ce que cet outil sert à faire

Il porte le **dernier étage** de la cascade décrite par le skill `recherche` :
le web général. On ne l'appelle qu'après avoir épuisé le coffre parent et les
sites de confiance — c'est l'étage le plus bruité, et celui dont les résultats
demandent le plus de vérification.

C'est aussi une alternative à `chrome-devtools` quand il ne faut que **lire**
des résultats, sans piloter un navigateur.

## Permissions

`permission: elevated`. L'outil sort de la machine : chaque requête part vers
l'instance SearXNG, qui interroge elle-même des moteurs tiers. C'est ce
caractère qui justifie le niveau.

## Sécurité

- **L'URL de l'instance n'entre jamais dans le dépôt.** Elle vit dans la
  configuration du harness, hors dépôt — le dépôt est public, et une adresse
  interne n'y a pas sa place (§9). `mcp.example.json` ne porte qu'une URL
  fictive.
- **Une instance auto-hébergée n'est pas pour autant privée** : SearXNG
  interroge des moteurs externes, qui voient la requête. Ne pas y mettre de
  contenu du coffre parent — ni un extrait de note, ni un nom de projet.
- **Consigner l'usage** : tout appel de ce serveur laisse une ligne dans le log
  de session (§9) — quoi, où, résultat. On y écrit la nature de la recherche,
  pas une URL interne.
- **Vérifier ce qu'on rapporte** : un résultat de moteur n'est pas une source.
  Citer l'URL réellement consultée, et distinguer l'évidence de
  l'interprétation (§8).
