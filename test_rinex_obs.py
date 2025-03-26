# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# Created on Wed Mar 26 16:56:25 2025

# @author: anthonydiallo
# """

# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# Script de nettoyage d’un fichier RINEX d’observation

# Ce script corrige surtout les problèmes de séparation d’époques :
#  - Il insère un saut de ligne avant tout caractère ">" qui n’est pas déjà en début de ligne,
#    pour forcer chaque en‐tête d’époque à être sur sa propre ligne.
#  - Ensuite, il regroupe les lignes correspondant à une époque (en partant du marqueur ">" jusqu’au
#    prochain ">") et, si nécessaire, réajuste le nombre de satellites indiqué dans l’en‐tête en fonction
#    du nombre d’enregistrements (en tenant compte des lignes de continuation qui commencent par un espace).

# Utilisation :
#     python clean_rinex_obs.py <fichier_input> <fichier_output>
# """

# import re
# import sys

# def clean_rinex_file(input_file, output_file):
#     # Lecture complète du fichier
#     try:
#         with open(input_file, 'r') as f:
#             text = f.read()
#     except Exception as e:
#         print(f"Erreur lors de l'ouverture de {input_file}: {e}")
#         sys.exit(1)

#     # 1. Insérer un saut de ligne avant chaque ">" qui n’est pas déjà au début d’une ligne.
#     text = re.sub(r'(?<!\n)>', r'\n>', text)
    
#     # Séparer le header et le corps
#     header, sep, body = text.partition("END OF HEADER")
#     if not sep:
#         print("Le fichier ne contient pas 'END OF HEADER'.")
#         sys.exit(1)
    
#     header = header + "END OF HEADER"  # conserver le header intact

#     # 2. Traiter le corps en regroupant par époque.
#     # Chaque époque commence par une ligne débutant par ">"
#     epochs = []
#     current_epoch = []
#     for line in body.splitlines():
#         if line.startswith(">"):
#             # Si on a déjà des lignes dans current_epoch, on termine l'époque précédente.
#             if current_epoch:
#                 epochs.append(current_epoch)
#             current_epoch = [line]
#         else:
#             # Ajout de la ligne à l'époque courante
#             if line.strip() != "":
#                 current_epoch.append(line)
#     if current_epoch:
#         epochs.append(current_epoch)

#     print(f"[DEBUG] Nombre d'époques trouvées : {len(epochs)}")

#     # 3. Pour chaque époque, vérifions le nombre de satellites.
#     # Dans l'en‐tête (la première ligne), le dernier champ (après l'UTC) est le nombre de satellites.
#     # Les enregistrements satellites sont les lignes dont le premier caractère n'est pas un espace.
#     corrected_epochs = []
#     for ep in epochs:
#         header_line = ep[0]
#         # On se sert d'une expression régulière pour extraire le nombre de satellites.
#         # Par exemple, dans une ligne d'époque typique (RINEX 3) :
#         # "> 2025 03 25 12 32 19.0000000  0 15" => le nombre est "15" (les champs sont séparés par des espaces)
#         parts = header_line.strip().split()
#         if len(parts) < 8:
#             print(f"[WARNING] L'en‐tête semble incomplet : {header_line}")
#             sat_expected = None
#         else:
#             try:
#                 sat_expected = int(parts[7])
#             except Exception:
#                 sat_expected = None

#         # Comptons le nombre d'enregistrements satellites.
#         # On considère comme début d'un enregistrement satellite une ligne dont le premier caractère n'est pas un espace.
#         sat_lines = [line for line in ep[1:] if line and not line.startswith(" ")]
#         sat_count = len(sat_lines)

#         if sat_expected is not None and sat_expected != sat_count:
#             print(f"[DEBUG] Epoch '{header_line.strip()}': attendu {sat_expected} satellites, trouvé {sat_count}.")
#             # Optionnel : on peut corriger le header en remplaçant le dernier champ par sat_count.
#             # On reconstruit la ligne avec les mêmes champs mais avec le nombre corrigé.
#             parts[-1] = str(sat_count)
#             new_header = " ".join(parts)
#         else:
#             new_header = header_line.strip()

#         # Reconstruire l'époque avec le header corrigé et les lignes satellites telles qu’elles étaient.
#         corrected_epoch = [new_header] + ep[1:]
#         corrected_epochs.append("\n".join(corrected_epoch))

#     # 4. Reconstruire le corps complet avec des sauts de ligne entre les époques
#     new_body = "\n".join(corrected_epochs)
#     cleaned_text = header + "\n" + new_body

#     # Sauvegarder le fichier nettoyé
#     try:
#         with open(output_file, 'w') as f:
#             f.write(cleaned_text)
#         print(f"[DEBUG] Fichier nettoyé sauvegardé dans : {output_file}")
#     except Exception as e:
#         print(f"Erreur lors de l'écriture dans {output_file}: {e}")
#         sys.exit(1)

# if __name__ == "__main__":
#     if len(sys.argv) != 3:
#         print("Usage: python clean_rinex_obs.py <input_rinex_file> <output_rinex_file>")
#         sys.exit(1)
    
#     input_rinex = sys.argv[1]
#     output_rinex = sys.argv[2]
#     clean_rinex_file(input_rinex, output_rinex)
    
#     import re

#     with open('test/rinex/sept084m.25o_cleaned', 'r') as f:
#         lines = f.readlines()

#     epoch_pattern = re.compile(r'^>\s*(\d{4}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d+\.\d+)\s+(\d+)\s+(\d+)')
#     current_epoch_count = None
#     satellite_lines = 0

#     for line in lines:
#         if line.startswith('>'):
#             # Si nous étions en train de lire un epoch, vérifier la cohérence
#             if current_epoch_count is not None:
#                 if satellite_lines != current_epoch_count:
#                     print(f"Incohérence détectée pour l'epoch précédente : attendu {current_epoch_count}, trouvé {satellite_lines}")
#                     # Parse la ligne d'époque
#             m = epoch_pattern.match(line)
#             if m:
#                 timestamp, event_flag, sat_count = m.groups()
#                 current_epoch_count = int(sat_count)
#                 print(f"Epoch détectée : {timestamp}, Event flag : {event_flag}, Satellites attendus : {current_epoch_count}")
#             else:
#                 print("Erreur de parsing de l'epoch:", line)
#             satellite_lines = 0  # Réinitialiser le compteur
#         else:
#             # Ligne satellite (ou continuation)
#             satellite_lines += 1

#         # Vérifier le dernier epoch
#     if current_epoch_count is not None and satellite_lines != current_epoch_count:
#         print(f"Incohérence détectée pour le dernier epoch : attendu {current_epoch_count}, trouvé {satellite_lines}")

    
import re

def clean_rinex_observation_file(input_file: str, output_file: str) -> None:
    """
    Nettoie un fichier RINEX d'observation en corrigeant deux types d'anomalies :
    
    1. Insertion de sauts de ligne manquants : certains marqueurs d'époque (lignes commençant par ">")
       se trouvent collés à la fin d'une ligne satellite. On insère un saut de ligne avant
       tout ">" qui n'est pas déjà en début de ligne.
       
    2. Correction de l'incohérence entre le nombre de satellites annoncé dans la ligne d'époque
       et le nombre de blocs d'observations satellites effectivement présents.
       Pour chaque époque, la fonction parcourt les lignes satellites qui suivent et compte
       les blocs (chaque bloc commence par une ligne dont le premier caractère correspond à un
       identifiant de système GNSS reconnu, par exemple "G", "R", "E", "C", "J", "I", "S").
       Si le nombre compté diffère du nombre indiqué (trouvé dans les colonnes 33-35 de la ligne
       d'époque), la ligne d'époque est reconstruite en y inscrivant le nombre réel, sur 3 caractères.
       
    Le fichier nettoyé (avec un header intact et des epochs corrigés) est sauvegardé dans output_file.
    
    Args:
        input_file (str): chemin du fichier RINEX original.
        output_file (str): chemin où sera sauvegardé le fichier nettoyé.
    """
    # Lecture intégrale du fichier
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Correction 1 : insertion d'un saut de ligne avant chaque ">" qui n'est pas déjà en début de ligne.
    content = re.sub(r'(?<!\n)>', r'\n>', content)
    
    # Séparer l'en-tête et la section d'observations
    lines = content.splitlines()
    header_lines = []
    obs_lines = []
    header_ended = False
    for line in lines:
        header_lines.append(line)
        if "END OF HEADER" in line:
            header_ended = True
            break
    # Les lignes suivantes appartiennent à la section d'observation
    obs_lines = lines[len(header_lines):]
    
    # On définit ici les identifiants possibles de systèmes GNSS.
    # En RINEX 3, la première lettre de l'observation satellite correspond au système (ex: G pour GPS, R pour GLONASS, etc.)
    valid_systems = set(['G', 'R', 'E', 'C', 'J', 'I', 'S'])
    
    cleaned_obs = []
    i = 0
    while i < len(obs_lines):
        line = obs_lines[i]
        if line.startswith('>'):
            # C'est une ligne d'époque.
            epoch_header = line
            # Extraction du nombre de satellites indiqué dans la ligne d'époque.
            # Selon la spécification, ce nombre se trouve aux positions 33-35 (indices 32 à 34)
            try:
                header_sat_count = int(epoch_header[32:35])
            except ValueError:
                header_sat_count = 0

            # On collecte ensuite toutes les lignes satellites associées à cette époque
            sat_lines = []
            i += 1
            while i < len(obs_lines) and not obs_lines[i].startswith('>'):
                sat_lines.append(obs_lines[i])
                i += 1

            # Comptage du nombre de blocs satellites.
            # Chaque bloc satellite commence par une ligne dont le premier caractère est dans valid_systems.
            sat_block_count = 0
            j = 0
            while j < len(sat_lines):
                current_line = sat_lines[j]
                if current_line and current_line[0] in valid_systems:
                    sat_block_count += 1
                    j += 1
                    # Si l'observation satellite s'étale sur plusieurs lignes,
                    # les lignes de continuation n'auront pas un identifiant satellite en première position.
                    while j < len(sat_lines) and (not sat_lines[j] or sat_lines[j][0] not in valid_systems):
                        j += 1
                else:
                    j += 1

            # Correction 2 : si le nombre de satellites indiqués diffère du nombre réellement présent,
            # on reconstruit la ligne d'époque en mettant à jour le champ satellite.
            if header_sat_count != sat_block_count:
                new_count_field = f"{sat_block_count:3d}"
                epoch_header = epoch_header[:32] + new_count_field + epoch_header[35:]
                
            # Ajout de l'époque (corrigée si besoin) et de ses lignes satellites
            cleaned_obs.append(epoch_header)
            cleaned_obs.extend(sat_lines)
        else:
            # Cas inattendu (par exemple, une ligne hors contexte) : on l'ajoute quand même.
            cleaned_obs.append(line)
            i += 1
    
    # Réassemblage : on remet ensemble le header et la section d'observations corrigée
    cleaned_content = "\n".join(header_lines + cleaned_obs) + "\n"
    
    # Sauvegarde du fichier nettoyé
    with open(output_file, 'w') as f:
        f.write(cleaned_content)
    
    print(f"Nettoyage terminé. Le fichier nettoyé est sauvegardé sous '{output_file}'.")

# Exemple d'utilisation :
if __name__ == '__main__':
    # Remplacer ces noms de fichiers par ceux souhaités.
    clean_rinex_observation_file('sept084m.25o', 'sept084m_clean.25o')





