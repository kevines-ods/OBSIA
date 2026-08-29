# 2026-08-20 — Spécification stack Tauri/Rust + multi-fournisseur

## Objectif
Application de bureau native Linux capable d'orchestrer des agents IA.

## Choix techniques
| Couche | Choix | Pourquoi |
|---|---|---|
| Framework | **Tauri** | Bundle léger, natif Linux, backend Rust sécurisé |
| Langage | **Rust** | Mémoire sûre, perf, accès au système |
| Frontend | React/TypeScript | Écosystème UI riche |
| LLM | **Multi-fournisseur** | Local (Ollama/Gemma) + API (Claude/OpenAI) |

## Raison du multi-fournisseur
Le modèle est remplaçable ; le coffre (mémoire) ne l'est pas. Choisir son
fournisseur ne doit pas obliger à réécrire.

## Interprétation
Bascule provider par capacité (texte/vision/speech) pour optimiser coût/latence.

## URLs sources
- (à ajouter)
