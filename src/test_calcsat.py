# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# #!/usr/bin/env python3
# """
# Script de test pour la fonction calcSatCoord appliquée à plusieurs satellites.
# Ce script charge le fichier Rinex de navigation, puis pour différents instants de la journée,
# il crée un objet gnssdate (avec l'heure de simulation) et calcule les coordonnées des satellites sélectionnés.
# Les résultats (coordonnées X, Y, Z et dte) sont affichés pour vérification.
# """

# import sys
# from datetime import datetime, timedelta
# import gpsdatetime as gpst
# import gnsstoolbox.orbits as orb

# def test_calcSatCoord_multiple(rinex_nav_file, base_date, time_offsets, satellite_list):
#     """
#     Teste la fonction calcSatCoord pour les satellites donnés à différents instants.
    
#     Parameters:
#         rinex_nav_file (str): Chemin vers le fichier Rinex de navigation.
#         base_date (datetime): La date de base (exemple : 2024-02-23 à minuit).
#         time_offsets (list): Liste des décalages en secondes à ajouter à base_date.
#         satellite_list (list): Liste de tuples (constellation, PRN) à tester,
#                                par exemple [("G", 1), ("G", 2), ("G", 3), ...].
#     """
#     # Création d'un objet d'orbite et chargement du fichier Rinex
#     Nav = orb.orbit()
#     try:
#         Nav.loadRinexN(rinex_nav_file)
#     except Exception as e:
#         print(f"Erreur lors du chargement du fichier Rinex nav: {e}")
#         return

#     for offset in time_offsets:
#         # Calcul de l'instant simulé
#         dt_point = base_date + timedelta(seconds=offset)
#         # Formatage de l'instant pour le module gpsdatetime (exemple : "2024 02 23 06 00 00")
#         key = dt_point.strftime("%Y %m %d %H %M %S")
#         # Création et initialisation d'un nouvel objet gnssdate pour cet instant
#         gnssdate = gpst.gpsdatetime()
#         gnssdate.rinex_t(key)
        
#         print("=============================================")
#         print(f"Instant simulé : {key} | MJD: {gnssdate.mjd}")
        
#         for const, prn in satellite_list:
#             try:
#                 # Calcul des coordonnées pour le satellite spécifié
#                 Xs, Ys, Zs, dte = Nav.calcSatCoord(const, prn, gnssdate)
#                 print(f"Satellite {const}{prn:02d} - Coordonnées :")
#                 print(f"  X = {Xs}")
#                 print(f"  Y = {Ys}")
#                 print(f"  Z = {Zs}")
#                 print(f"  dte = {dte}")
#             except Exception as e:
#                 print(f"Erreur pour le satellite {const}{prn:02d}: {e}")
#         print("=============================================\n")

# if __name__ == "__main__":
#     # Si un chemin vers le fichier Rinex est passé en argument, on l'utilise, sinon on utilise "Journee.rnx"
#     if len(sys.argv) > 1:
#         rinex_nav_file = sys.argv[1]
#     else:
#         rinex_nav_file = "Journee.rnx"
    
#     # Définir la date de base (exemple : 2024-02-23 à minuit)
#     base_date = datetime(2024, 2, 23)
#     # Définir des instants de test en secondes depuis minuit : par exemple 06:00, 12:00, 18:00, 21:00
#     time_offsets = [21600, 43200, 64800, 75600]
    
#     # Liste des satellites à tester, ici on teste par exemple G01 à G07
#     satellite_list = [("G", 1), ("G", 2), ("G", 3), ("G", 4), ("G", 5), ("G", 6), ("G", 7)]
    
#     test_calcSatCoord_multiple(rinex_nav_file, base_date, time_offsets, satellite_list)


import gnsstoolbox.orbits as orb
import gpsdatetime as gpst

# 1. Instancier l'objet de calcul d'orbite
Orb = orb.orbit()

# 2. Charger le fichier RINEX navigation (éphémérides broadcast)
Orb.loadRinexN('Journee.rnx')  # exemple: fichier nav du 1er Jan 2023 (RINEX v3 nommé maob0010.23n)

# 3. Définir la date/heure d'intérêt
t = gpst.gpsdatetime(yyyy=2024, mon=2, dd=23, h=9, min=0, sec=0)  # 1er janv 2023 12h00 UTC
mjd_time = t.mjd

# 4. Sélectionner un satellite (ex: GPS PRN 21)
constellation = 'G'
prn = 1

# 5. Récupérer l'éphéméride broadcast correspondante la plus proche
eph = Orb.getEphemeris(constellation, prn, mjd_time)
if eph:
    print(f"Satellite {constellation}{prn} - TOE de l'éphéméride : {eph.tgps.st_iso_epoch()}")

# 6. Calculer les coordonnées du satellite à l'instant t
X, Y, Z, dte = Orb.calcSatCoord(constellation, prn, mjd_time, degree=0)
print(f"Coordonnées ECEF à {t.st_iso_epoch()} : X={X:.1f} m, Y={Y:.1f} m, Z={Z:.1f} m; dte={dte:.3f} µs")






