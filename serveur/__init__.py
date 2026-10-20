#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L'outillage local du coffre — la porte d'entrée, la carte légale et l'écrivain.

Ce dossier est le **code du produit**, à côté du moteur de règles qu'il appelle
(`scripts/convention_des_notes.py`, `scripts/garde_secrets.py`). Il n'entre ni
dans `IA/` ni dans un dossier du coffre parent : il se retire en supprimant ce
seul dossier, le coffre continuant de s'installer, se lire et se modifier sans
lui.

Rien ici ne porte le nom d'un dossier d'un coffre : les zones autorisées sont
données par l'appelant. Un chemin du coffre parent gravé dans ce code serait un
défaut, pas une commodité (cap « le dépôt produit diffère du dépôt OBSIA »).
"""

__all__ = ["porte_entree", "carte_legale", "ecrivain"]
