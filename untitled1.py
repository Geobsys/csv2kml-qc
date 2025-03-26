#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 26 20:20:11 2025

@author: anthonydiallo
"""

def load_cleaned_rinex_obs(file_path):
    """
    Ouvre un fichier RINEX d’observation nettoyé en utilisant la fonction loadRinexO() 
    de gnsstoolbox et renvoie l’objet d’observation.

    Paramètres:
      file_path (str): chemin complet vers le fichier RINEX nettoyé.

    Retourne:
      obs (rinex_o.rinex_o): objet d’observation chargé, ou None en cas d’erreur.
    """
    from gnsstoolbox import rinex_o

    obs = rinex_o.rinex_o()
    try:
        obs.loadRinexO(file_path)
        print(f"[DEBUG] Chargement du fichier RINEX '{file_path}' réussi.")
    except Exception as e:
        print(f"[DEBUG] Erreur lors du chargement du fichier RINEX '{file_path}': {e}")
        return None

    # Affichage d'un aperçu du contenu
    try:
        # Si l'objet possède un attribut 'epochs' (liste des époques)
        if hasattr(obs, 'epochs') and obs.epochs:
            nb_epochs = len(obs.epochs)
            print(f"[DEBUG] Nombre d'époques lues: {nb_epochs}")
            # Afficher la première époque pour vérification
            print(f"[DEBUG] Première époque: {obs.epochs[0]}")
        else:
            print("[DEBUG] Aucun epoch trouvé dans l'objet RINEX.")
    except Exception as e:
        print(f"[DEBUG] Erreur lors de la lecture des époques: {e}")

    return obs

# Exemple d'utilisation :
if __name__ == "__main__":
    rinex_file = "test/rinex/sept084m_clean.25o"  # chemin vers votre fichier nettoyé
    obs_obj = load_cleaned_rinex_obs(rinex_file)
    if obs_obj is not None:
        print("[DEBUG] Le fichier RINEX est correctement chargé.")
    else:
        print("[DEBUG] Le chargement du fichier RINEX a échoué.")
