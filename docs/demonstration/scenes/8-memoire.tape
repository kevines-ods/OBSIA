# Scène 8 — la mémoire : une préférence dite une fois est retrouvée dans une séance neuve.
Output "8-memoire.mp4"
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

Type "Retiens que je veux des réponses courtes, et qu'on m'explique chaque commande avant de la lancer."
Sleep 900ms
Enter
Wait+Screen@240s /Build · .+ · [0-9.]+m? ?[0-9.]*s/
Sleep 4s

# /new ouvre une séance vierge : l'écran se vide, le repère de fin redevient fiable.
Type "/new"
Sleep 600ms
Enter
Sleep 2s
Type "Qu'est-ce que tu sais de ma façon de travailler ?"
Sleep 900ms
Enter
Wait+Screen@240s /Build · .+ · [0-9.]+m? ?[0-9.]*s/
Sleep 7s
