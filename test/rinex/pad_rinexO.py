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
    """
    Lit un fichier RINEX d'observation et complète les lignes d'observation pour qu'elles fassent exactement 80 caractères.

    Le script lit l'intégralité du fichier d'entrée et, pour chaque ligne qui ne commence pas par '>',
    vérifie si la ligne contient moins de 80 caractères (sans compter le retour à la ligne). 
    Si c'est le cas, la ligne est complétée avec des espaces jusqu'à atteindre exactement 80 caractères.
    Les lignes commençant par '>' (lignes d'époque) sont conservées telles quelles.
    Le contenu modifié est ensuite écrit dans le fichier spécifié par output_filename.

    Parameters
    ----------
    input_filename : str
        Chemin vers le fichier RINEX d'observation à lire.
    output_filename : str
        Chemin vers le fichier de sortie dans lequel le contenu modifié sera sauvegardé.

    Returns
    -------
    None

    Examples
    --------
    >>> pad_rinex_file("rinexO2503.25o.A", "rinexO2503_padded.25o.A")
    Fichier avec lignes padées écrit dans rinexO2503_padded.25o.A
    """
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
                # Si la longueur est inférieure à 80, on pad avec des espaces.
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
    """
    Fonction principale du script.

    Définit le fichier d'entrée et le fichier de sortie, puis appelle la fonction pad_rinex_file
    pour traiter le fichier RINEX d'observation et générer le fichier avec les lignes complétées.
    """
    input_filename = "rinexO2503.25o.A"   # Votre fichier nettoyé
    output_filename = "rinexO2503_padded.25o.A"  # Fichier de sortie
    pad_rinex_file(input_filename, output_filename)

if __name__ == '__main__':
    main()

