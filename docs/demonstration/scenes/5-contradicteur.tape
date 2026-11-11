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
Sleep 6s

Type "Avant de continuer, fais relire mon plan d'arrosage par le contradicteur."
Sleep 900ms
Enter
Wait+Screen@240s /Build · .+ · [0-9.]+m? ?[0-9.]*s/
Sleep 7s
