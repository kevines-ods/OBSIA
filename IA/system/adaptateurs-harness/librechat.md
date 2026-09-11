# LibreChat

**Statut : gabarit v1 — à valider sur machine réelle.**

Interface web auto-hébergée dont les conversations vivent dans une base **sur
le serveur**, pas dans le navigateur : une même session se reprend depuis un
poste fixe comme depuis un téléphone. Agents, MCP et fournisseurs multiples
sont natifs, ce qui en fait un candidat sérieux quand le coffre doit être
atteint depuis plusieurs appareils.

1. **Charger le cerveau.** Depuis la racine du dépôt, générer le prompt :
   `python3 scripts/generer_prompt.py -o prompt-systeme.md --mcp`, puis donner
   le fichier produit comme instructions du preset (ou de l'agent côté
   interface). Le mécanisme `CLAUDE.md` n'existe pas ici : rien n'est chargé
   implicitement depuis le répertoire de travail.
2. **Atteindre le coffre parent.** Déclarer le bloc MCP `coffre-parent`
   (`commun.md`) dans la configuration MCP de l'interface, pointant sur la
   **racine du coffre** — le dossier qui contient `OBSIA/`. Fiche de l'outil :
   `IA/MCP/coffre-parent.md` ; chemin réel et secrets hors dépôt (§7.6).
3. **Modèles.** Tous les moteurs se branchent par configuration, pas par le
   coffre : un serveur local (llama.cpp, Ollama) comme un service distant
   s'adressent par une configuration de type OpenAI-compatible. Quelle machine
   répond ne s'écrit jamais dans le coffre (§7.6), seulement dans la
   configuration — qui n'est pas versionnée.
4. **Un fichier agent = un interlocuteur côté interface.** Le `name` du
   frontmatter donne le nom, le corps porte les instructions, `skills` et `mcp`
   disent ce qu'il mobilise. Le coffre reste la source de vérité : ne pas
   recopier un agent dans l'interface, le référencer.
5. **Tâches planifiées.** Ne rien présumer : tant qu'il n'est pas vérifié que
   l'interface expose un planificateur, une tâche reste `exécutant: local` et
   s'instancie sur la machine (§12). Une tâche = au plus une instance vivante,
   tous exécutants confondus.
6. **Vérifier après branchement** — comme pour tout harness : lister la racine
   du coffre, lire une note de `Mon coffre/SAVOIRS/`, retrouver le registre des
   tags. Si `SAVOIRS/` n'apparaît pas, le serveur n'est pas monté sur la bonne
   racine.

> Licence **MIT**, vérifiée à la source — compatible avec l'AGPL-3.0-or-later du
> dépôt. À recontrôler au moment du choix : une licence maison, même sur un
> outil libre, peut restreindre ce que l'AGPL autorise.

> Le coffre ne dépend pas de LibreChat ; cette fiche n'est qu'un gabarit
> d'intégration.
