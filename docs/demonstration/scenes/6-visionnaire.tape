# Scène 6 — le visionnaire, en sous-agent : une idée confrontée à la vision du projet.
Output "6-visionnaire.mp4"
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
Sleep 6s

# « @ » ouvre la liste : Entrée retient le sous-agent, la phrase suit.
Type "@vision"
Sleep 1200ms
Enter
Sleep 600ms
Type "j'aimerais ajouter une caméra avec reconnaissance d'images dans le cloud. Est-ce que ça va dans le sens du projet ?"
Sleep 900ms
Enter
Wait+Screen@300s /Build · .+ · [0-9.]+m? ?[0-9.]*s/
Sleep 7s
