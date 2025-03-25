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
import csts
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
def custom_pt(kml, # simplekml object
			  pt, # a point from imported data, pd.DataFrame object
			  mode="icon", # point representation, string
			  name="", # point name, string python3 src/csv_to_kml.py test/EXTENVENT.LOG
			  description="", # point description, string
			  label_scale=2, # point name scale, int
			  icon_scale=1, # point icon scale, int
			  icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png", # point icon reference, string
			  show_pt_name=False, # show the point name, bool
			  altitudemode="absolute" # altitude mode in kml, string ("absolute", "relativeToGround", "clampToGround")
			  ):
	if(mode=="icon"):
		# append a point to the simplekml object
		pnt = kml.newpoint(altitudemode = altitudemode, description = description)
		if show_pt_name : 
			pnt.style.labelstyle.color = csts.colors_dict[csts.status_dict[pt['state']]["color"]]
			pnt.style.labelstyle.scale = label_scale
			pnt.name = name
		pnt.coords = [(pt['lon'],pt['lat'],pt['altitude'])]
		pnt.style.iconstyle.color = csts.colors_dict[csts.status_dict[pt['state']]["color"]]
		pnt.style.iconstyle.scale = icon_scale
		pnt.style.iconstyle.icon.href = icon_href
	return None


""" Creation of a kml line """
def custom_line(kml, # simplekml object
				pts_coords, # point coordinates, list (lenght 2 or more) of tuples (lenght 2 or 3) with floats
				status="None", # GNSS measure status (R, F, N or None), string
				mode="line", # line representation, string
				name="", # line name, string
				description="", # line description, string
				width=1, # line width scale, int
				altitudemode="absolute" # altitude mode in kml, string ("absolute", "relativeToGround", "clampToGround")
				):
	if (mode=="line"):
		#append a line
		ls = kml.newlinestring(name=name, description=description, altitudemode = altitudemode)
		ls.coords = pts_coords
		ls.extrude = 0
		ls.style.linestyle.width = width
		ls.style.linestyle.color = csts.colors_dict[csts.status_dict[status]["color"]]
	return None

""" Creation of a kml line """
def custom_int_conf(kml, # simplekml object
					pt,  # point object, pd.DataFrame object
					mode="pyr", # confidence interval representation, string
					name="", # confidence interval name, string
					altitudemode="absolute", # altitude mode in kml, string ("absolute", "relativeToGround", "clampToGround")
					color=csts.colors_dict["green"], # confidence interval color, string
					incert_pla_factor_E=1e5, # scale factor meters to degres Est, float
					incert_pla_factor_N=1e5, # scale factor meters to degres North, float
					scale_factor_pla=1, # scale factor planimetric show, float
					incert_pla_max=np.nan, # maximum planimetric uncertainty showed, float
					scale_factor_hig=1, # scale factor altimetric show, float
					incert_hig_max=np.nan # maximum altimetric uncertainty showed, float
					):
	if (mode=="pyr"):
		# adjusting showing options
		if pt["incert_pla"] > incert_pla_max :
			pt["incert_pla"] = incert_pla_max
		pt["incert_pla"] *= scale_factor_pla
		if pt["incert_hig"] > incert_hig_max :
			pt["incert_hig"] = incert_hig_max
		pt["incert_hig"] *= scale_factor_hig
		# switching from meters to equivalent degres
		incert_lon = pt["incert_pla"]*incert_pla_factor_E
		incert_lat = pt["incert_pla"]*incert_pla_factor_N
		# creating the pyramid (confidence interval) corners
		corners = np.array([(pt["lon"]-incert_lon, pt["lat"]		   , pt["altitude"]), 
			 	   			(pt["lon"]	   	     , pt["lat"]+incert_lat, pt["altitude"]), 
				   			(pt["lon"]+incert_lon, pt["lat"]		   , pt["altitude"]), 
				   			(pt["lon"]		     , pt["lat"]-incert_lat, pt["altitude"]), 
				   			(pt["lon"]		     , pt["lat"]		   , pt["altitude"] + pt["incert_hig"] )])
		# creating the description
		conf_int = [pt["incert_pla"], pt["incert_hig"], incert_lat, incert_lon]
		description_text = gen_description_conf_int(conf_int)
		#append the four faces of the pyramid
		pol = kml.newpolygon(name=name, description=description_text, altitudemode=altitudemode, extrude = 0)
		pol.outerboundaryis = [corners[0], corners[1], corners[-1], corners[0]]
		pol.style.polystyle.color = color
		pol = kml.newpolygon(name=name, description=description_text, altitudemode=altitudemode, extrude = 0)
		pol.outerboundaryis = [corners[1], corners[2], corners[-1], corners[1]]
		pol.style.polystyle.color = color
		pol = kml.newpolygon(name=name, description=description_text, altitudemode=altitudemode, extrude = 0)
		pol.outerboundaryis = [corners[2], corners[3], corners[-1], corners[2]]
		pol.style.polystyle.color = color
		pol = kml.newpolygon(name=name, description=description_text, altitudemode=altitudemode, extrude = 0)
		pol.outerboundaryis = [corners[3], corners[0], corners[-1], corners[3]]
		pol.style.polystyle.color = color
	return None

""" Creation of a kml frustum """
def custom_frustum(	kml,  # simplekml object
					pt,	  # point object, pd.DataFrame object
					product_rotation_matrix, # product between rotation  matrix
					mode="fur",  # frustum representation, string
					name="",	  # frustum name, string
					description="",  # point description, string
					altitudemode="absolute",  # altitude mode, string ("absolute", "relativeToGround", "clampToGround")
					incert_pla_factor_E = 1e-5,	# scale factor meters to degres Est
					incert_pla_factor_N = 1e-5,	# scale factor meters to degres North
					fr_sensor=1,	# size of the sensor
					fr_focal=10,	# size of the focal
					fr_distance=5,	# distance between the two faces of the frustum
					):
	if (mode == "fur") :
		far = (fr_sensor/fr_focal*fr_distance)
		lon,lat,altitude = pt['lon'], pt['lat'],pt['altitude']
		oX,oY,oZ = pt['oX'],pt['oY'],pt['oZ']

		# rotation matrix : allow to change the frustum orientation according to the camera
		rotation_matrixX = np.array([[1,          0,           0],
        							 [0, np.cos(oX), -np.sin(oX)],
        							 [0, np.sin(oX),  np.cos(oX)]])
		rotation_matrixY = np.array([[np.cos(oY) , 0, np.sin(oY)],
        							 [0          , 1,          0],
        							 [-np.sin(oY), 0, np.cos(oY)]])
		rotation_matrixZ = np.array([[np.cos(oZ), -np.sin(oZ), 0],
									 [np.sin(oZ),  np.cos(oZ), 0],
									 [0         , 0          , 1]])
				    
		# far and near points of the frustum and the difference of altitude between them
		frustum = [[ fr_sensor, 0        , fr_focal],
				   [ 0        , fr_sensor, fr_focal],
				   [-fr_sensor, 0        , fr_focal],
				   [ 0        ,-fr_sensor, fr_focal],
				   [ far      , 0        , fr_distance + fr_focal],
				   [ 0        , far      , fr_distance + fr_focal],
				   [-far      , 0        , fr_distance + fr_focal],
				   [ 0        , -far     , fr_distance + fr_focal]]
		
		# rotation of the frustum into the geographical reference frame
		frustum_o = frustum @ (rotation_matrixX @ rotation_matrixY @ rotation_matrixZ) @ product_rotation_matrix

		# translation of the frustum's points in WGS84
		frustum_o[:,0] *= incert_pla_factor_E
		frustum_o[:,1] *= incert_pla_factor_N
		frustum_o += np.array([lon, lat, altitude])

		# insert the frustum in the kml
		pol = kml.newpolygon(name=name, description=description, altitudemode=altitudemode, extrude=0)
		pol.outerboundaryis = [frustum_o[0], frustum_o[1], frustum_o[2], frustum_o[3], frustum_o[0]]
		pol.style.polystyle.color = simplekml.Color.blue # Default color
		ext = kml.newpolygon(name=name, description=description, altitudemode=altitudemode, extrude=0)
		ext.outerboundaryis = [frustum_o[4], frustum_o[5], frustum_o[6], frustum_o[7], frustum_o[4]]
		ext.style.polystyle.color = simplekml.Color.blue  # Default color
		for i in range(4):
			lin = kml.newlinestring(name=name, description=description)
			lin.coords = [frustum_o[i], frustum_o[i+4]]
			lin.altitudemode = altitudemode
			lin.style.linestyle.width = 2
			lin.style.linestyle.color = simplekml.Color.orange  # Default color
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
                # Utilise get() pour éviter l'erreur si la clé n'existe pas
                unity = csts.param_dict.get(i, {}).get("unity", "")
                value = f"{pt[i]} {unity}"
        else:
            # Si la valeur est en secondes, la formater en hh/mm/ss
            value = f"{int(pt[i]//3600)}h {int((pt[i]%3600)//60)}min {round((pt[i]%3600)%60,3)}s"
        if i in csts.param_dict:
            text += f'<tr><td style="text-align: left;">{csts.param_dict[i]["name"]}</td><td style="text-align: left;">{value}</td></tr>\n'
        else:
            text += f'<tr><td style="text-align: left;">{i}</td><td style="text-align: left;">{value}</td></tr>\n'
    text += '</table>'
    return text


""" Generate a description text for a line """
def gen_description_line(line) :
	# generate a description for a line based on the line points
	text = '<table style="border: 1px solid black;>'
	text += f'<tr><td">{" "}</td><td">{" "}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">{"Start"}</td><td style="text-align: left;">{line[1][0]}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">{"End"}</td><td style="text-align: left;">{line[1][-1]}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">{"Status"}</td><td style="text-align: left;">{csts.status_dict[line[0][0]]["name"]}</td></tr>\n'
	text += '</table>'
	return text

""" Generate a description text for a confidence interval """
def gen_description_conf_int(conf_int) :
	text = '<table style="border: 1px solid black;>'
	text += f'<tr><td">{" "}</td><td">{" "}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">Planimetric uncertainty (E/N)</td><td style="text-align: left;">{conf_int[0]}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">Altimetric uncertainty</td><td style="text-align: left;">{conf_int[1]}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">Latitude uncertainty </td><td style="text-align: left;">{conf_int[2]}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">Longitude uncertainty </td><td style="text-align: left;">{conf_int[3]}</td></tr>\n'
	text += '</table>'
	return text

""" Generate a description text for a building """
def gen_description_buildings(bat) :
	text = '<table style="border: 1px solid black;>'
	text += f'<tr><td">{" "}</td><td">{" "}</td></tr>\n'
	for champ in ["ID", "HAUTEUR", "Z_MIN_SOL", "Z_MAX_SOL", "Z_MIN_TOIT", "Z_MAX_TOIT"] :
		try :
			if champ != "ID" :
				text += f'<tr><td style="text-align: left;">{champ}</td><td style="text-align: left;">{bat[champ]} m</td></tr>\n'
			else :
				text += f'<tr><td style="text-align: left;">{champ}</td><td style="text-align: left;">{bat[champ]}</td></tr>\n'
		except :
			print("Your Buildings file is different from IGN BDTOPO.")
	text += '</table>'
	return text

""" Calculate the scale factor between projected meters (L93) and geographical degres (WGS84) """
def calcul_incert_pla_factor(data, size):
	transformer1 = pyproj.Transformer.from_crs(4326, 2154)
	transformer2 = pyproj.Transformer.from_crs(2154, 4326)
	
	point93 = transformer1.transform(np.mean(data['lat']), np.mean(data['lon']), np.mean(data['h']))
	E = point93[0] 
	N = point93[1] 
	h = point93[2]
	point1 = transformer2.transform(E	   , N	   , h)
	point2 = transformer2.transform(E + size, N + size, h)
	sigmaLon = point2[1] - point1[1]
	sigmaLat = point2[0] - point1[0]

	incert_pla_factor_E = sigmaLon / size
	incert_pla_factor_N = sigmaLat / size
	return incert_pla_factor_E, incert_pla_factor_N

""" Transform shapefile objects into kml objects """
def shp2kml(shp_file, kml, quiet=False):
    buildings_infos = {}
    if shp_file.endswith('.shp'):
        with fiona.open(shp_file, 'r') as shp:
            loading = 0
            unshowed_bat = 0
            for building in shp:
                building_id = str(building['properties']['ID'])
                building_height = building['properties']['HAUTEUR']
                building_ground_coords = np.array(building['geometry']['coordinates'][0])
                if quiet:
                    print(f"\nChecking building {building_id}: height={building_height}, ground_coords shape={building_ground_coords.shape}")
                try:
                    if building_height is not None and building_ground_coords.size > 0 and np.all(building_ground_coords[:, -1] != -1000):
                        if quiet:
                            print(f"Valid building: {building_id}")
                        building_roof_coords = building_ground_coords.copy()
                        building_roof_coords[:, -1] += building_height
                        buildings_infos[building_id] = {
                            "height": building_height,
                            "base_coords": building_ground_coords,
                            "roof_coords": building_roof_coords
                        }
                        if quiet:
                            print(f"Inserted {building_id} into buildings_infos")
                            print("Current dictionary keys:", list(buildings_infos.keys()))
                    # Conversion en WGS84 pour le dessin KML
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
                    if quiet:
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
    """
    Convertit (lon, lat, h) ellipsoïdal WGS84 vers (X, Y, Z) EPSG:4964 (ECEF).
    """
    transformer = pyproj.Transformer.from_crs(4326, 4964)
    coord_XYZ = transformer.transform(lat, lon, h)
    return np.array(coord_XYZ)

def XYZ_2_ENh(X, Y, Z):
    """
    Convertit (X, Y, Z) ECEF (EPSG:4964) vers (E, N, h) Lambert-93 "2.5D".
    """
    transformer = pyproj.Transformer.from_crs(4964, 2154)
    coord_ENh = transformer.transform(X, Y, Z)
    return np.array(coord_ENh)

def llh_2_llH(lon, lat, h, grid_path=csts.grid_path):
    """
    Convertit h ellipsoïdal en H orthométrique (via un fichier de grille).
    """
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
    """
    Convertit (X, Y, Z) ECEF (EPSG:4964) en (E, N, H) Lambert-93 + alt. orthométrique.
    Renvoie aussi (lon, lat) WGS84 si besoin.
    """
    # 1) ECEF => (lat, lon, h) ellipsoïdal
    transformer1 = pyproj.Transformer.from_crs(4964, 4326)
    coordLLh = transformer1.transform(X, Y, Z)

    # 2) h ellipsoïdal => H orthométrique
    transformer2 = pyproj.Transformer.from_pipeline("cct +proj=vgridshift +grids=" + grid_path)
    coordLLH = transformer2.transform(coordLLh[1], coordLLh[0], coordLLh[2])

    # 3) (lat, lon, H) => Lambert-93
    transformer3 = pyproj.Transformer.from_crs(4326, 2154)
    coordENH = transformer3.transform(coordLLH[1], coordLLH[0], coordLLH[2])

    # On renvoie (E, N, H_ortho, lon, lat)
    return coordENH[0], coordENH[1], coordENH[2], coordLLH[0], coordLLH[1]

def ENH_2_XYZ(pts, grid_path):
    """
    Convertit un tableau (E, N, H ortho) Lambert-93 => ECEF (X, Y, Z).
    """
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
    """
    Convertit un point (E, N, h) Lambert-93 "2.5D" => (lat, lon, h) WGS84.
    """
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

def compute_score(los, nlos, optimal_time, sim_start, sim_end, los_ref=85, nlos_ref=1, weights=(0.7, 0.3, 0.2)):
    """
    Calcule un score normalisé pour le meilleur instant (fenêtre optimale) d'un point.
    
    Paramètres :
      - los : nombre maximal de satellites LOS trouvés durant la simulation.
      - nlos : nombre de satellites NLOS au moment où le nombre de LOS est maximal.
      - optimal_time : heure (en secondes depuis minuit) où le nb_max de LOS est atteint.
      - sim_start : début de la simulation en secondes (ex. 0 pour 00h00).
      - sim_end : fin de la simulation en secondes (ex. 86399 pour 23h59).
      - los_ref : valeur de référence pour normaliser le nombre de LOS (ex. 85).
      - nlos_ref : valeur de référence pour le nombre de NLOS (ex. 10).
      - weights : pondérations (alpha, beta, gamma) pour LOS, NLOS et le critère temporel (la somme doit être 1).
      
    Retourne :
      - score : valeur entre 0 et 1, 1 correspondant au cas idéal.
    """
    # Normalisation du nb de LOS (borné à 1)
    los_factor = min(los / los_ref, 1.0)
    
    # Facteur NLOS : 1 si aucun NLOS, 0 si nlos >= nlos_ref (décroissance linéaire)
    nlos_factor = 1 - min(nlos / nlos_ref, 1.0)
    
    # Calcul de l'heure "idéale" (milieu de la plage)
    perfect_time = (sim_start + sim_end) / 2.0
    max_deviation = (sim_end - sim_start) / 2.0
    time_factor = 1 - (abs(optimal_time - perfect_time) / max_deviation)
    time_factor = max(0, min(time_factor, 1))
    
    # Score final pondéré
    score = 1000*(weights[0] * los_factor + weights[1] * nlos_factor + weights[2] * time_factor)
    return score

def compute_collisions_theorique(sat_dict, building_dict, dist_building=300, show=False):
    """
    Version adaptée pour un récepteur déjà en Lambert-93 + altitude (coordE, coordN, H).
    Le satellite, lui, est transformé ECEF -> Lambert93 localement,
    puis on calcule pt_along_line(...) en Lambert-93.
    """
    # Transformer les coordonnées satellites depuis ECEF (EPSG:4978) vers Lambert93 (EPSG:2154)
    transformer_sat_to_l93 = pyproj.Transformer.from_crs("EPSG:4978", "EPSG:2154", always_xy=True)

    for ekey in sat_dict:
        rcvr = sat_dict[ekey]["rcvr_infos"]

        # Au lieu de xr, yr, zr = rcvr["coordX"], on récupère E, N, H => la position du récepteur en Lambert-93
        Er, Nr, Hr = rcvr["coordE"], rcvr["coordN"], rcvr["H"]

        for skey, sat in sat_dict[ekey]["sat_infos"].items():
            xs_orig, ys_orig, zs_orig = sat["X"], sat["Y"], sat["Z"]

            # (1) Vérifier coords satellites valides
            if np.isnan([xs_orig, ys_orig, zs_orig]).any():
                sat["status"] = "UNKNOWN"
                sat["Building ID"] = "None"
                continue

            # (2) Transformation satellite ECEF -> Lambert-93
            try:
                xs_l93, ys_l93, zs_l93 = transformer_sat_to_l93.transform(xs_orig, ys_orig, zs_orig)
            except Exception:
                sat["status"] = "UNKNOWN"
                sat["Building ID"] = "None"
                continue

            # (3) Calcul d’un point intermédiaire sur la ligne (en Lambert-93) :
            #     On part de (Er,Nr,Hr) vers (xs_l93,ys_l93,zs_l93),
            #     et on se déplace de 1000 m.
            try:
                xn, yn, zn = pt_along_line((Er, Nr, Hr), (xs_l93, ys_l93, zs_l93), distance=1000)
            except Exception:
                sat["status"] = "UNKNOWN"
                sat["Building ID"] = "None"
                continue

            # (4) Test de collision (toujours en Lambert-93), on appelle ce point (en,nn,Hn).
            en, nn, Hn = xn, yn, zn

            collision_detected = False
            b_detected = "None"

            # (5) Parcours des bâtiments (base_coords/roof_coords sont aussi en Lambert-93).
            for bkey, building in building_dict.items():
                base_coords = np.array(building["base_coords"])
                # Distances par rapport au récepteur (Er,Nr,Hr)
                distances = np.linalg.norm(base_coords - np.array([Er, Nr, Hr]), axis=1)
                if np.min(distances) < dist_building:
                    aabb_min = np.min(building["base_coords"], axis=0)
                    aabb_max = np.max(building["roof_coords"], axis=0)
                    collision_status, _, _ = segment_intersects_bbox(
                        np.array([Er, Nr, Hr]),
                        np.array([en, nn, Hn]),
                        aabb_min,
                        aabb_max
                    )
                    if collision_status:
                        collision_detected = True
                        b_detected = bkey
                        break

            # (6) Attribuer LOS / NLOS
            if collision_detected:
                sat["status"] = "NLOS"
                sat["Building ID"] = b_detected
            else:
                sat["status"] = "LOS"
                sat["Building ID"] = "None"

    return sat_dict


def compute_optimal_window_from_kml(kml_file, rinex_nav_file, buildings_dict,
                                    start_time, end_time, distance_step, velocity,
                                    time_step_sec=180, output_csv="resultats_optimal_window.csv", mnt=45.0):
    """
    Calcule la fenêtre optimale (nb max de satellites LOS) pour une trajectoire
    KML "théorique" (points en Lambert-93) et un shapefile de bâtiments (Lambert-93).

    - On lit la polyligne KML (read_and_discretize_kml) => DataFrame points_list
      contenant coordX, coordY, coordZ (Lambert-93).
    - On fixe éventuellement H= mnt.
    - On simule dans le temps (boucle) en chargeant le RINEX Nav (calcSatCoord ECEF).
    - On appelle compute_collisions_theorique(...) pour déterminer LOS/NLOS.
    """

    # 1) Discrétisation
    points_list = read_and_discretize_kml(kml_file, start_time, end_time, distance_step, velocity)
    if points_list is None or points_list.empty:
        print("Erreur : Aucun point extrait de la trajectoire KML.")
        return None

    # 2) MNT forcé si besoin
    if mnt != 0.0:
        points_list["coordZ"] = mnt
        points_list["H"] = mnt  # altitude orthométrique "artificielle"

    def parse_time(hhmm):
        hh, mm = map(int, hhmm.replace("h", ":").split(":"))
        return hh * 3600 + mm * 60

    global_end_sec = parse_time(end_time)
    simulation_end = global_end_sec + 600
    base_date = datetime(2024, 2, 23)

    results = []
    print("\n[compute_optimal_window_from_kml] Début de la simulation de la fenêtre optimale.")

    # 3) Pour chaque point (Lambert-93)
    for i, pt in points_list.iterrows():
        pt_time = pt["time_sod"]
        best_time = pt_time
        best_los = -1
        best_nlos = 0

        simulation_times = []
        simulation_los = []

        # Rappel : coordX, coordY, coordZ en Lambert-93
        E_l93 = pt["coordX"]
        N_l93 = pt["coordY"]
        H_l93 = pt["coordZ"]

        print(f"\n[Point {i}] E={E_l93:.3f}, N={N_l93:.3f}, H={H_l93:.2f}, time_sod={pt_time}")

        t = float(pt_time)
        while t <= simulation_end:
            t_eval = t
            sim_dt = base_date + timedelta(seconds=t_eval)
            sim_dt = snap_to_nearest_epoch(sim_dt, snap_threshold=1)
            key = sim_dt.strftime("%Y %m %d %H %M %S")

            gnssdate = gpst.gpsdatetime(
                yyyy=sim_dt.year, mon=sim_dt.month, dd=sim_dt.day,
                h=sim_dt.hour, min=sim_dt.minute, sec=sim_dt.second
            )
            mjd_time = gnssdate.mjd
            print(f"  [Simulation] Date gnssdate: {key} | MJD: {mjd_time}")

            # 4) Lecture RINEX
            try:
                with open(rinex_nav_file, 'r') as f:
                    lines = f.readlines()
            except Exception as e:
                print(f"[compute_optimal_window_from_kml] Erreur ouverture RINEX: {e}")
                return None

            if not any("END OF HEADER" in line for line in lines):
                print("[compute_optimal_window_from_kml] Pas de header RINEX.")
                return None

            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
                    temp.writelines(lines)
                    temp_filename = temp.name
            except Exception as e:
                print(f"[compute_optimal_window_from_kml] Erreur fichier temp: {e}")
                return None

            Nav = orb.orbit()
            try:
                Nav.loadRinexN(temp_filename)
            except Exception as e:
                print(f"[compute_optimal_window_from_kml] Erreur chargement éphémérides: {e}")
                os.remove(temp_filename)
                return None
            os.remove(temp_filename)

            # 5) Calcul sat ECEF
            sat_cepoch_dict = {}
            for const in ["G","R","E","C"]:
                for prn in range(1,33):
                    try:
                        Xs, Ys, Zs, dte = Nav.calcSatCoord(const, prn, mjd_time, degree=0)
                        if (Xs, Ys, Zs)!=(0,0,0) and not np.isnan([Xs,Ys,Zs]).any():
                            sat_cepoch_dict[f"{const}{prn:02d}"] = {"X": Xs, "Y": Ys, "Z": Zs, "dte": dte}
                    except:
                        pass

            # 6) rcvr_infos en Lambert-93
            rcvr_dict = {
                "coordE": E_l93,
                "coordN": N_l93,
                "H": H_l93
            }
            current_sat_dict = { key: {"rcvr_infos": rcvr_dict, "sat_infos": sat_cepoch_dict} }

            if not current_sat_dict:
                n_los=0
                n_obs=0
            else:
                sim_key = list(current_sat_dict.keys())[0]
                print(f"    [DEBUG] Éphéméride associée: {sim_key}")
                # 7) Collisions => compute_collisions_theorique
                current_sat_dict = compute_collisions_theorique(current_sat_dict, buildings_dict, dist_building=300)
                local_sat_infos = current_sat_dict[sim_key]["sat_infos"].values()

                n_los  = sum(1 for s in local_sat_infos if s.get("status","UNKNOWN")=="LOS")
                n_obs = sum(1 for s in local_sat_infos if s.get("status","UNKNOWN")=="NLOS")

            print(f"    Nombre de satellites LOS = {n_los}, OBS = {n_obs}")
            simulation_times.append(t_eval)
            simulation_los.append(n_los)

            if n_los>best_los:
                best_los = n_los
                best_time= t_eval
                best_obs= n_obs

            t += time_step_sec

        print(f"  Temps simulés point {i}: {simulation_times}")
        print(f"  Nb LOS: {simulation_los}")

        # 8) Score final
        optimal_time_str = datetime.utcfromtimestamp(best_time).strftime("%H:%M:%S")
        final_score = compute_score(best_los, best_obs, best_time, sim_start=0, sim_end=86399)
        transformer_l93_to_wgs = pyproj.Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)
        lon_wgs, lat_wgs, alt_wgs = transformer_l93_to_wgs.transform(E_l93, N_l93, H_l93)

        results.append({
            "Point Index": i,
            "lon": lon_wgs,
            "lat": lat_wgs,
            "H ": alt_wgs,
            "Optimal Time": optimal_time_str,
            "Nb Max LOS": best_los,
            "Score": final_score
        })

    # 9) CSV
    df_results = pd.DataFrame(results)
    print("\n--- Résultats Fenêtre Optimale ---")
    print(df_results)
    df_results.to_csv(output_csv, index=False)
    print(f"[DEBUG] Fichier CSV = '{output_csv}'")
    sys.exit(0)

###############################################
# Fonctions de simulation temporelle pour LOG
###############################################
def compute_optimal_window_from_log(data, rinex_nav_file, buildings_dict,
                                    time_step_sec=180,
                                    output_csv="resultats_optimal_window_log.csv",
                                    time_end=""):
    """
    Calcule la fenêtre temporelle optimale pour chaque point du fichier LOG,
    en utilisant la fonction XYZ_2_ENH pour obtenir les coordonnées Lambert-93 (E, N)
    + altitude orthométrique (H), compatibles avec les données de bâtiments.

    Hypothèses :
      - data contient : "lat", "lon", "h" (ellipsoïdal), "date", "time", etc.
      - On peut avoir "coordX", "coordY", "coordZ" (ECEF) déjà présents.
      - Sinon, on calcule l’ECEF via llh_2_XYZ.
      - Puis on applique XYZ_2_ENH pour avoir (E, N, H ortho).
      - Les bâtiments sont en Lambert-93 planimétrique + altitude orthométrique (IGN69).
      - La simulation temporelle (boucle) charge le RINEX nav, calcule la position des
        satellites, et détermine s’il y a collision ou non (LOS/NLOS).
      - On cherche la meilleure fenêtre (temps) où le nombre de LOS est maximal.
    """

    results = []
    #print("\n[DEBUG] Début de la simulation de la fenêtre optimale pour le fichier LOG.")

    # Sous-fonction pour parser "HH:MM" en secondes
    def parse_time(hhmm):
        try:
            hh, mm = map(int, hhmm.replace("h", ":").split(":"))
            return hh * 3600 + mm * 60
        except Exception as e:
            #print(f"[DEBUG] Erreur lors du parsing de '{hhmm}': {e}")
            return 0

    # Détermination du temps de fin global (simulation_end)
    if time_end:
        # L'utilisateur a fourni "HH:MM" => on ajoute 60 minutes
        global_end_sec = parse_time(time_end)
        simulation_end = global_end_sec + 900
        #print(f"  [DEBUG] Temps de fin imposé: time_end = {time_end} -> simulation_end = {simulation_end} sec")
    else:
        # On balaie le DataFrame pour trouver la plus grande heure
        max_time_sod = 0
        for i, row in data.iterrows():
            try:
                time_str = str(row["time"]).strip('"')
                if ":" in time_str:
                    # Format "HH:MM:SS"
                    dt_tmp = datetime.strptime(row["date"].strip('"') + " " + time_str, "%d/%m/%Y %H:%M:%S.%f")
                else:
                    # time_str = nombre de secondes
                    seconds = float(time_str)
                    dt_tmp = datetime.strptime(
                        row["date"].strip('"') + " " +
                        f"{int(seconds % 86400 // 3600):02d}:"
                        f"{int((seconds % 86400 % 3600)//60):02d}:"
                        f"{seconds % 60:06.3f}",
                        "%d/%m/%Y %H:%M:%S.%f"
                    )
                time_sod = dt_tmp.hour * 3600 + dt_tmp.minute * 60 + dt_tmp.second
                if time_sod > max_time_sod:
                    max_time_sod = time_sod
            except Exception as e:
                #print(f"  [DEBUG] Erreur parsing ligne {i}: {e}")
                continue
        simulation_end = max_time_sod + 3600

    # Récupération d'une date de base
    try:
        base_date = datetime.strptime(data.iloc[0]["date"].strip('"'), "%d/%m/%Y")
    except Exception as e:
        #print(f"  [DEBUG] Erreur lors de l'extraction de la base date: {e}. Utilisation de la date par défaut.")
        base_date = datetime(2024, 2, 23)

    # Parcours de chaque point du fichier LOG
    for i, row in data.iterrows():
        # Lecture lat, lon, h ellipsoïdal
        try:
            lat_ellip = float(row["lat"])
            lon_ellip = float(row["lon"])
            h_ellip   = float(str(row["h"]).replace('"','').strip())
        except Exception as e:
            #print(f"[DEBUG] Ignoré la ligne {i} : coordonnées invalides ({e}).")
            continue
        if any(np.isnan(v) for v in [lat_ellip, lon_ellip, h_ellip]):
            #print(f"[DEBUG] Ignoré la ligne {i} : NaN détecté.")
            continue

        # Conversion date / heure
        try:
            date_str = str(row["date"]).strip('"')
            time_str = str(row["time"]).strip('"')
            if ":" in time_str:
                try:
                    sim_dt = datetime.strptime(date_str + " " + time_str, "%d/%m/%Y %H:%M:%S.%f")
                except:
                    # Retente sans microsecondes
                    sim_dt = datetime.strptime(date_str + " " + time_str, "%d/%m/%Y %H:%M:%S")
            else:
                # time_str est un float => conversion
                seconds = float(time_str)
                ss_mod = seconds % 86400
                hh = int(ss_mod // 3600)
                mm = int((ss_mod % 3600) // 60)
                ss = ss_mod % 60
                time_str_cvt = f"{hh:02d}:{mm:02d}:{ss:06.3f}"
                sim_dt = datetime.strptime(date_str + " " + time_str_cvt, "%d/%m/%Y %H:%M:%S.%f")
        except Exception as e:
            #print(f"[DEBUG] Erreur parsing date/heure pour la ligne {i}: {e}")
            continue

        # Temps du point (sec depuis minuit)
        point_time = sim_dt.hour * 3600 + sim_dt.minute * 60 + sim_dt.second

        # Récupération / calcul ECEF si pas déjà présent
        try:
            coordX = float(row["coordX"])
            coordY = float(row["coordY"])
            coordZ = float(row["coordZ"])
            #print(f"[DEBUG] Ligne {i} => ECEF extrait: ({coordX}, {coordY}, {coordZ})")
        except Exception:
            # On calcule via llh_2_XYZ (ellipsoïdal -> ECEF)
            try:
                receiver_xyz = llh_2_XYZ(lon_ellip, lat_ellip, h_ellip)
                coordX, coordY, coordZ = receiver_xyz
                #print(f"[DEBUG] Ligne {i} => ECEF calculé via llh_2_XYZ: ({coordX}, {coordY}, {coordZ})")
            except Exception as e2:
                print(f"[DEBUG] Erreur lors de la conversion ECEF ligne {i}: {e2}")
                continue

        # Ici, on applique la fonction XYZ_2_ENH pour avoir (E, N, H) en Lambert-93 + altitude ortho
        # + récup éventuelle du (lon2, lat2) si la fonction le fournit.
        # Exemple hypothétique de signature :
        #   def XYZ_2_ENH(X, Y, Z, grid_path=csts.grid_path):
        #       return (E, N, H, lon2, lat2)
        try:
            E_l93, N_l93, H_ortho, lon2, lat2 = XYZ_2_ENH(coordX, coordY, coordZ, csts.grid_path)
            #print(f"[DEBUG] Ligne {i} => XYZ_2_ENH => E={E_l93:.3f}, N={N_l93:.3f}, H={H_ortho:.3f}")
        except Exception as e3:
            print(f"[DEBUG] Erreur lors de XYZ_2_ENH ligne {i}: {e3}")
            continue

        # Variables de recherche "meilleure fenêtre"
        best_los = -1
        best_time = point_time
        best_obs = 0
        simulation_times = []
        simulation_los = []

        # Boucle temporelle
        t = point_time
        base_sim_date = sim_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        while t <= simulation_end:
            t_eval = t
            sim_current_dt = base_sim_date + timedelta(seconds=t_eval)
            sim_current_dt = snap_to_nearest_epoch(sim_current_dt, snap_threshold=1)

            key = sim_current_dt.strftime("%Y %m %d %H %M %S")
            gnssdate = gpst.gpsdatetime(
                yyyy=sim_current_dt.year,
                mon=sim_current_dt.month,
                dd=sim_current_dt.day,
                h=sim_current_dt.hour,
                min=sim_current_dt.minute,
                sec=sim_current_dt.second
            )
            print(f"[DEBUG] [Simulation] {key} | MJD={gnssdate.mjd}")
            mjd_time = gnssdate.mjd

            # On lit le fichier RINEX nav
            try:
                with open(rinex_nav_file, 'r') as f:
                    lines = f.readlines()
            except Exception as e:
                print(f"[DEBUG] Erreur ouverture Rinex: {e}")
                return None

            if not any("END OF HEADER" in line for line in lines):
                print("[DEBUG] Le header n'a pas été trouvé dans le fichier Rinex.")
                return None

            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
                    temp.writelines(lines)
                    temp_filename = temp.name
            except Exception as e:
                print(f"[DEBUG] Erreur écriture fichier temporaire: {e}")
                return None

            Nav = orb.orbit()
            try:
                Nav.loadRinexN(temp_filename)
                #print(f"  [DEBUG] Éphémérides chargées pour {key}.")
            except Exception as e:
                print(f"[DEBUG] Erreur loadRinexN: {e}")
                os.remove(temp_filename)
                return None

            os.remove(temp_filename)

            # Calcul position satellites
            sat_cepoch_dict = {}
            for const in ["G", "R", "E", "C"]:
                for prn in range(1, 33):
                    try:
                        Xs, Ys, Zs, dte = Nav.calcSatCoord(const, prn, mjd_time, degree=0)
                        if (Xs, Ys, Zs) != (0, 0, 0) and not any(math.isnan(v) for v in [Xs, Ys, Zs]):
                            sat_cepoch_dict[f"{const}{prn:02d}"] = {
                                "X": Xs,
                                "Y": Ys,
                                "Z": Zs,
                                "dte": dte
                            }
                    except:
                        continue

            # Dictionnaire local pour collisions
            # => On place le récepteur en Lambert93 + H ortho
            rcvr_dict = {
                "coordX": coordX,
                "coordY": coordY,
                "coordZ": coordZ,
                "coordE": E_l93,
                "coordN": N_l93,
                "H": H_ortho,
                # éventuellement "lon" et "lat" si utile ...
            }

            current_sat_dict = {
                key: {
                    "rcvr_infos": rcvr_dict,
                    "sat_infos": sat_cepoch_dict
                }
            }

            if not current_sat_dict or len(current_sat_dict.keys()) == 0:
                n_los, n_obs = 0, 0
            else:
                sim_key = list(current_sat_dict.keys())[0]
                #print(f"    [DEBUG] Collision check => Epoch: {sim_key}")
                current_sat_dict = compute_collisions(current_sat_dict, buildings_dict,
                                                      dist_building=300, show=False)
                local_sat_infos = current_sat_dict.get(sim_key, {}).get("sat_infos", {})
                n_los = sum(1 for v in local_sat_infos.values() if v.get("status", "UNKNOWN") == "LOS")
                n_obs = sum(1 for v in local_sat_infos.values() if v.get("status", "UNKNOWN") == "NLOS")

            print(f"    [DEBUG] LOS={n_los}, OBS={n_obs} (t_eval={t_eval}s)")
            simulation_times.append(t_eval)
            simulation_los.append(n_los)

            # Mise à jour de la "meilleure fenêtre"
            if n_los > best_los:
                best_los = n_los
                best_time = t_eval
                best_obs = n_obs

            t += time_step_sec

        # Fin simulation sur ce point
        optimal_time_str = datetime.utcfromtimestamp(best_time).strftime("%H:%M:%S")
        score = compute_score(best_los, best_obs, best_time, sim_start=0, sim_end=86399)

        # Enregistrement résultat
        results.append({
            "Point Index": i,
            "Lat (ellip)": lat_ellip,
            "Lon (ellip)": lon_ellip,
            "H ellip": h_ellip,
            # E, N, H_ortho si vous voulez les mettre en sortie
            "E (l93)": E_l93,
            "N (l93)": N_l93,
            "H ortho (m)": H_ortho,
            "Optimal Time": optimal_time_str,
            "Nb Max LOS": best_los,
            "Score": score
        })

    # Export CSV
    df_results = pd.DataFrame(results)
    print("\n--- Résultats Fenêtre Optimale ---")
    print(df_results)
    df_results.to_csv(output_csv, index=False)
    print(f"[DEBUG] Résultats enregistrés dans '{output_csv}'.")
    sys.exit(0)



#########################################
# (Les autres fonctions utilitaires restent inchangées)
#########################################

def compute_collisions(
    sat_dict,
    building_dict,
    dist_building=300,  # zone de proximité autour du récepteur
    show=False
):
    """
    Utilise pt_along_line + XYZ_2_ENH pour convertir le point intermédiaire
    en Lambert-93 (E,N,H) + lat/lon. Vérifie la collision dans l'AABB du bâtiment.
    
    => status "NLOS" si collision
    => status "LOS" si aucun
    => status "UNKNOWN" si coords invalides
    """
    for ekey in sat_dict:

        # Récup coords ECEF du récepteur
        xr = sat_dict[ekey]["rcvr_infos"]["coordX"]
        yr = sat_dict[ekey]["rcvr_infos"]["coordY"]
        zr = sat_dict[ekey]["rcvr_infos"]["coordZ"]
        
        # Récup coords ENH du récepteur (si besoin)
        er = sat_dict[ekey]["rcvr_infos"]["coordE"]
        nr = sat_dict[ekey]["rcvr_infos"]["coordN"]
        Hr = sat_dict[ekey]["rcvr_infos"]["H"]

        if show:
            print(f'[compute_collisions] Epoch {ekey} => {len(sat_dict[ekey]["sat_infos"])} satellites')

        # Pour chaque satellite
        for skey in sat_dict[ekey]["sat_infos"]:
            xs = sat_dict[ekey]["sat_infos"][skey]["X"]
            ys = sat_dict[ekey]["sat_infos"][skey]["Y"]
            zs = sat_dict[ekey]["sat_infos"][skey]["Z"]

            # Vérif coords valides
            if not np.isnan([xs, ys, zs]).any():
                
                # Point le long de la ligne
                xn, yn, zn = pt_along_line((xr, yr, zr), (xs, ys, zs), distance=1000)

                # Conversion en E, N, H + lon/lat apparents
                en, nn, Hn, lon_app, lat_app = XYZ_2_ENH(xn, yn, zn, csts.grid_path)

                # Stockage pour le KML
                sat_dict[ekey]["sat_infos"][skey]["lon_apparente"] = lon_app
                sat_dict[ekey]["sat_infos"][skey]["lat_apparente"] = lat_app
                sat_dict[ekey]["sat_infos"][skey]["H_apparente"]   = Hn

                collision_detected = False

                # Pour chaque bâtiment
                for bkey in building_dict:
                    base_coords = np.array(building_dict[bkey]["base_coords"])
                    # Distance min par rapport à la base
                    distances = np.linalg.norm(base_coords - np.array([er, nr, Hr]), axis=1)
                    distance_min = np.min(distances)

                    # Si c'est dans la zone dist_building
                    if distance_min < dist_building:
                        aabb_min = np.min(building_dict[bkey]["base_coords"], axis=0)
                        aabb_max = np.max(building_dict[bkey]["roof_coords"], axis=0)

                        collision_status, _, _ = segment_intersects_bbox(
                            np.array([er, nr, Hr]),
                            np.array([en, nn, Hn]),
                            aabb_min,
                            aabb_max
                        )
                        if collision_status:
                            collision_detected = True
                            sat_dict[ekey]["sat_infos"][skey]["Building ID"] = bkey
                            if show:
                                print(f"[compute_collisions] Satellite {skey} => collision with building {bkey}")
                            break

                # Statut final
                if collision_detected:
                    sat_dict[ekey]["sat_infos"][skey]["status"] = "NLOS"
                else:
                    sat_dict[ekey]["sat_infos"][skey]["status"] = "LOS"

            else:
                # Coord invalide => UNKNOWN
                sat_dict[ekey]["sat_infos"][skey]["status"] = "UNKNOWN"
                sat_dict[ekey]["sat_infos"][skey]["Building ID"] = "None"
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

