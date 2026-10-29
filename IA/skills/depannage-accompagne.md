---
schema: 1
kind: skill
name: depannage-accompagne
description: Dépanner, à distance et sans supervision, le poste d'une personne non technique — diagnostiquer en lecture seule, proposer une action à la fois en français simple, refuser sudo et toute suppression, ne rien écrire hors du carnet du chantier. Jamais avec le propriétaire du coffre comme personne à accompagner.
module: linux-poste
type: outil
read_only: false
---

# Skill — Dépannage accompagné

Méthode d'un agent qui dépanne, en autonomie, le poste d'une personne qui ne
peut pas juger une commande avant de la lancer. Le propriétaire du coffre
n'est pas là pour superviser ; la personne devant l'écran, si.

## Politique d'autorisation

| Action | Comportement |
| --- | --- |
| Lecture du poste (`df`, `free`, `journalctl`, `systemctl status`, `ip`, `lsblk`…) | libre, sans demander |
| Écriture dans le carnet du chantier | libre — c'est la trace de l'agent |
| Modification du système (paquet, réglage, configuration) | annoncer en français simple **une seule** action et son effet, puis attendre un « oui » explicite |
| `sudo` ou tout mot de passe | **jamais** : donner la commande à recopier, la personne la tape elle-même |
| Suppression de fichiers ou de données | **jamais** : consigner le suspens au carnet et attendre le propriétaire |
| Secrets (clés, jetons, mots de passe) | ne jamais les afficher, répéter, écrire ni demander ; une valeur rencontrée se masque sans être recopiée |

## Méthode

1. **Diagnostiquer d'abord, en lecture seule** : rassembler les faits avant de
   proposer quoi que ce soit.
2. **Expliquer, pas noyer** : le problème et la solution en français simple,
   sans jargon ni choix multiple — la personne ne peut pas juger une
   commande, on ne lui en fait jamais choisir entre plusieurs.
3. **Une action à la fois** : une solution principale ; une alternative
   seulement si elle est réellement plus simple pour elle.
4. **Écrire le carnet au fil de l'eau** : ce qui est constaté, proposé,
   décidé, fait — l'étape en cours **avant** d'agir — puis `git commit` et
   `git push`. Si la poussée échoue, le commit reste et repousse au prochain
   essai ; rien ne se perd, la trace part juste plus tard.
5. **S'arrêter plutôt que s'acharner** : après trois essais sans résultat
   nouveau, ou dès qu'un geste de la personne (recopier une commande, un
   clic, un redémarrage) ira plus vite — le lui dire en une phrase et
   consigner le suspens au carnet pour le propriétaire.
6. **Signer** chaque entrée de carnet du nom de l'agent qui l'utilise.
7. **Ne rien affirmer sans l'avoir lu** dans la séance en cours ; à défaut,
   le dire, ou marquer « NON VÉRIFIÉ ».

## Ce que le carnet porte, et pas

Aucune adresse, aucun nom d'hôte, aucun identifiant : la trace circule hors
du coffre. La **nature** des actions y suffit ; le propriétaire retrouve la
cible par ses propres moyens.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « je peux lui faire choisir entre deux options, elle comprendra » | elle ne peut pas juger une commande qu'elle ne connaît pas : une seule solution, pas un menu |
| « sudo juste pour cette fois, c'est plus rapide » | jamais : la commande se donne à recopier, le mot de passe ne se tape jamais pour elle |
| « je supprime, je recréerai pareil si besoin » | non : consigner le suspens et attendre le propriétaire, une suppression ne se refait pas à l'identique |
| « je note juste le résultat, pas l'étape en cours » | si la connexion tombe entre les deux, l'étape en cours est ce qui manque pour reprendre |
