# Scène 2 — la reprise : l'agent retrouve le chantier par son carnet.
Output "2-reprise.mp4"
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

Type "Où en est mon projet de serre ? Je ne sais plus où je m'étais arrêté."
Sleep 900ms
Enter
Wait+Screen@180s /Build · .+ · [0-9.]+m? ?[0-9.]*s/
Sleep 6s
