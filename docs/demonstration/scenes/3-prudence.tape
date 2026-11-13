# Scène 3 — la prudence : une commande trouvée sur un forum n'est pas lancée, elle est expliquée.
Output "3-prudence.mp4"
Set Shell bash
Set FontFamily "JetBrains Mono"
Set FontSize 16
Set Width 1280
Set Height 800
Set Padding 24
Set TypingSpeed 55ms

Hide
Type 'cd "$OBSIA_DEMO_COFFRE" && clear'
Enter
Show

Type "opencode"
Sleep 700ms
Enter
# On attend l'écran d'accueil : un démarrage lent ferait taper dans le vide.
Wait+Screen@60s /Ask anything/
Sleep 2s

Type "J'ai noté une commande docker dans mes notes en vrac. Je peux la lancer ?"
Sleep 900ms
Enter
Wait+Screen@180s /Build · .+ · [0-9.]+m? ?[0-9.]*s/
Sleep 6s
