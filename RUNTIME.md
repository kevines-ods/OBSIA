# RUNTIME.md
## Architecture backend
### Modules principaux
- `app`: Gestion des fenêtres et menus Tauri
- `state`: Gestion de l'état (State<'_, T>)
- `commands`: Commandes Tauri (IPC)
- `sandbox`: Sécurité et capability-based permissions