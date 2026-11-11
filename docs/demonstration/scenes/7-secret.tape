# Scène 7 — les secrets : un mot de passe ne s'écrit jamais dans une note. Le mot de passe est inventé.
Output "7-secret.mp4"
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

Type "Note dans mon projet de serre que le mot de passe du wifi du jardin est Tomate-Cerise-42."
Sleep 900ms
Enter
Wait+Screen@240s /Build · .+ · [0-9.]+m? ?[0-9.]*s/
Sleep 7s
