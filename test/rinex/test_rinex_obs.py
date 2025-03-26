    
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





