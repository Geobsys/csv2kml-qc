# -*- coding: utf-8 -*-

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@authors:
         mehdi daakir
         gabin bourlon
         axel debock
         felix mercier
         clement cambours
         liu zijan
"""

################################
# Imports :
################################
# Python files:
import csts
import functions
import tool  # On suppose que tool.py est dans le même dossier

# Packages:
import os
import simplekml
import pyproj
import fiona
import numpy as np
import pandas as pd
import argparse


################################
# Main
################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=csts.desc_tool)
    
    # Paramètres d'import
    parser.add_argument('input_file', type=str, help="Fichier d'entrée (GEOSTIX, KML, LOG, extevent)")
    parser.add_argument('-it', '--input_type', type=str,
                        help="Type de fichier d'entrée: 'kmltraj', 'extevent' ou 'log' (Default=log)",
                        default="log", choices=["kmltraj", "extevent", "log"])
    parser.add_argument('-sep', '--separator', type=str, help="Séparateur utilisé dans le fichier (Default=,)", default=",")
    
    # Option pour choisir le mode de calcul temporel (au lieu de la conversion CSV -> KML)
    parser.add_argument('--temporal', action="store_true", help="Calculer la fenêtre temporelle optimale (au lieu de convertir CSV en KML)")
    
    # Pour le mode kmltraj : on ajoute l'argument de date
    parser.add_argument('-d', '--date', type=str, help="Date de l'acquisition (format DD/MM/YYYY) (Default=23/02/2024)", default="23/02/2024")
    
    # Paramètres spécifiques aux trajectoires KML (ces paramètres ne seront utilisés qu'en mode kmltraj)
    parser.add_argument('start_time_kml', nargs='?', type=str, help="Heure de début pour la trajectoire KML (Default=8h00)", default="8h00")
    parser.add_argument('-end_time_kml', type=str, help="Heure de fin pour la trajectoire KML (Default=20h00)", default="20h00")
    parser.add_argument('-dist_step_kml', type=float, help="Pas en distance (m) pour discrétiser la polyligne KML (Default=5)", default=5)
    parser.add_argument('-velocity_kml', type=float, help="Vitesse moyenne en m/s (Default=1.5)", default=1.5)
    
    # Paramètres d'export
    parser.add_argument('-o', '--output_file', type=str, help="Fichier de sortie (Default=./input_file.kml)", default="")
    parser.add_argument('-name', '--doc_name', type=str, help="Nom du document (Default=input_file)", default="")
    
    parser.add_argument('--quiet', action="store_true", help="Ne pas afficher les statistiques ou autres informations")
    
    # Paramètres d'apparence
    parser.add_argument('-m', '--mode', type=str, help="Mode de représentation (Default=icon)", default="icon", choices=["icon"])
    parser.add_argument('-ls', '--label_scale', type=float, help="Échelle du label (Default=2)", default=2)
    parser.add_argument('-is', '--icon_scale', type=float, help="Échelle de l'icône (Default=1)", default=1)
    parser.add_argument('-ih', '--icon_href', type=str,
                        help="URL de l'icône (Default=http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png)",
                        default="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png")
    parser.add_argument('--show_pt_name', action="store_true", help="Afficher les noms des points dans le visualiseur")
    
    # Paramètres généraux
    parser.add_argument('-dr', '--data_range', type=str,
                        help="Intervalle de données : (s,e,t) (Default=(0,-1,10) pour log, (0,-1,1) pour extevent)",
                        default='default')
    parser.add_argument('-am', '--altitude_mode', type=str,
                        help="Mode d'altitude (absolute, relativeToGround, clampToGround) (Default=absolute)",
                        default="absolute", choices=["absolute", "relativeToGround", "clampToGround"])
    parser.add_argument('--time_end', type=str, help="Heure de fin de simulation (format HH:MM:SS) pour étaler la simulation au-delà de la fin des relevés LOG", default=None)
    # Options pour la conversion CSV -> KML
    parser.add_argument('--hide_pts', action="store_true", help="Ne pas afficher les points")
    parser.add_argument('--hide_lines', action="store_true", help="Ne pas afficher les lignes")
    parser.add_argument('--hide_conf_int', action="store_true", help="Ne pas afficher l'intervalle de confiance")
    parser.add_argument('-sp', '--scale_factor_pla', type=float, help="Facteur d'échelle pour l'incertitude planimétrique (Default=1)", default=1)
    parser.add_argument('-mp', '--incert_pla_max', type=float, help="Incertitude planimétrique max (Default=NaN)", default=np.nan)
    parser.add_argument('-sh', '--scale_factor_hig', type=float, help="Facteur d'échelle pour l'incertitude altimétrique (Default=1)", default=1)
    parser.add_argument('-mh', '--incert_hig_max', type=float, help="Incertitude altimétrique max (Default=NaN)", default=np.nan)
    
    # Buildings
    parser.add_argument('-buildings', type=str, help="Chemin vers le fichier .shp des bâtiments", default='')
    parser.add_argument('--hide_buildings', action="store_true", help="Ne pas afficher les bâtiments")
    parser.add_argument('-margin', type=float, help="Marge autour du chantier (Default=250)", default=250)
    parser.add_argument('-sb', '--save_buildings', type=str, help="Nom du fichier .shp des bâtiments filtrés (Default='intersection')", default="intersection")
    parser.add_argument('--show_extent', action="store_true", help="Afficher l'étendue des bâtiments", default=True)
    
    # Frustum
    parser.add_argument('--hide_frustum', action="store_true", help="Ne pas afficher le frustum")
    parser.add_argument('-fr_sensor', type=float, help="Facteur de distance pour la face proche (Default=1)", default=1)
    parser.add_argument('-fr_focal', type=float, help="Distance focale (Default=10)", default=10)
    parser.add_argument('-fr_distance', type=float, help="Distance entre les faces du frustum (Default=5)", default=5)
    parser.add_argument('-fr_alpha', type=float, help="Angle autour de l'axe X (Default=0)", default=0)
    parser.add_argument('-fr_beta', type=float, help="Angle autour de l'axe Y (Default=0)", default=0)
    parser.add_argument('-fr_gamma', type=float, help="Angle autour de l'axe Z (Default=0)", default=0)
    
    # RINEX data
    parser.add_argument('-ro', '--rinex_name_obs', type=str, help="Chemin du fichier RINEX d'observation", default='')
    parser.add_argument('-rn', '--rinex_name_nav', type=str, help="Chemin du fichier RINEX de navigation", default='')
    
    # >>>>> NOUVEL ARGUMENT : MNT <<<<<
    parser.add_argument('--mnt', type=float, default=0.0,
                        help="Valeur moyenne d'altitude (ex. 45) : pour forcer le Z ou ajuster la hauteur des points.")
    
    # Collision (NLOS)
    parser.add_argument('--detect_nlos', action="store_true", help="Effectuer la détection des collisions (NLOS)")
    parser.add_argument('-ll', '--line_length', type=float, help="Longueur de la ligne pour les rayons (Default=250)", default=250)
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("args.hide_pts =", args.hide_pts)
    
    # Mode temporel (calcul de la fenêtre temporelle optimale)
    if args.temporal:
        # CAS 1: Trajectoire théorique => kmltraj
        if args.input_type == "kmltraj" and args.rinex_name_nav and args.detect_nlos:
            if args.buildings != "":
                dummy_kml = simplekml.Kml()
                buildings_dict = functions.shp2kml(args.buildings, dummy_kml, show=False)
                if not args.quiet:
                    print(f"{len(buildings_dict)} bâtiments chargés depuis {args.buildings}")
            else:
                buildings_dict = {}
                
            # => compute_optimal_window_from_kml
            #   On lui passera la valeur MNT, qu'on utilisera pour forcer z= MNT
            #   (modifications dans functions.py)
            df_optimal = functions.compute_optimal_window_from_kml(
                kml_file=args.input_file,
                rinex_nav_file=args.rinex_name_nav,
                buildings_dict=buildings_dict,
                start_time=args.start_time_kml,
                end_time=args.end_time_kml,
                distance_step=args.dist_step_kml,
                velocity=args.velocity_kml,
                time_step_sec=60,
                output_csv="resultats_optimal_window_kml.csv",
                mnt = args.mnt
            )
            print(df_optimal)
            
        # CAS 2: Trajectoire réelle => extevent ou log
        else:
            if args.input_type == "extevent":
                labels = csts.extevent_labels
            elif args.input_type == "log":
                labels = csts.log_labels
            else:
                print("Pour le calcul temporel, utilisez 'kmltraj', 'extevent' ou 'log'.")
                exit(1)
            try:
                data = pd.read_csv(args.input_file, sep=args.separator, header=None)
            except Exception as e:
                print(f"Erreur lors de la lecture du fichier '{args.input_file}' avec le séparateur '{args.separator}': {e}")
                exit(1)
            try:
                data.columns = labels
            except Exception as e:
                print("Le type d'entrée n'est pas supporté. Vous pouvez changer le type avec -it.")
                exit(1)
                
            if args.input_type == "log":
                if args.buildings != "":
                    dummy_kml = simplekml.Kml()
                    buildings_dict = functions.shp2kml(args.buildings, dummy_kml, show=False)
                    if not args.quiet:
                        print(f"{len(buildings_dict)} bâtiments chargés depuis {args.buildings}")
                else:
                    buildings_dict = {}
                    
                # => compute_optimal_window_from_log
                #   qui va gérer la logique "z = h - mnt" si mnt!=0 (dans functions.py).
                df_optimal = functions.compute_optimal_window_from_log(
                    data=data,
                    rinex_nav_file=args.rinex_name_nav,
                    buildings_dict=buildings_dict,
                    time_step_sec=3600,
                    output_csv="resultats_optimal_window_log.csv",
                    time_end=args.time_end
                )
                print(df_optimal)
                
    else:
        # Si on n'est pas en mode temporel => CSV -> KML
        # => utilise la fonction tool.csv_to_kml
        tool.csv_to_kml(
            input_file=args.input_file,
            input_type=args.input_type,
            separator=args.separator,
            output_file=args.output_file,
            doc_name=args.doc_name,
            quiet=args.quiet,
            mode=args.mode,
            label_scale=args.label_scale,
            icon_scale=args.icon_scale,
            icon_href=args.icon_href,
            show_pt_name=args.show_pt_name,
            data_range=args.data_range,
            altitude_mode=args.altitude_mode,
            hide_pts=args.hide_pts,
            hide_lines=args.hide_lines,
            hide_conf_int=args.hide_conf_int,
            scale_factor_pla=args.scale_factor_pla,
            incert_pla_max=args.incert_pla_max,
            scale_factor_hig=args.scale_factor_hig,
            incert_hig_max=args.incert_hig_max,
            hide_buildings=args.hide_buildings,
            margin=args.margin,
            buildings=args.buildings,
            save_buildings=args.save_buildings,
            hide_frustum=args.hide_frustum,
            fr_sensor=args.fr_sensor,
            fr_focal=args.fr_focal,
            fr_distance=args.fr_distance,
            fr_alpha=args.fr_alpha,
            fr_beta=args.fr_beta,
            fr_gamma=args.fr_gamma,
            detect_nlos=args.detect_nlos,
            rinex_obs=args.rinex_name_obs,
            rinex_nav=args.rinex_name_nav,
            line_length=args.line_length,
            show_extent=args.show_extent
        )

