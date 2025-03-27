#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 22:05:08 2025

@author: anthonydiallo
"""

# # -*- coding: utf-8 -*-
# import gnsstoolbox.rinex_o as rx
# import gpsdatetime as gpst

# # 3. Écrire le nouveau fichier RINEX corrigé
# Rnx = rx.rinex_o
# try :
#     Rnx.loadRinexO("sept084m.25o")
#     print("ouverture du fichier rinex réussi")
#     #print(t) 
# except :
#     print("Échec")

# t=gpst.gpsdatetime() 
# t.rinex_t('13  5 30  1  0 30.0000000')
# Ep = Rnx.getEpochByMjd(t.mjd)  
# Hd = Rnx.getHeaderByMjd(t.mjd)
# print(Hd)

# Hd = Rnx.getHeaderByMjd(t.mjd)
# print(Hd)

# with open("sept084m_clean.25o", "w") as fout:
#     fout.writelines(header_lines)
#     fout.write("END OF HEADER\n")
#     fout.writelines(data_lines)

# print("Nettoyage terminé. Fichier 'sept084m_clean.25o' généré.")

# import georinex as gr

# obs = gr.load('sept084m_final.25o')

# !/usr/bin/env python3
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
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
    """Lit le fichier RINEX et retourne l'en-tête et la liste des époques (chaque époque est une liste de lignes)."""
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
    Crée un fichier temporaire contenant l'en-tête et une seule époque,
    tente de le charger avec georinex, et renvoie True si le chargement réussit,
    ou False sinon.
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
    Extrait l'heure de l'époque à partir de la première ligne de l'époque (ligne commençant par '>').
    Retourne une chaîne représentant la date et l'heure.
    Exemple de ligne d'époque :
    > 2025 03 25 12 57 07.0000000  0 16
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
    input_filename = "sept084o.25o.A"
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

# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# Script pour supprimer toutes les époques situées entre la première époque
# et la première époque dont l'heure est "12 33 11.0000000".
# Toutes les autres époques sont conservées et la structure du fichier RINEX d'observation est préservée.
# Le fichier résultant est écrit dans un nouveau fichier.
# """

# import datetime

# def read_rinex_file(filename):
#     """
#     Lit le fichier RINEX et retourne l'en‐tête et la liste des époques.
#     Chaque époque est une liste de lignes (la première ligne de chaque époque commence par '>').
#     """
#     with open(filename, 'r') as f:
#         lines = f.readlines()
    
#     # Trouver la fin de l'en‐tête (la ligne contenant "END OF HEADER")
#     header_end = None
#     for i, line in enumerate(lines):
#         if "END OF HEADER" in line:
#             header_end = i
#             break
#     if header_end is None:
#         raise ValueError("L'en‐tête n'a pas été trouvé dans le fichier.")
    
#     header = lines[:header_end+1]
#     body = lines[header_end+1:]
    
#     # Découper le corps en époques (chaque ligne commençant par '>' démarre une nouvelle époque)
#     epochs = []
#     current_epoch = []
#     for line in body:
#         if line.startswith('>'):
#             if current_epoch:
#                 epochs.append(current_epoch)
#             current_epoch = [line]
#         else:
#             if current_epoch:
#                 current_epoch.append(line)
#     if current_epoch:
#         epochs.append(current_epoch)
    
#     return header, epochs

# def parse_epoch_time(epoch_line):
#     """
#     Extrait la date et l'heure de la ligne d'époque.
#     Exemple de ligne d'époque :
#       > 2025 03 25 12 33 11.0000000  0 16
#     Retourne un objet datetime.
#     """
#     parts = epoch_line.strip().split()
#     if len(parts) < 7:
#         raise ValueError("Format d'époque incorrect : " + epoch_line)
#     year = int(parts[1])
#     month = int(parts[2])
#     day = int(parts[3])
#     hour = int(parts[4])
#     minute = int(parts[5])
#     # La seconde peut être sous forme flottante
#     second = float(parts[6])
#     return datetime.datetime(year, month, day, hour, minute, int(second), 
#                              microsecond=int((second - int(second))*1e6))

# def filter_epochs(header, epochs, target_time_str="12 33 11.0000000"):
#     """
#     Conserve :
#       - La première époque (la plus ancienne)
#       - Et toutes les époques dont l'heure est >= target_time (target_time_str)
#     Les époques strictement entre la première et la première époque atteignant target_time sont supprimées.
    
#     Le paramètre target_time_str doit être une chaîne de caractères du type "hh mm ss.sss..."
#     """
#     if not epochs:
#         return []
    
#     # La première époque (toujours conservée)
#     first_epoch_time = parse_epoch_time(epochs[0][0])
    
#     # On convertit target_time_str en un tuple (hour, minute, second)
#     parts = target_time_str.split()
#     target_hour = int(parts[0])
#     target_min = int(parts[1])
#     target_sec = float(parts[2])
    
#     # On recherche la première époque dont l'heure est >= target
#     target_epoch = None
#     for ep in epochs:
#         try:
#             ep_time = parse_epoch_time(ep[0])
#         except Exception as e:
#             continue
#         # Ici, on compare uniquement l'heure, les minutes et les secondes
#         if (ep_time.hour > target_hour or 
#             (ep_time.hour == target_hour and ep_time.minute > target_min) or
#             (ep_time.hour == target_hour and ep_time.minute == target_min and ep_time.second >= int(target_sec))):
#             target_epoch = ep
#             break

#     if target_epoch is None:
#         # Si aucune époque n'atteint la cible, on conserve toutes
#         return epochs
#     else:
#         # On conserve la première époque et toutes celles à partir de target_epoch
#         new_epochs = []
#         new_epochs.append(epochs[0])
#         target_found = False
#         for ep in epochs[1:]:
#             ep_time = parse_epoch_time(ep[0])
#             # Si on rencontre l'époque cible (ou une époque ultérieure), on la conserve
#             if (ep_time.hour > target_hour or 
#                 (ep_time.hour == target_hour and ep_time.minute > target_min) or
#                 (ep_time.hour == target_hour and ep_time.minute == target_min and ep_time.second >= int(target_sec))):
#                 target_found = True
#                 new_epochs.append(ep)
#             else:
#                 # Si l'époque se situe avant la cible et que target n'est pas encore rencontré, on la supprime.
#                 # Si target n'est pas encore trouvé, cela signifie que l'époque est entre la première et target.
#                 pass
#         return new_epochs

# def write_rinex_file(header, epochs, output_filename):
#     """
#     Écrit le fichier RINEX de sortie en réassemblant l'en‐tête et les époques (dans l'ordre).
#     """
#     with open(output_filename, 'w') as f:
#         f.writelines(header)
#         for ep in epochs:
#             f.writelines(ep)
#     print(f"Fichier nettoyé écrit dans {output_filename}")

# def main():
#     input_filename = "sept084m_final.25o"   # Fichier d'entrée
#     output_filename = "sept084m_cleaned_final.25o"  # Fichier de sortie
#     header, epochs = read_rinex_file(input_filename)
#     print("Nombre total d'époques lues :", len(epochs))
    
#     new_epochs = filter_epochs(header, epochs, target_time_str="12 33 11.0000000")
#     print("Nombre d'époques conservées :", len(new_epochs))
    
#     write_rinex_file(header, new_epochs, output_filename)

# if __name__ == '__main__':
#     main()
import georinex as gr

try:
    obs = gr.load('sept084m_cleaned_final_padded.25o', useindicators=False)
    print("Fichier RINEX chargé avec succès par georinex.")
    print(obs)
except Exception as e:
    print("Erreur lors du chargement du fichier nettoyé avec georinex :", e)
    
def read_rinex_file(filename):
    """
    

    Parameters
    ----------
    filename : TYPE
        DESCRIPTION.

    Raises
    ------
    ValueError
        DESCRIPTION.

    Returns
    -------
    header : TYPE
        DESCRIPTION.
    epochs : TYPE
        DESCRIPTION.

    """
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    header_end = None
    for i, line in enumerate(lines):
        if "END OF HEADER" in line:
            header_end = i
            break
    if header_end is None:
        raise ValueError("En‐tête introuvable.")
    
    header = lines[:header_end+1]
    body = lines[header_end+1:]
    
    epochs = []
    current_epoch = []
    for line in body:
        if line.startswith('>'):
            if current_epoch:
                epochs.append(current_epoch)
            current_epoch = [line]
        else:
            if current_epoch:
                current_epoch.append(line)
    if current_epoch:
        epochs.append(current_epoch)
    
    return header, epochs

# Charger et afficher la première époque conservée dans le fichier nettoyé
header, epochs = read_rinex_file("sept084m_cleaned_final_padded.25o")
if epochs:
    print("Première époque (lignes) :")
    for line in epochs[0]:
        print(repr(line))
else:
    print("Aucune époque trouvée.")



