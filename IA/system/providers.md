# providers.md — Fournisseurs LLM

Ce coffre ne parle à aucun fournisseur : il décrit *quoi* faire, le harness
fournit *avec quoi*. Ce fichier n'est donc qu'un **repère** pour choisir un
modèle — la configuration réelle (clés, URLs, modèle par défaut) vit dans le
harness, jamais ici.

## Catalogue

| Fournisseur | Type | Modèle(s) | Notes |
|---|---|---|---|
| OpenAI | API | gpt-… | payant, rapide |
| Anthropic | API | claude-… | raisonnement long |
| Google | API | gemini-… | multimodal |
| Mistral | API | mistral-… | hébergement européen |
| Ollama | local | llama, gemma, qwen | gratuit, hors-ligne, plus lent |
| llama.cpp | local | GGUF | gratuit, hors-ligne, contrôle fin |

## Choix du modèle

Bascule par capacité : vision ou audio → fournisseur multimodal ; texte seul →
le moins cher qui tient la tâche. Une tâche portant sur des données privées se
traite de préférence sur un fournisseur local.

## Sécurité

Les clés d'API sont fournies au harness par **variables d'environnement**
(`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, …). Elles n'entrent **jamais** dans le
coffre, ni dans une note, ni dans un fichier de configuration versionné — le
dépôt est public (cf. `VAULT-CONTRACT.md`).
