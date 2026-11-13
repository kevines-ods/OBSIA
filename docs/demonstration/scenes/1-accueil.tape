# Scène 1 — l'accueil : ce qu'OBSIA sait faire, et ce qu'il a trouvé dans le coffre.
Output "1-accueil.mp4"
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

Type "Bonjour ! Qu'est-ce que tu peux faire pour moi dans ce coffre ?"
Sleep 900ms
Enter
Wait+Screen@180s /Build · .+ · [0-9.]+m? ?[0-9.]*s/
Sleep 6s
