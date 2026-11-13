# Scène 5 — le contradicteur, en sous-agent : il relit le plan sans rien modifier.
Output "5-contradicteur.mp4"
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

# « @ » ouvre la liste : Entrée retient le sous-agent, la phrase suit.
Type "@contra"
Sleep 1200ms
Enter
Sleep 600ms
Type "relis mon plan d'arrosage avant que je continue."
Sleep 900ms
Enter
Wait+Screen@300s /Build · .+ · [0-9.]+m? ?[0-9.]*s/
Sleep 7s
