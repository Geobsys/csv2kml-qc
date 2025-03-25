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

###########
# Imports :
###########
# Python files:
import csts
# Packages:
import numpy as np
import pyproj                       # Coordinates transformations
import fiona                        # Shapefile management
import simplekml                    # KML management
import gpsdatetime as gpst          # GNSS date management
import gnsstoolbox.orbits as orb    # Orbit rinex management
import gnsstoolbox.rinex_o as rx    # Navigation rinex management
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import math
import os
import pandas as pd
import tempfile
import sys

""" Creation of a kml point """
def custom_pt(
    kml, # simplekml object
    pt,  # a point from imported data, pd.DataFrame object
    mode="icon", # point representation, string
    name="", # point name, string
    desc="", # point description, string
    label_scale=2, # point name scale, int
    icon_scale=1, # point icon scale, int
    icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png", # point icon reference, string
    show_pt_name=False, # show the point name, bool
    altitude_mode="absolute" # altitude mode in kml, string ("absolute","relativeToGround","clampToGround")
):
    if mode=="icon":
        # append a point to the simplekml object
        pnt = kml.newpoint(
            altitudemode=altitude_mode,
            description=desc
        )
        if show_pt_name:
            pnt.style.labelstyle.color = csts.colors_dict[csts.status_dict[pt['state']]["color"]]
            pnt.style.labelstyle.scale = label_scale
            pnt.name = name

        pnt.coords = [(pt['lon'], pt['lat'], pt['H'])]
        pnt.style.iconstyle.color = csts.colors_dict[csts.status_dict[pt['state']]["color"]]
        pnt.style.iconstyle.scale = icon_scale
        pnt.style.iconstyle.icon.href = icon_href

    return None

""" Creation of a kml line """
def custom_line(
    kml,  # simplekml object
    pts_coords, # list of tuples (2 or 3 floats)
    status="None", # GNSS measure status (R, F, N or None), string
    mode="line", # line representation, string
    name="", # line name, string
    description="", # line description, string
    width=1, # line width, int
    altitudemode="absolute" # altitude mode in kml
):
    if mode=="line":
        ls = kml.newlinestring(name=name, description=description, altitudemode=altitudemode)
        ls.coords = pts_coords
        ls.extrude = 0
        ls.style.linestyle.width = width
        ls.style.linestyle.color = csts.colors_dict[csts.status_dict[status]["color"]]
    return None

""" Creation of a kml confidence interval """
def custom_int_conf(
    kml,  # simplekml object
    pt,   # point (pandas Series)
    mode="pyr",  # representation mode
    name="",     # name for the interval
    altitudemode="absolute", # altitude mode in kml
    color=csts.colors_dict["green"],  # confidence interval color
    incert_pla_factor_E=1e5,  # scale factor meters to degrees Est, float
    incert_pla_factor_N=1e5,  # scale factor meters to degrees North, float
    scale_factor_pla=1,       # planimetric scale factor, float
    incert_pla_max=np.nan,    # maximum planimetric uncertainty, float
    scale_factor_hig=1,       # altimetric scale factor, float
    incert_hig_max=np.nan     # maximum altimetric uncertainty, float
):
    if mode=="pyr":
        # Adjust uncertainties with limits and scale factors
        if not np.isnan(incert_pla_max) and pt["incert_pla"] > incert_pla_max:
            pt["incert_pla"] = incert_pla_max
        pt["incert_pla"] *= scale_factor_pla
        if not np.isnan(incert_hig_max) and pt["incert_hig"] > incert_hig_max:
            pt["incert_hig"] = incert_hig_max
        pt["incert_hig"] *= scale_factor_hig

        # Convert uncertainties from meters to degrees
        incert_lon = pt["incert_pla"] * incert_pla_factor_E
        incert_lat = pt["incert_pla"] * incert_pla_factor_N

        # Compute pyramid corners
        corners = np.array([
            (pt["lon"]-incert_lon, pt["lat"],           pt["H"]),
            (pt["lon"],            pt["lat"]+incert_lat, pt["H"]),
            (pt["lon"]+incert_lon, pt["lat"],           pt["H"]),
            (pt["lon"],            pt["lat"]-incert_lat, pt["H"]),
            (pt["lon"],            pt["lat"],           pt["H"] + pt["incert_hig"])
        ])

        conf_int = [pt["incert_pla"], pt["incert_hig"], incert_lat, incert_lon]
        description_text = gen_description_conf_int(conf_int)

        # Create four pyramid faces
        for face in [[0,1], [1,2], [2,3], [3,0]]:
            pol = kml.newpolygon(name=name, description=description_text, altitudemode=altitudemode, extrude=0)
            pol.outerboundaryis = [corners[face[0]], corners[face[1]], corners[-1], corners[face[0]]]
            pol.style.polystyle.color = color

    return None

""" Creation of a kml frustum """
def custom_frustum(
    kml,  # simplekml object
    pt,   # point (pandas Series)
    product_rotation_matrix, # rotation matrix (numpy array)
    mode="fur",  # representation mode
    name="",     # frustum name
    description="",  # description
    altitudemode="absolute", # altitude mode
    incert_pla_factor_E=1e-5, # scale factor for meters->degrees (Est)
    incert_pla_factor_N=1e-5, # scale factor for meters->degrees (North)
    fr_sensor=1,      # sensor size
    fr_focal=10,      # focal length
    fr_distance=5,    # distance between near and far faces
):
    if mode == "fur":
        far = (fr_sensor / fr_focal * fr_distance)
        # Ici, on s'attend à ce que pt possède 'lon', 'lat', et 'altitude'
        # On peut utiliser 'height' ou 'H' selon le cas. Ici, on choisit 'altitude'
        lon, lat, altitude = pt['lon'], pt['lat'], pt['altitude'] if 'altitude' in pt else pt['H']
        oX, oY, oZ = pt['oX'], pt['oY'], pt['oZ']

        # Rotation matrices (local camera orientation)
        rotation_matrixX = np.array([
            [1,           0,            0],
            [0, np.cos(oX), -np.sin(oX)],
            [0, np.sin(oX),  np.cos(oX)]
        ])
        rotation_matrixY = np.array([
            [np.cos(oY), 0, np.sin(oY)],
            [0,          1,          0],
            [-np.sin(oY),0, np.cos(oY)]
        ])
        rotation_matrixZ = np.array([
            [np.cos(oZ), -np.sin(oZ), 0],
            [np.sin(oZ),  np.cos(oZ), 0],
            [0,           0,          1]
        ])

        frustum = [
            [ fr_sensor,  0       , fr_focal],
            [ 0,          fr_sensor, fr_focal],
            [-fr_sensor,  0       , fr_focal],
            [ 0,         -fr_sensor, fr_focal],
            [ far,       0       , fr_distance + fr_focal],
            [ 0,         far     , fr_distance + fr_focal],
            [-far,       0       , fr_distance + fr_focal],
            [ 0,        -far     , fr_distance + fr_focal]
        ]

        # Rotate the frustum into the geographical reference frame
        frustum_o = np.array(frustum) @ (rotation_matrixX @ rotation_matrixY @ rotation_matrixZ) @ product_rotation_matrix

        # Translate the frustum points into WGS84 coordinates
        frustum_o[:,0] *= incert_pla_factor_E
        frustum_o[:,1] *= incert_pla_factor_N
        frustum_o += np.array([lon, lat, altitude])

        # Create near and far polygons and the connecting lines
        pol = kml.newpolygon(name=name, description=description, altitudemode=altitudemode, extrude=0)
        pol.outerboundaryis = [tuple(frustum_o[i]) for i in range(4)] + [tuple(frustum_o[0])]
        pol.style.polystyle.color = simplekml.Color.blue

        ext = kml.newpolygon(name=name, description=description, altitudemode=altitudemode, extrude=0)
        ext.outerboundaryis = [tuple(frustum_o[i]) for i in range(4,8)] + [tuple(frustum_o[4])]
        ext.style.polystyle.color = simplekml.Color.blue

        for i in range(4):
            lin = kml.newlinestring(name=name, description=description)
            lin.coords = [tuple(frustum_o[i]), tuple(frustum_o[i+4])]
            lin.altitudemode = altitudemode
            lin.style.linestyle.width = 2
            lin.style.linestyle.color = simplekml.Color.orange

    return None

""" Generate a description text for a point """
def gen_description_pt(pt, max_index):
    index = pt.index
    text = '<table style="border: 1px solid black;">'
    text += '<tr><td></td><td></td></tr>\n'
    for i in index:
        if i == "state":
            value = f"{csts.status_dict[pt[i]]['name']}"
        elif csts.param_dict.get(i, {}).get("unity", "") != 's':
            if i == "index":
                value = f"{pt[i]}/{max_index}"
            else:
                value = f"{pt[i]} {csts.param_dict.get(i, {}).get('unity', '')}"
        else:
            value = f"{int(pt[i]//3600)}h {int((pt[i]%3600)//60)}min {round((pt[i]%3600)%60,3)}s"
        if i in csts.param_dict:
            text += f'<tr><td style="text-align: left;">{csts.param_dict[i]["name"]}</td><td style="text-align: left;">{value}</td></tr>\n'
        else:
            text += f'<tr><td style="text-align: left;">{i}</td><td style="text-align: left;">{value}</td></tr>\n'
    text += '</table>'
    return text

""" Generate a description text for a line """
def gen_description_line(line):
    text = '<table style="border: 1px solid black;">'
    text += '<tr><td></td><td></td></tr>\n'
    text += f'<tr><td style="text-align: left;">Start</td><td style="text-align: left;">{line[1][0]}</td></tr>\n'
    text += f'<tr><td style="text-align: left;">End</td><td style="text-align: left;">{line[1][-1]}</td></tr>\n'
    text += f'<tr><td style="text-align: left;">Status</td><td style="text-align: left;">{csts.status_dict[line[0][0]]["name"]}</td></tr>\n'
    text += '</table>'
    return text

""" Generate a description text for a confidence interval """
def gen_description_conf_int(conf_int):
    text = '<table style="border: 1px solid black;">'
    text += '<tr><td></td><td></td></tr>\n'
    text += f'<tr><td style="text-align: left;">Planimetric uncertainty (E/N)</td><td style="text-align: left;">{conf_int[0]}</td></tr>\n'
    text += f'<tr><td style="text-align: left;">Altimetric uncertainty</td><td style="text-align: left;">{conf_int[1]}</td></tr>\n'
    text += f'<tr><td style="text-align: left;">Latitude uncertainty</td><td style="text-align: left;">{conf_int[2]}</td></tr>\n'
    text += f'<tr><td style="text-align: left;">Longitude uncertainty</td><td style="text-align: left;">{conf_int[3]}</td></tr>\n'
    text += '</table>'
    return text

""" Generate a description text for a building """
def gen_description_buildings(building):
    text = '<table style="border: 1px solid black;">'
    text += '<tr><td></td><td></td></tr>\n'
    for champ in ["ID", "HAUTEUR", "Z_MIN_SOL", "Z_MAX_SOL", "Z_MIN_TOIT", "Z_MAX_TOIT"]:
        try:
            if champ != "ID":
                text += f'<tr><td style="text-align: left;">{champ}</td><td style="text-align: left;">{building[champ]} m</td></tr>\n'
            else:
                text += f'<tr><td style="text-align: left;">{champ}</td><td style="text-align: left;">{building[champ]}</td></tr>\n'
        except:
            print("Your Buildings file is different from IGN BDTOPO.")
    text += '</table>'
    return text

""" Calculate the scale factor between projected meters (L93) and geographical degrees (WGS84) """
def calcul_incert_pla_factor(data, size):
    transformer1 = pyproj.Transformer.from_crs(4326, 2154)
    transformer2 = pyproj.Transformer.from_crs(2154, 4326)
    if "h" in data.columns:
        height_col = "h"
    elif "height" in data.columns:
        height_col = "height"
    else:
        raise KeyError("Aucune colonne de hauteur ('h' ou 'height') trouvée dans le DataFrame.")
    point93 = transformer1.transform(np.mean(data['lat']), np.mean(data['lon']), np.mean(data[height_col]))
    E = point93[0]
    N = point93[1]
    h = point93[2]
    point1 = transformer2.transform(E, N, h)
    point2 = transformer2.transform(E + size, N + size, h)
    sigmaLon = point2[1] - point1[1]
    sigmaLat = point2[0] - point1[0]
    incert_pla_factor_E = sigmaLon / size
    incert_pla_factor_N = sigmaLat / size
    return incert_pla_factor_E, incert_pla_factor_N

""" Convert a Shapefile to KML and extract building information."""
def shp2kml(shp_file, kml, show=False):
    buildings_infos = {}
    if shp_file.endswith('.shp'):
        with fiona.open(shp_file, 'r') as shp:
            loading = 0
            unshowed_bat = 0
            for building in shp:
                building_id = str(building['properties']['ID'])
                building_height = building['properties']['HAUTEUR']
                building_ground_coords = np.array(building['geometry']['coordinates'][0])
                if show:
                    print(f"\nChecking building {building_id}: height={building_height}, ground_coords shape={building_ground_coords.shape}")
                try:
                    if building_height is not None and building_ground_coords.size > 0 and np.all(building_ground_coords[:, -1] != -1000):
                        if show:
                            print(f"Valid building: {building_id}")
                        building_roof_coords = building_ground_coords.copy()
                        building_roof_coords[:, -1] += building_height
                        buildings_infos[building_id] = {
                            "height": building_height,
                            "base_coords": building_ground_coords,
                            "roof_coords": building_roof_coords
                        }
                        if show:
                            print(f"Inserted {building_id} into buildings_infos")
                            print("Current dictionary keys:", list(buildings_infos.keys()))
                    building_ground_coords = building_ground_coords.reshape((len(building_ground_coords), 3))[:, :2]
                    transformer = pyproj.Transformer.from_crs(2154, 4326)
                    coordsWGS = transformer.transform(building_ground_coords[:, :1], building_ground_coords[:, 1:2])
                    coords = [(coordsWGS[1][i][0], coordsWGS[0][i][0], building_height) for i in range(len(building_ground_coords))]
                    pol = kml.newpolygon(
                        name=building['properties']['ID'],
                        altitudemode="relativeToGround"
                    )
                    pol.outerboundaryis = coords
                    pol.extrude = 1
                    pol.description = gen_description_buildings(building['properties'])
                    if show:
                        loading += 1
                        print(f"Conversion shp to kml {100 * loading // len(shp)} % \r", end="")
                except Exception as e:
                    unshowed_bat += 1
                    print(f"Error processing {building_id}: {e}")
    else:
        print("The file format is not supported.")
        return None
    return buildings_infos

def llh_2_XYZ(lon, lat, h):
    transformer = pyproj.Transformer.from_crs(4326, 4964)
    coord_XYZ = transformer.transform(lat, lon, h)
    return np.array(coord_XYZ)

def XYZ_2_ENh(X, Y, Z):
    transformer = pyproj.Transformer.from_crs(4964, 2154)
    coord_ENh = transformer.transform(X, Y, Z)
    return np.array(coord_ENh)

def llh_2_llH(lon, lat, h, grid_path=csts.grid_path):
    try:
        transformer = pyproj.Transformer.from_pipeline("cct +proj=vgridshift +grids=" + grid_path)
        coord_LLH = transformer.transform(lon, lat, h)
        return np.array(coord_LLH)
    except Exception as e:
        if " " in grid_path:
            print("Error: your folder path contains a space, and pyproj doesn't manage it ...")
        else:
            print(f"Error: There is an error with pyproj: {e}")
        return None

def XYZ_2_ENH(X, Y, Z, grid_path=csts.grid_path):
    transformer1 = pyproj.Transformer.from_crs(4964, 4326)
    coordLLh = transformer1.transform(X, Y, Z)
    transformer2 = pyproj.Transformer.from_pipeline("cct +proj=vgridshift +grids=" + grid_path)
    coordLLH = transformer2.transform(coordLLh[1], coordLLh[0], coordLLh[2])
    transformer3 = pyproj.Transformer.from_crs(4326, 2154)
    coordENH = transformer3.transform(coordLLH[1], coordLLH[0], coordLLH[2])
    return coordENH[0], coordENH[1], coordENH[2], coordLLH[0], coordLLH[1]

def ENH_2_XYZ(pts, grid_path):
    pts = np.array(pts)
    result = np.zeros_like(pts)
    transformer1 = pyproj.Transformer.from_crs(2154, 4326)
    transformer2 = pyproj.Transformer.from_pipeline("cct +proj=vgridshift +grids=" + grid_path)
    transformer3 = pyproj.Transformer.from_crs(4326, 4964)
    for i, pt in enumerate(pts):
        coordLLH = transformer1.transform(pt[0], pt[1], pt[2])
        coordLLh = transformer2.transform(coordLLH[1], coordLLH[0], coordLLH[2])
        O = coordLLH[2] - coordLLh[2]
        llhPt = (coordLLh[0], coordLLh[1], pt[2] + O)
        coordXYZ = transformer3.transform(llhPt[1], llhPt[0], llhPt[2])
        result[i] = coordXYZ
    return result

def ENh_2_llh(E, N, h):
    transformer = pyproj.Transformer.from_crs(2154, 4326)
    coord_llh = transformer.transform(E, N, h)
    return np.array(coord_llh)

""" get satellite informations """
def get_sat_infos(data, rinex_obs, rinex_nav):
    Obs = rx.rinex_o()
    Obs.loadRinexO(rinex_obs)
    Nav = orb.orbit()
    Nav.loadRinexN(rinex_nav)
    sat_dict = {}
    for row in data.itertuples(index=False, name="Pandas"):
        ind = data.loc[data["hour"] == getattr(row, "hour")].index[0]
        rcvr_dict = {
            "coordX": getattr(row, "coordX"),
            "coordY": getattr(row, "coordY"),
            "coordZ": getattr(row, "coordZ"),
            "lon": getattr(row, "lon"),
            "lat": getattr(row, "lat"),
            "h": getattr(row, "h"),
            "coordE": getattr(row, "coordE"),
            "coordN": getattr(row, "coordN"),
            "H": getattr(row, "H"),
            "incert_pla": getattr(row, "incert_pla"),
            "incert_hig": getattr(row, "incert_hig"),
            "index": ind
        }
        date = getattr(row, "date").split("/")
        year, month, day = date[2], date[1], date[0]
        hour = getattr(row, "hour").split(':')
        h_val, m_val, s_val = hour[0], hour[1], round(float(hour[2]), 0)
        date_hour = f"{year} {month} {day} {h_val} {m_val} {s_val}"
        gnssdate = gpst.gpsdatetime()
        gnssdate.rinex_t(date_hour)
        Ep = Obs.getEpochByMjd(gnssdate.mjd)
        if Ep is not None:
            sat_cepoch_dict = {}
            for sat in Ep.satellites:
                if sat is not None:
                    name_sat = f"{sat.const}{sat.PRN}"
                    try:
                        X, Y, Z, dte = Nav.calcSatCoord(sat.const, sat.PRN, gnssdate)
                        if not np.isnan(X):
                            sat_cepoch_dict[name_sat] = {
                                "X": X,
                                "Y": Y,
                                "Z": Z,
                                "dte": dte
                            }
                    except:
                        pass
            sat_dict[date_hour] = {
                "rcvr_infos": rcvr_dict,
                "sat_infos": sat_cepoch_dict
            }
    return sat_dict

def pt_along_line(P1, P2, distance=1000):
    P1 = np.array(P1)
    P2 = np.array(P2)
    direction = P2 - P1
    length = np.linalg.norm(direction)
    if length == 0:
        raise ValueError("P1 and P2 cannot be the same point")
    unit_direction = direction / length
    return tuple(P1 + unit_direction * distance)

def segment_intersects_bbox(ray_origin, ray_end, aabb_min, aabb_max):
    ray_direction = ray_end - ray_origin
    ray_length = np.linalg.norm(ray_direction)
    if ray_length == 0:
        return False, None, None
    ray_direction /= ray_length
    t_min = (aabb_min - ray_origin) / ray_direction
    t_max = (aabb_max - ray_origin) / ray_direction
    t1 = np.minimum(t_min, t_max)
    t2 = np.maximum(t_min, t_max)
    t_entry = np.max(t1)
    t_exit = np.min(t2)
    if t_entry <= t_exit and 0 <= t_exit <= ray_length:
        return True, t_entry, t_exit
    return False, None, None


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exemple de mise à jour dynamique des éphémérides dans la simulation de la fenêtre optimale.
Utilise gpsdatetime et gnsstoolbox.
"""

import os
import sys
import math
import tempfile
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pyproj

# Import des modules de gnss toolbox et gpsdatetime
import gpsdatetime as gpst
import gnsstoolbox.orbits as orb

# --- Fonctions utilitaires ---

def snap_to_nearest_epoch(dt, snap_threshold=3600):
    """
    Arrondit un datetime dt à l’époché la plus proche si la différence (en secondes)
    entre dt et l’arrondi est inférieure ou égale à snap_threshold.
    
    Avec snap_threshold=1, chaque seconde est pratiquement conservée.
    """
    total_sec = dt.hour * 3600 + dt.minute * 60 + dt.second
    remainder = total_sec % snap_threshold
    if remainder <= snap_threshold / 2:
        snapped_sec = total_sec - remainder
    else:
        snapped_sec = total_sec - remainder + snap_threshold
    if abs(total_sec - snapped_sec) <= snap_threshold:
        new_hour = snapped_sec // 3600
        new_minute = (snapped_sec % 3600) // 60
        new_second = snapped_sec % 60
        return dt.replace(hour=new_hour, minute=new_minute, second=new_second)
    return dt

def read_and_discretize_kml(kml_file, start_time, end_time, distance_step, velocity):
    """
    Lit un fichier KML et discrétise la trajectoire pour obtenir une série de points
    avec leurs coordonnées en Lambert93 et en WGS84 ainsi qu’un temps (en secondes depuis minuit).
    """
    def parse_time(hhmm):
        hh, mm = map(int, hhmm.replace("h", ":").split(":"))
        return hh * 3600 + mm * 60

    start_sec = parse_time(start_time)
    end_sec = parse_time(end_time)

    try:
        tree = ET.parse(kml_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Erreur de lecture du fichier KML : {e}")
        return None

    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    coords_text = None

    # Recherche d'un élément LineString
    for linestring in root.findall(".//kml:LineString", ns):
        coord_elem = linestring.find(".//kml:coordinates", ns)
        if coord_elem is not None and coord_elem.text:
            coords_text = coord_elem.text.strip()
            break

    if coords_text:
        raw_coords = coords_text.split()
        if len(raw_coords) < 2:
            print("Polyligne trop courte ou vide.")
            return None
        wgs_coords = []
        for rc in raw_coords:
            parts = rc.split(',')
            if len(parts) >= 2:
                lon_f, lat_f = float(parts[0]), float(parts[1])
                alt_f = float(parts[2]) if len(parts) > 2 else 0.0
                wgs_coords.append((lon_f, lat_f, alt_f))
        if len(wgs_coords) < 2:
            print("Pas assez de points pour discrétiser (LineString).")
            return None
    else:
        print("Aucun <LineString> trouvé => utilisation des <Point> pour reconstruire la trajectoire.")
        wgs_coords = []
        for placemark in root.findall(".//kml:Placemark", ns):
            pt_elem = placemark.find(".//kml:Point/kml:coordinates", ns)
            if pt_elem is not None and pt_elem.text:
                parts = pt_elem.text.strip().split(',')
                if len(parts) >= 2:
                    lon_f, lat_f = float(parts[0]), float(parts[1])
                    alt_f = float(parts[2]) if len(parts) > 2 else 0.0
                    wgs_coords.append((lon_f, lat_f, alt_f))
        if len(wgs_coords) < 2:
            print("Aucun LineString et moins de 2 <Point> => impossible de discrétiser.")
            return None

    # Conversion des coordonnées WGS84 en Lambert93
    transformer_wgs_to_l93 = pyproj.Transformer.from_crs(4326, 2154, always_xy=True)
    l93_coords = [transformer_wgs_to_l93.transform(lon, lat, alt) for lon, lat, alt in wgs_coords]

    def dist3D(a, b):
        return math.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2 + (b[2] - a[2])**2)

    points = []
    current_time_sod = float(start_sec)
    seg_idx = 0
    seg_p1 = l93_coords[0]
    seg_p2 = l93_coords[1]
    seg_len = dist3D(seg_p1, seg_p2)
    seg_used = 0.0
    current_pt = seg_p1
    transformer_l93_to_wgs = pyproj.Transformer.from_crs(2154, 4326, always_xy=True)

    def add_point(x, y, z, t_sod):
        if z <= 1.0:
            z = 45.0
        lon2, lat2, alt2 = transformer_l93_to_wgs.transform(x, y, z)
        points.append({
            "time_sod": t_sod,
            "lat": lat2,
            "lon": lon2,
            "H": alt2,
            "coordX": x,
            "coordY": y,
            "coordZ": z
        })

    add_point(*current_pt, current_time_sod)
    while not (current_time_sod >= end_sec or seg_idx >= len(l93_coords) - 1):
        step = distance_step
        remain = seg_len - seg_used
        if step <= remain:
            ratio = (seg_used + step) / seg_len
            nx = seg_p1[0] + ratio * (seg_p2[0] - seg_p1[0])
            ny = seg_p1[1] + ratio * (seg_p2[1] - seg_p1[1])
            nz = seg_p1[2] + ratio * (seg_p2[2] - seg_p1[2])
            seg_used += step
            current_pt = (nx, ny, nz)
        else:
            dist_left = step - remain
            current_pt = seg_p2
            seg_idx += 1
            if seg_idx >= len(l93_coords) - 1:
                break
            seg_p1 = l93_coords[seg_idx]
            seg_p2 = l93_coords[seg_idx + 1]
            seg_len = dist3D(seg_p1, seg_p2)
            seg_used = 0.0
            if dist_left < seg_len:
                ratio2 = dist_left / seg_len
                nx = seg_p1[0] + ratio2 * (seg_p2[0] - seg_p1[0])
                ny = seg_p1[1] + ratio2 * (seg_p2[1] - seg_p1[1])
                nz = seg_p1[2] + ratio2 * (seg_p2[2] - seg_p1[2])
                current_pt = (nx, ny, nz)
                seg_used = dist_left
            else:
                while dist_left >= seg_len and seg_idx < len(l93_coords) - 1:
                    dist_left -= seg_len
                    seg_idx += 1
                    if seg_idx >= len(l93_coords) - 1:
                        break
                    seg_p1 = l93_coords[seg_idx]
                    seg_p2 = l93_coords[seg_idx + 1]
                    seg_len = dist3D(seg_p1, seg_p2)
                    seg_used = 0.0
                if seg_idx < len(l93_coords) - 1 and dist_left > 0:
                    ratio3 = dist_left / seg_len
                    nx = seg_p1[0] + ratio3 * (seg_p2[0] - seg_p1[0])
                    ny = seg_p1[1] + ratio3 * (seg_p2[1] - seg_p1[1])
                    nz = seg_p1[2] + ratio3 * (seg_p2[2] - seg_p1[2])
                    current_pt = (nx, ny, nz)
                    seg_used = dist_left
        dt_sec = distance_step / velocity
        current_time_sod += dt_sec
        if current_time_sod > end_sec:
            current_time_sod = end_sec
        add_point(*current_pt, current_time_sod)
    df_points = pd.DataFrame(points)
    print(f"[read_and_discretize_kml] Discrétisation terminée avec {len(df_points)} points.")
    return df_points

# --- Fonction principale intégrant l'actualisation dynamique de gnssdate et la récupération des éphémérides ---

def compute_optimal_window_from_kml(kml_file, rinex_nav_file, buildings_dict,
                                    start_time, end_time, distance_step, velocity,
                                    time_step_sec=180, output_csv="resultats_optimal_window.csv"):
    # Discrétisation de la trajectoire depuis le fichier KML
    points_list = read_and_discretize_kml(kml_file, start_time, end_time, distance_step, velocity)
    if points_list is None or points_list.empty:
        print("Erreur : Aucun point extrait de la trajectoire KML.")
        return None

    def parse_time(hhmm):
        hh, mm = map(int, hhmm.replace("h", ":").split(":"))
        return hh * 3600 + mm * 60

    global_end_sec = parse_time(end_time)
    simulation_end = global_end_sec + 3600  # On simule jusqu'à end_time + 1h
    base_date = datetime(2024, 2, 23)

    results = []
    print("\n[compute_optimal_window_from_kml] Début de la simulation de la fenêtre optimale.")
    for i, pt in points_list.iterrows():
        pt_time = pt["time_sod"]
        best_time = pt_time
        best_los = -1
        simulation_times = []
        simulation_los = []
        t = float(pt_time)
        print(f"\n[Point {i}] Coordonnées: ({pt['lon']:.6f}, {pt['lat']:.6f}), H = {pt['H']:.2f}, time_sod = {pt_time}")
        while t <= simulation_end:
            t_eval = t
            # Calcul de la date de simulation (base_date + t_eval secondes)
            sim_dt = base_date + timedelta(seconds=t_eval)
            sim_dt = snap_to_nearest_epoch(sim_dt, snap_threshold=1)
            key = sim_dt.strftime("%Y %m %d %H %M %S")
            # Création dynamique de l'objet gnssdate pour cet instant
            gnssdate = gpst.gpsdatetime(yyyy=sim_dt.year, mon=sim_dt.month, dd=sim_dt.day,
                                        h=sim_dt.hour, min=sim_dt.minute, sec=sim_dt.second)
            print(f"  [Simulation] Date de gnssdate: {key} | MJD: {gnssdate.mjd}")
            mjd_time = gnssdate.mjd

            # Chargement du fichier RINEX navigation (à chaque simulation)
            try:
                with open(rinex_nav_file, 'r') as f:
                    lines = f.readlines()
            except Exception as e:
                print(f"[compute_optimal_window_from_kml] Erreur lors de l'ouverture du fichier Rinex: {e}")
                return None

            if not any("END OF HEADER" in line for line in lines):
                print("[compute_optimal_window_from_kml] Le header n'a pas été trouvé dans le fichier Rinex.")
                return None

            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
                    temp.writelines(lines)
                    temp_filename = temp.name
            except Exception as e:
                print(f"[compute_optimal_window_from_kml] Erreur lors de l'écriture du fichier temporaire: {e}")
                return None

            # Création d'un nouvel objet Orb et chargement du fichier RINEX
            Nav = orb.orbit()
            try:
                Nav.loadRinexN(temp_filename)
            except Exception as e:
                print(f"[compute_optimal_window_from_kml] Erreur lors du chargement des éphémérides: {e}")
                os.remove(temp_filename)
                return None
            os.remove(temp_filename)
            
            # Récupération des éphémérides pour cet instant simulé pour toutes les constellations
            sat_cepoch_dict = {}
            for const in ["G", "R", "E", "C"]:
                for prn in range(1, 33):
                    try:
                        # eph = Nav.getEphemeris(const, prn, gnssdate)
                        Xs, Ys, Zs, dte = Nav.calcSatCoord(const, prn, mjd_time, degree=0)
                        if (Xs, Ys, Zs) != (0, 0, 0) and not (math.isnan(Xs) or math.isnan(Ys) or math.isnan(Zs)):
                            sat_cepoch_dict[f"{const}{prn:02d}"] = {"X": Xs, "Y": Ys, "Z": Zs, "dte": dte}
                    except Exception:
                        continue

            # Préparation des informations du récepteur
            try:
                e_, n_, bigH_, _, _ = XYZ_2_ENH(pt["coordX"], pt["coordY"], pt["coordZ"], csts.grid_path)
            except Exception as e:
                print("Erreur dans XYZ_2_ENH :", e)
                e_, n_, bigH_ = None, None, None

            rcvr_dict = {
                "coordX": pt["coordX"],
                "coordY": pt["coordY"],
                "coordZ": pt["coordZ"],
                "coordE": e_,
                "coordN": n_,
                "H": bigH_
            }
            
            current_sat_dict = { key: {"rcvr_infos": rcvr_dict, "sat_infos": sat_cepoch_dict} }
            if not current_sat_dict or len(current_sat_dict.keys()) == 0:
                n_los = 0
            else:
                sim_key = list(current_sat_dict.keys())[0]
                print(f"    Éphéméride associée: {sim_key}")
                current_sat_dict = compute_collisions(current_sat_dict, buildings_dict, dist_building=300, show=False)
                local_sat_infos = current_sat_dict.get(sim_key, {}).get("sat_infos", {})
                n_los = sum(1 for v in local_sat_infos.values() if v.get("status", "UNKNOWN") == "LOS")
            print(f"    Nombre de satellites LOS pour ce point = {n_los}")
            simulation_times.append(t_eval)
            simulation_los.append(n_los)
            if n_los > best_los:
                best_los = n_los
                best_time = t_eval
                print(f"    Nouvelle meilleure fenêtre: t = {t_eval} sec (Nb LOS = {best_los})")
            t += time_step_sec
        print(f"  Temps simulés pour le point {i}: {simulation_times}")
        print(f"  Nb LOS pour le point {i}: {simulation_los}")
        optimal_time_str = datetime.utcfromtimestamp(best_time).strftime("%H:%M:%S")
        results.append({
            "Point Index": i,
            "Latitude": pt["lat"],
            "Longitude": pt["lon"],
            "Hauteur (H)": pt["H"],
            "Optimal Time": optimal_time_str,
            "Nb Max LOS": best_los
        })
    df_results = pd.DataFrame(results)
    print("\n--- Résultats Fenêtre Optimale ---")
    print(df_results)
    df_results.to_csv(output_csv, index=False)
    print(f"\nLes résultats ont été enregistrés dans '{output_csv}'.")
    sys.exit(0)

#########################################
# (Les autres fonctions utilitaires restent inchangées)
#########################################
# ... custom_pt, custom_line, custom_int_conf, custom_frustum, gen_description_pt, etc.

def compute_collisions(sat_dict, building_dict, dist_building=300, show=False):
    # Transformer les coordonnées satellites depuis ECEF (EPSG:4978) vers Lambert93 (EPSG:2154)
    transformer_sat_to_l93 = pyproj.Transformer.from_crs("EPSG:4978", "EPSG:2154", always_xy=True)
    
    for ekey in sat_dict:
        rcvr = sat_dict[ekey]["rcvr_infos"]
        xr, yr, zr = rcvr["coordX"], rcvr["coordY"], rcvr["coordZ"]
        
        for skey, sat in sat_dict[ekey]["sat_infos"].items():
            xs_orig, ys_orig, zs_orig = sat["X"], sat["Y"], sat["Z"]
            # Si les coordonnées satellites sont invalides, on marque le satellite comme "UNKNOWN"
            if np.isnan(xs_orig) or np.isnan(ys_orig) or np.isnan(zs_orig):
                sat["status"] = "UNKNOWN"
                sat["Building ID"] = "None"
                continue

            # Transformation des coordonnées satellites depuis ECEF vers Lambert93
            try:
                xs, ys, zs = transformer_sat_to_l93.transform(xs_orig, ys_orig, zs_orig)
            except Exception:
                sat["status"] = "UNKNOWN"
                sat["Building ID"] = "None"
                continue

            # Calcul d'un point intermédiaire sur la ligne entre le récepteur et le satellite
            try:
                # Ici, on choisit une distance fixe (par exemple 1000 m) le long de la ligne
                xn, yn, zn = pt_along_line((xr, yr, zr), (xs, ys, zs), distance=1000)
            except Exception:
                sat["status"] = "UNKNOWN"
                sat["Building ID"] = "None"
                continue

            # Pour le test d'intersection, on utilise directement ce point intermédiaire
            en, nn, Hn = xn, yn, zn

            collision_detected = False
            # Parcours de chaque bâtiment pour vérifier une éventuelle collision
            for bkey, building in building_dict.items():
                base_coords = np.array(building["base_coords"])
                distances = np.linalg.norm(base_coords - np.array([xr, yr, zr]), axis=1)
                if np.min(distances) < dist_building:
                    aabb_min = np.min(building["base_coords"], axis=0)
                    aabb_max = np.max(building["roof_coords"], axis=0)
                    collision_status, _, _ = segment_intersects_bbox(
                        np.array([xr, yr, zr]),
                        np.array([en, nn, Hn]),
                        aabb_min,
                        aabb_max
                    )
                    if collision_status:
                        collision_detected = True
                        b_detected = bkey  # sauvegarde l'ID du bâtiment en collision
                        break

            if collision_detected:
                sat["status"] = "NLOS"
                sat["Building ID"] = b_detected
            else:
                sat["status"] = "LOS"
                sat["Building ID"] = "None"
    return sat_dict

def draw_collision_rays(sat_dict, kml_layer):
    line_style_dict = {}
    for key, style in csts.line_styles.items():
        s = simplekml.Style()
        s.linestyle.color = style['color']
        s.linestyle.width = 2
        line_style_dict[key] = s
    for key in sat_dict:
        folder = kml_layer.newfolder(name=f"Vectors for Point at Epoch {key}", visibility=0)
        for skey in sat_dict[key]["sat_infos"]:
            sat_status = sat_dict[key]["sat_infos"][skey]["status"]
            desc = (
                '<table style="border: 1px solid black;">'
                '<tr><td></td><td></td></tr>\n'
                f'<tr><td style="text-align: left;">Nom :</td><td style="text-align: left;">{skey}</td></tr>\n'
                f'<tr><td style="text-align: left;">Epoch :</td><td style="text-align: left;">{key}</td></tr>\n'
                f'<tr><td style="text-align: left;">Status :</td><td style="text-align: left;">{sat_status}</td></tr>\n'
                f'<tr><td style="text-align: left;">Building ID :</td><td style="text-align: left;">{sat_dict[key]["sat_infos"][skey]["Building ID"]}</td></tr>\n'
                '</table>'
            )
            rcvr_lon = sat_dict[key]["rcvr_infos"]["lon"]
            rcvr_lat = sat_dict[key]["rcvr_infos"]["lat"]
            rcvr_H = sat_dict[key]["rcvr_infos"]["H"]
            sat_lon_app = sat_dict[key]["sat_infos"][skey]["lon_apparente"]
            sat_lat_app = sat_dict[key]["sat_infos"][skey]["lat_apparente"]
            sat_H_app = sat_dict[key]["sat_infos"][skey]["H_apparente"]
            end_coords = [(rcvr_lon, rcvr_lat, rcvr_H), (sat_lon_app, sat_lat_app, sat_H_app)]
            vector_placemark = kml_layer.newlinestring(name=f"Vector to {skey} ({sat_status})", description=desc)
            vector_placemark.coords = end_coords
            vector_placemark.altitudemode = simplekml.AltitudeMode.absolute
            style_key = 'LOS' if sat_status == 'LOS' else 'NLOS'
            vector_placemark.style = line_style_dict[style_key]
    return None

