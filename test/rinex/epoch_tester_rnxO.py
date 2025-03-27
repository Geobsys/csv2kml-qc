#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 22:05:08 2025

@author: anthonydiallo
"""

"""
Script qui teste, époque par époque, la lecture d'un fichier RINEX par georinex.
Pour chaque époque, on crée un fichier temporaire contenant l'en-tête et l'époque,
puis on tente de le charger avec gr.load.
Dès qu'une époque provoque une erreur, le script affiche l'heure de l'époque problématique.
"""

import os
import tempfile
import georinex as gr

def read_rinex_file(filename):
    """
    Lit le fichier RINEX et retourne l'en-tête ainsi que la liste des époques.

    Le fichier est lu intégralement et l'en-tête est extrait jusqu'à la ligne contenant
    "END OF HEADER". Le reste du fichier est découpé en époques, où chaque époque commence
    par une ligne débutant par '>'.

    Parameters
    ----------
    filename : str
        Chemin vers le fichier RINEX à lire.

    Returns
    -------
    header : list of str
        Liste des lignes constituant l'en-tête (incluant la ligne "END OF HEADER").
    epochs : list of list of str
        Liste des époques, chaque époque étant une liste de lignes.

    Raises
    ------
    ValueError
        Si l'en-tête n'est pas trouvé dans le fichier.
    """
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Trouver la fin de l'en-tête
    header_end = None
    for i, line in enumerate(lines):
        if "END OF HEADER" in line:
            header_end = i
            break
    if header_end is None:
        raise ValueError("En-tête introuvable dans le fichier.")
    
    header = lines[:header_end+1]
    body = lines[header_end+1:]
    
    # Découper le body en époques
    epochs = []
    current_epoch = []
    for line in body:
        if line.startswith('>'):
            # Nouvelle époque trouvée
            if current_epoch:
                epochs.append(current_epoch)
            current_epoch = [line]
        else:
            if current_epoch:
                current_epoch.append(line)
    # Ajouter la dernière époque, si présente
    if current_epoch:
        epochs.append(current_epoch)
    
    return header, epochs

def test_epoch_with_georinex(header, epoch_lines):
    """
    Crée un fichier temporaire contenant l'en-tête et une seule époque, puis tente de le charger avec georinex.

    Le fichier temporaire est supprimé après le test, quelle que soit l'issue du chargement.

    Parameters
    ----------
    header : list of str
        Liste des lignes composant l'en-tête du fichier RINEX.
    epoch_lines : list of str
        Liste des lignes de l'époque à tester.

    Returns
    -------
    bool
        True si le chargement du fichier temporaire par georinex réussit, False sinon.

    Notes
    -----
    Toute exception survenant lors du chargement est capturée, affichée, et le fichier temporaire est supprimé.
    """
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
        # Écrire l'en-tête suivi de l'époque
        temp.writelines(header)
        temp.writelines(epoch_lines)
        temp_filename = temp.name

    try:
        # Tenter de charger le fichier temporaire avec georinex
        obs = gr.load(temp_filename, useindicators=False)
        success = True
    except Exception as e:
        print("Erreur lors du chargement de l'époque :", e)
        success = False
    finally:
        os.remove(temp_filename)
    return success

def extract_epoch_time(epoch_lines):
    """
    Extrait l'heure de l'époque à partir de la première ligne de l'époque.

    La première ligne doit commencer par '>' et contenir au moins 7 éléments séparés par des espaces.
    Les éléments 2 à 7 correspondent respectivement à l'année, le mois, le jour, l'heure, la minute et la seconde.

    Parameters
    ----------
    epoch_lines : list of str
        Liste des lignes représentant une époque, avec la première ligne contenant la date et l'heure.

    Returns
    -------
    str
        Chaîne représentant la date et l'heure de l'époque, ou "Inconnue" si le format n'est pas respecté.

    Examples
    --------
    >>> extract_epoch_time(["> 2025 03 25 12 57 07.0000000  0 16"])
    '2025 03 25 12 57 07.0000000'
    """
    first_line = epoch_lines[0]
    parts = first_line.strip().split()
    if len(parts) >= 7:
        # Concaténer les éléments de date et heure
        epoch_time = " ".join(parts[1:7])
    else:
        epoch_time = "Inconnue"
    return epoch_time

def main():
    """
    Exécute le script de test de lecture d'un fichier RINEX.

    Le script lit un fichier RINEX, extrait l'en-tête et les époques, puis teste chaque époque en tentant
    de charger un fichier temporaire constitué de l'en-tête et de l'époque. En cas d'erreur lors du chargement,
    l'heure de l'époque problématique est affichée et l'exécution s'arrête.
    """
    input_filename = "rinexO2703.25o.A"
    header, epochs = read_rinex_file(input_filename)
    print("Nombre total d'époques :", len(epochs))
    
    for idx, epoch_lines in enumerate(epochs):
        epoch_time = extract_epoch_time(epoch_lines)
        print(f"Test de l'époque {idx+1} ({epoch_time}) ...", end=" ")
        if test_epoch_with_georinex(header, epoch_lines):
            print("OK")
        else:
            print("ERREUR détectée pour cette époque !")
            print(f"L'époque problématique est : {epoch_time}")
            break
    else:
        print("Toutes les époques ont été testées sans erreur.")

if __name__ == '__main__':
    main()

