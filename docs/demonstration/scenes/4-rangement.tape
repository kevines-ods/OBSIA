# Scène 4 — le rangement : aperçu d'abord, écriture après accord.
Output "4-rangement.mp4"
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

Type "Range mes notes en vrac, s'il te plaît."
Sleep 900ms
Enter
Wait+Screen@180s /Build · .+ · [0-9.]+m? ?[0-9.]*s/
Sleep 5s

# La seconde attente est une durée fixe : le repère de fin de la première
# réponse reste à l'écran. À allonger si le modèle est lent.
Type "Oui, vas-y."
Sleep 900ms
Enter
Sleep 75s
