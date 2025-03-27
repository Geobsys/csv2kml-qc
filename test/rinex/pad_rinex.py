#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 00:01:20 2025

@author: anthonydiallo
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ce script lit un fichier RINEX d'observation (nettoyé),
passe en revue toutes ses lignes d’observation (celles qui ne commencent pas par '>'),
et pour chacune, s’assure que la ligne fait exactement 80 caractères (sans compter le retour à la ligne).
Si ce n’est pas le cas, la ligne est complétée par des espaces.
Le fichier résultant est écrit dans un nouveau fichier.
"""

def pad_rinex_file(input_filename, output_filename):
    with open(input_filename, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        # Si la ligne commence par '>' (ligne d'époque), on la conserve telle quelle.
        if line.startswith('>'):
            new_lines.append(line)
        else:
            # Pour les lignes d'observation, on enlève le saut de ligne,
            # puis on pad avec des espaces pour atteindre 80 caractères.
            stripped = line.rstrip('\n')
            # Si la ligne est vide, on la conserve
            if not stripped:
                new_lines.append("\n")
            else:
                # Si la longueur est inférieure à 80, on pad
                if len(stripped) < 80:
                    padded = stripped.ljust(80)
                else:
                    # Si la ligne est déjà de longueur 80 ou plus, on la garde telle quelle.
                    padded = stripped
                new_lines.append(padded + "\n")
    
    with open(output_filename, 'w') as f:
        f.writelines(new_lines)
    print(f"Fichier avec lignes padées écrit dans {output_filename}")

def main():
    input_filename = "sept084o.25o.A"   # Votre fichier nettoyé
    output_filename = "sept084m_paddedo.25o.A"  # Fichier de sortie
    pad_rinex_file(input_filename, output_filename)

if __name__ == '__main__':
    main()
