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

    parser = argparse.ArgumentParser(description="*************** csv_to_kml ***************")
    # Import parameters
    parser.add_argument('input_file', type=str, help="input file from the Geostix, LOG, EXTEVENT or KML")
    parser.add_argument('-it', '--input_type', type=str, help="input file type between 'extevent' and 'log' (Default=log)",
                        default="log", choices=["kmltraj","extevent", "log"])
    parser.add_argument('-sep','--separator', type=str, help="separator used in the .csv file (Default=,)", default=",")
    parser.add_argument('-ro', type=str, help="RINEX observation file", default='')
    # Export parameters
    parser.add_argument('-o','--output_file', type=str, help="output file in .kml format (Default=./input_file.kml)", default="")
    parser.add_argument('-name','--doc_name', type=str, help="kml document name", default="")
    parser.add_argument('--quiet', action="store_true", help="print some statistics")
    
    # Apearance parameters
    parser.add_argument('-m','--mode', type=str, help="representation mode (Default=icon)",
                        default="icon", choices=["icon"])
    parser.add_argument('-ls','--label_scale', type=float, help="label scale (Default=2)", default=2)
    parser.add_argument('-is','--icon_scale', type=float, help="icon scale (Default=1)", default=1)
    parser.add_argument('-ih','--icon_href', type=str,
                        help="icon href (Default=http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png)",
                        default="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png")
    parser.add_argument('--show_pt_name', action="store_true", help="Hide the points names")
    
    # General parameters
    parser.add_argument('-dr','--data_range', type=str,
                        help="Range of data from start (s), to end (e), with a step (t) : (s,e,t). e and t are optional. If -it 'extevent' => Default=(0,-1,1), -it 'log' => Default=(0,-1,10)",
                        default='default')
    parser.add_argument('-am','--altitudemode', type=str,
                        help="See simplekml .Altitudemode (absolute, relativeToGround, clampToGround). (Default=absolute)",
                        default="absolute", choices=["absolute", "relativeToGround", "clampToGround"])

    # Point
    parser.add_argument('--show_point', action="store_false", help="Don't show points")
    # Line
    parser.add_argument('--show_line', action="store_false", help="Don't show the lines between points")
    # Confidence interval
    parser.add_argument('--show_conf_int', action="store_false", help="Don't show the confidence interval")
    parser.add_argument('-sp','--scale_factor_pla', type=float, help="Scale factor for planimetric uncertainty. (Default=1)", default=1)
    parser.add_argument('-mp','--incert_pla_max', type=float, help="Maximum planimetric uncertainty. (Default=Nan)", default=np.nan)
    parser.add_argument('-sh','--scale_factor_hig', type=float, help="Scale factor for altimetric uncertainty. (Default=1)", default=1)
    parser.add_argument('-mh','--incert_hig_max', type=float, help="Maximum altimetric uncertainty. (Default=Nan)", default=np.nan)

    # Buildings
    parser.add_argument('-buildings', type=str, help="Chemin vers le fichier .shp des bâtiments", default='')
    parser.add_argument('--show_buildings', action="store_false", help="Don't show buildings")
    parser.add_argument('-margin', type=float, help="margin (in meters) around the workfield for building modelisation (Default=20)", default=20)
    parser.add_argument('-departments', type=str,
                        help="input folder/file for shapefile building model. If there's multiple shapefiles, the code picks the first, etc.",
                        default='')
    parser.add_argument('-save_buildings', type=str,
                        help="If you want to save the shp file of your buildings, you can provide a folder path and name. If the name is 'intersection', it won't be saved. (Default=intersection)",
                        default="intersection")

    # Ephemerids
    parser.add_argument('--calc_ephemerids', action="store_false", help="Don't calculate the ephemerids")
    parser.add_argument('-rn','--rinex_name', type=str, help="Path of the observation or navigation rinex file", default='')
    
    # Frustum
    parser.add_argument('--show_orientation', action="store_false", help="Don't show frustum")
    parser.add_argument('-fr_sensor', type=float, help="distance factor of the near face of the frustum (Default=1)", default=1)
    parser.add_argument('-fr_focal', type=float, help="focal distance. (Default=10)", default=1)
    parser.add_argument('-fr_distance', type=float, help="distance between near and far plane. (Default=5)", default=5)
    parser.add_argument('-fr_alpha', type=float,  help="angle around X-axis. (Default=0)", default=0)
    parser.add_argument('-fr_beta', type=float,   help="angle around Y-axis. (Default=0)", default=0)
    parser.add_argument('-fr_gamma', type=float,  help="angle around Z-axis. (Default=0)", default=0)

    parser.add_argument('--temporal', action="store_true", help="Perform a temporal window calculation instead of the usual CSV->KML.")
    
    parser.add_argument('-d', '--date', type=str, default="23/02/2024",
                        help="Acquisition date (DD/MM/YYYY)")
    parser.add_argument('-start_time_kml', type=str, default="8h00",
                        help="Start time for KML traj (Default=8h00)")
    parser.add_argument('-end_time_kml', type=str, default="20h00",
                        help="End time for KML traj (Default=20h00)")
    parser.add_argument('-dist_step_kml', type=float, default=5,
                        help="Distance step for KML traj (Default=5)")
    parser.add_argument('-velocity_kml', type=float, default=1.5,
                        help="Velocity (m/s) for KML traj (Default=1.5)")

    parser.add_argument('--mnt', type=float, default=0.0,
                        help="Altitude offset or mean altitude for forcing Z (ex. 45).")
    parser.add_argument('--time_end', type=str, help="Heure de fin de simulation (format HH:MM:SS) pour étaler la simulation au-delà de la fin des relevés LOG", default=None)
    parser.add_argument('--detect_nlos', action="store_true", help="Detect collisions (NLOS).")
    parser.add_argument('-ll','--line_length', type=float, help="Line length for collisions (Default=250)", default=250)
    parser.add_argument('-start_time_log', type=str, default="8h00",
                        help="Start time for LOG trajectory simulation (e.g. 8h00)")
    parser.add_argument('-velocity_log', type=float, default=1.5,
                        help="Velocity (m/s) for LOG trajectory simulation (default=1.5)")
    args = parser.parse_args()
    
    # Conversion des chemins relatifs pour les fichiers situés dans le dossier 'test'
    # Pour le fichier d'entrée : si le type est 'kmltraj' on recherche dans le dossier 'kml', sinon dans 'log'
    if not os.path.isabs(args.input_file):
        if args.input_type == "kmltraj":
            args.input_file = functions.chemin_relatif(args.input_file, "kml")
        else:
            args.input_file = functions.chemin_relatif(args.input_file, "log")
    
    # Pour les fichiers RINEX (observation ou navigation)
    if args.rinex_name and not os.path.isabs(args.rinex_name):
        args.rinex_name = functions.chemin_relatif(args.rinex_name, "rinex")
    if args.ro and not os.path.isabs(args.ro):
        args.ro = functions.chemin_relatif(args.ro, "rinex")
    
    # Pour le shapefile des bâtiments
    if args.buildings and not os.path.isabs(args.buildings):
        args.buildings = functions.chemin_relatif(args.buildings, "shp")
    
    # Mode temporel (calcul de la fenêtre temporelle optimale)
    if args.temporal:
        # CAS 1: Trajectoire théorique => kmltraj
        if args.input_type == "kmltraj" and args.rinex_name :
            if args.buildings != "":
                dummy_kml = simplekml.Kml()
                buildings_dict = functions.shp2kml(args.buildings, dummy_kml)
                if not args.quiet:
                    print(f"{len(buildings_dict)} bâtiments chargés depuis {args.buildings}")
            else:
                buildings_dict = {}

            df_optimal = functions.compute_optimal_window_from_kml(
                kml_file=args.input_file,
                rinex_nav_file=args.rinex_name,
                buildings_dict=buildings_dict,
                start_time=args.start_time_kml,
                end_time=args.end_time_kml,
                distance_step=args.dist_step_kml,
                velocity=args.velocity_kml,
                time_step_sec=900,
                output_csv="resultats_optimal_window_kml.csv",
                mnt=args.mnt
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
                    buildings_dict = functions.shp2kml(args.buildings, dummy_kml)
                    if not args.quiet:
                        print(f"{len(buildings_dict)} bâtiments chargés depuis {args.buildings}")
                else:
                    buildings_dict = {}

                df_optimal = functions.compute_optimal_window_from_log(
                    data=data,
                    rinex_nav_file=args.rinex_name,
                    buildings_dict=buildings_dict,
                    time_step_sec=120,
                    output_csv="resultats_optimal_window_log.csv",
                    time_end=args.time_end,
                    start_time=args.start_time_log,
                    velocity=args.velocity_log,
                    rinex_obs_file=args.ro
                )
                print(df_optimal)
                
    else:
        tool.csv_to_kml(
             args.input_file,
             args.input_type,
             args.separator,
             args.output_file,
             args.doc_name,
             args.quiet,
             args.mode,
             args.label_scale,
             args.icon_scale,
             args.icon_href,
             args.show_pt_name,
             args.data_range,
             args.altitudemode,
             args.show_point,
             args.show_line,
             args.show_conf_int,
             args.scale_factor_pla,
             args.incert_pla_max,
             args.scale_factor_hig,
             args.incert_hig_max,
             args.show_buildings,
             args.margin,
             args.departments,
             args.save_buildings,
             args.calc_ephemerids,
             args.rinex_name,
             args.show_orientation,
             args.fr_sensor,
             args.fr_focal,
             args.fr_distance,
             args.fr_alpha,
             args.fr_beta,
             args.fr_gamma
        )


