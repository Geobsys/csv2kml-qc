# -*- coding: utf-8 -*-

"""
@authors:
    mehdi daakir
    gabin bourlon
    axel debock
    felix mercier
    clement cambours
    liu zijan
    anthony diallo
    anthony evrard
    benoit esselami
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
from tqdm import tqdm
import contextlib
import concurrent.futures

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

def chemin_relatif(nom_fichier: str, type_fichier: str) -> str:
    """
    Retourne le chemin absolu d'un fichier en utilisant des chemins relatifs à partir du dossier 'test'.

    La structure du projet est la suivante :
        csv_to_kml/
            src/
                csv_to_kml.py
                functions.py
            test/
                kml/     -> pour les fichiers KML
                shp/     -> pour les fichiers shape
                log/     -> pour les fichiers LOG
                rinex/   -> pour les fichiers Rinex

    :param nom_fichier: Nom du fichier (par exemple 'short.kml' ou '20240223.LOG').
    :param type_fichier: Type de fichier, parmi 'kml', 'shp', 'log' ou 'rinex'.
    :return: Chemin absolu vers le fichier.
    """
    import os

    dossiers_valides = ['kml', 'shp', 'log', 'rinex']
    if type_fichier not in dossiers_valides:
        raise ValueError(
            f"Type de fichier '{type_fichier}' non supporté. Choisissez parmi {dossiers_valides}."
        )
    
    # Détermine le chemin du dossier courant (celui de functions.py, dans src)
    chemin_courant = os.path.dirname(os.path.abspath(__file__))
    # Le dossier 'test' se trouve au même niveau que 'src', on remonte d'un niveau et on rejoint 'test'
    dossier_test = os.path.abspath(os.path.join(chemin_courant, "..", "test"))
    
    # Construit le chemin complet en rejoignant le sous-dossier (kml, shp, log ou rinex) et le nom du fichier
    chemin_fichier = os.path.join(dossier_test, type_fichier, nom_fichier)
    
    return chemin_fichier


#####################################################################################################################
# --- Fonctions temporelles ---

def snap_to_nearest_epoch(dt, snap_threshold):
    """
   Arrondissement d'un datetime à l'époché la plus proche.

    Procédure :
      - Conversion de dt en secondes depuis minuit.
      - Calcul du reste de la division par snap_threshold.
      - Arrondissement à l'entier multiple de snap_threshold le plus proche
        (si l'écart est inférieur ou égal à snap_threshold).
      - Conversion du résultat en heures, minutes et secondes et mise à jour de dt.
    
    Paramètres :
      dt (datetime): Date et heure à arrondir.
      snap_threshold (int, optionnel): Seuil d'arrondissement en secondes 
                                       (par défaut 3600, soit 1 heure).
    
    Retourne :
      datetime: dt arrondi à l'époché la plus proche si la différence en secondes
                est inférieure ou égale à snap_threshold, sinon dt d'origine.
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

def compute_dop(receiver_position, sat_positions):
    """
    Calcul du DOP (Dilution of Precision) à partir de la position du récepteur et des positions satellites.
    
    Étapes :
    - Calcul des vecteurs de ligne de visée (los_vectors) et normalisation pour obtenir les vecteurs unitaires.
    - Construction de la matrice G en associant les composantes spatiales et une colonne de 1 pour modéliser l'erreur d'horloge.
    - Inversion de (G^T * G) pour obtenir la matrice de covariance Q.
    - Extraction des indices DOP à partir des termes diagonaux de Q :
        • GDOP : qualité globale (spatiale + temporelle) = √(trace(Q))
        • PDOP : position (X, Y, Z) = √(Q[0,0] + Q[1,1] + Q[2,2])
        • HDOP : horizontale (X, Y) = √(Q[0,0] + Q[1,1])
        • VDOP : verticale (Z) = √(Q[2,2])
        • TDOP : temporelle (horloge) = √(Q[3,3])
    
    Paramètres :
      receiver_position (array-like): Position du récepteur en coordonnées (X, Y, Z).
      sat_positions (np.ndarray): Tableau (n x 3) des positions satellites en coordonnées (X, Y, Z).
      
    Retourne :
      dict: Dictionnaire contenant les valeurs calculées de GDOP, PDOP, HDOP, VDOP et TDOP.
      
    Remarque :
      Nécessite au moins 4 satellites pour assurer une solution unique.
    """
    # Nombre de satellites
    nbr_sats = sat_positions.shape[0]
    if nbr_sats < 4:
        raise ValueError("At least 4 satellites are required to compute DOP values.")

    # Calcul des vecteurs unitaires de ligne de visée
    los_vectors = sat_positions - receiver_position
    distances = np.linalg.norm(los_vectors, axis=1).reshape(-1, 1)
    unit_vectors = los_vectors / distances

    # Construction de la matrice G (intégration de la composante temporelle)
    G = np.hstack((unit_vectors, np.ones((nbr_sats, 1))))

    # Inversion de (G^T * G) pour obtenir la matrice de covariance Q
    Q = np.linalg.inv(G.T @ G)

    # Extraction des valeurs DOP à partir de Q
    GDOP = np.sqrt(np.trace(Q))
    PDOP = np.sqrt(Q[0, 0] + Q[1, 1] + Q[2, 2])
    HDOP = np.sqrt(Q[0, 0] + Q[1, 1])
    VDOP = np.sqrt(Q[2, 2])
    TDOP = np.sqrt(Q[3, 3])

    # Assemblage et retour des indices DOP
    out_dict = {
        "GDOP": GDOP,
        "PDOP": PDOP,
        "HDOP": HDOP,
        "VDOP": VDOP,
        "TDOP": TDOP
    }
    return out_dict


def compute_collisions(sat_dict, building_dict, dist_building=300, show=False):
    """
    Calcul de collision entre les satellites et les bâtiments.
    
    Procédure :
      1. Transformation des coordonnées satellites depuis ECEF (EPSG:4978) vers Lambert-93 (EPSG:2154).
      2. Pour chaque satellite :
         - Vérification de la validité des coordonnées.
         - Transformation des coordonnées en Lambert-93.
         - Calcul d'un point intermédiaire le long de la ligne joignant le récepteur (en Lambert-93)
           à la position satellite, à une distance de 1000 m.
         - Test de collision entre le segment (récepteur - point intermédiaire) et la boite englobante 
           du bâtiment (définie par les coordonnées de base et de toit).
      3. Attribution du statut :
         - "NLOS" (Non Line Of Sight) si collision détectée.
         - "LOS" (Line Of Sight) sinon.
    
    Paramètres :
      sat_dict (dict): Dictionnaire contenant les informations du récepteur et des satellites.
      building_dict (dict): Dictionnaire des bâtiments avec leurs coordonnées en Lambert-93.
      dist_building (float, optionnel): Distance seuil (en m) pour considérer un bâtiment proche (par défaut 300).
      show (bool, optionnel): Flag pour afficher des informations (non utilisé ici).
    
    Retour :
      dict: Le dictionnaire sat_dict mis à jour avec les statuts "LOS" ou "NLOS" et l'ID du bâtiment en collision.
    """
    # Transformation des coordonnées satellites depuis ECEF vers Lambert-93
    transformer_sat_to_l93 = pyproj.Transformer.from_crs("EPSG:4978", "EPSG:2154", always_xy=True)

    for ekey in sat_dict:
        rcvr = sat_dict[ekey]["rcvr_infos"]
        # Extraction de la position du récepteur en Lambert-93 (E, N, H)
        Er, Nr, Hr = rcvr["coordE"], rcvr["coordN"], rcvr["H"]

        for skey, sat in sat_dict[ekey]["sat_infos"].items():
            xs_orig, ys_orig, zs_orig = sat["X"], sat["Y"], sat["Z"]

            # Vérification de la validité des coordonnées satellites
            if np.isnan([xs_orig, ys_orig, zs_orig]).any():
                sat["status"] = "UNKNOWN"
                sat["Building ID"] = "None"
                continue

            # Transformation des coordonnées satellite en Lambert-93
            try:
                xs_l93, ys_l93, zs_l93 = transformer_sat_to_l93.transform(xs_orig, ys_orig, zs_orig)
            except Exception:
                sat["status"] = "UNKNOWN"
                sat["Building ID"] = "None"
                continue

            # Calcul d'un point intermédiaire sur la ligne récepteur-satellite (distance = 1000 m)
            try:
                xn, yn, zn = pt_along_line((Er, Nr, Hr), (xs_l93, ys_l93, zs_l93), distance=1000)
                sat["sats_pos_l93"] = (xs_l93, ys_l93, zs_l93)
            except Exception:
                sat["status"] = "UNKNOWN"
                sat["Building ID"] = "None"
                continue

            # Définition du point intermédiaire en Lambert-93
            en, nn, Hn = xn, yn, zn

            collision_detected = False
            b_detected = "None"

            # Parcours des bâtiments pour détecter une collision
            for bkey, building in building_dict.items():
                base_coords = np.array(building["base_coords"])
                # Calcul des distances entre le récepteur et les points du bâtiment
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

            # Attribution du statut selon la détection de collision
            if collision_detected:
                sat["status"] = "NLOS"
                sat["Building ID"] = b_detected
            else:
                sat["status"] = "LOS"
                sat["Building ID"] = "None"

    return sat_dict

def candidate_simulation(candidate, points_list, cumulative, base_date, base_point_time,
                         Nav_data, buildings_dict, velocity, obs_data=None):
    """
    Simulation d'une fenêtre candidate pour une trajectoire et agrégation des statistiques.
    
    1) Création locale de l'objet Nav à partir de Nav_data
    2) Lecture du RINEX d'observation (si fourni)
    3) Parcours de chaque point de la trajectoire discrétisée
       - Calcul de la date GNSS (mjd_time)
       - Extraction/chargement des coordonnées satellites
       - Filtrage par angle d'élévation (exclusion des satellites sous l'horizon)
       - Calcul de collisions avec les bâtiments (LOS / NLOS)
       - Agrégation des statistiques (LOS, NLOS, PDOP/GDOP, etc.)
    4) Retourne un dictionnaire contenant un résumé de la simulation pour cette 'fenêtre' candidate.
    """
    import math
    import tempfile
    import contextlib
    import numpy as np
    
    # -------------------- Fonction utilitaire pour l'élévation --------------------
    def compute_elevation(userXYZ, satXYZ):
        """
        Calcule l'angle d'élévation (en degrés) d'un satellite
        par rapport à un récepteur en coordonnées ECEF.
        """
        # 1) Conversion de la position récepteur en (lat, lon, h)
        transformer_ecef_to_llh = pyproj.Transformer.from_crs("EPSG:4978", "EPSG:4326", always_xy=True)
        lat_u, lon_u, h_u = transformer_ecef_to_llh.transform(userXYZ[0], userXYZ[1], userXYZ[2])
        lat_u_rad = math.radians(lat_u)
        lon_u_rad = math.radians(lon_u)

        # 2) Calcul du vecteur récepteur->satellite en ECEF
        rx_sat = satXYZ - userXYZ

        # 3) Matrice de rotation ECEF -> ENU
        #    Source de référence classique : https://gssc.esa.int/navipedia/index.php/Transformations_between_ECEF_and_ENU_coordinates
        R = np.array([
            [-math.sin(lon_u_rad),                 math.cos(lon_u_rad),               0           ],
            [-math.sin(lat_u_rad)*math.cos(lon_u_rad), -math.sin(lat_u_rad)*math.sin(lon_u_rad), math.cos(lat_u_rad)],
            [ math.cos(lat_u_rad)*math.cos(lon_u_rad),  math.cos(lat_u_rad)*math.sin(lon_u_rad), math.sin(lat_u_rad)]
        ])

        enu = R @ rx_sat  # vecteur dans le repère local ENU
        e, n, u = enu

        # 4) Angle d’élévation = arcsin(Up / Norm(ENU))
        horiz_dist = math.sqrt(e**2 + n**2)
        elev = math.degrees(math.atan2(u, horiz_dist))
        return elev
    # --------------------------------------------------------------------------

    # Création locale de l'objet Nav
    Nav = orb.orbit()
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
            temp.writelines(Nav_data)
            nav_temp_filename = temp.name
    except Exception as e:
        print("DEBUG: Exception lors de la création du fichier temporaire Nav :", e)
        return None
    
    with contextlib.redirect_stdout(open(os.devnull, 'w')):
        try:
            Nav.loadRinexN(nav_temp_filename)
        except Exception as e:
            print("DEBUG: Exception dans Nav.loadRinexN :", e)
            os.remove(nav_temp_filename)
            return None
    os.remove(nav_temp_filename)

    # Lecture du RINEX d'observation (si fourni)
    Obs = None
    if obs_data is not None:
        Obs = rx.rinex_o()
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
                temp.writelines(obs_data)
                obs_temp_filename = temp.name
        except Exception as e:
            print("DEBUG: Exception lors de la création du fichier temporaire Obs :", e)
            Obs = None
        else:
            with contextlib.redirect_stdout(open(os.devnull, 'w')):
                try:
                    Obs.loadRinexO(obs_temp_filename)
                except Exception as e:
                    print("DEBUG: Exception dans Obs.loadRinexO :", e)
                    os.remove(obs_temp_filename)
                    Obs = None
            os.remove(obs_temp_filename)

    # Mise en cache des éphémérides, pour éviter de recalculer à chaque point
    ephemerides_cache = {}
    total_los = 0
    total_nlos = 0
    total_obstructed = 0
    dop_list = []

    # Conversion de la position ENH (Lambert-93) du récepteur en ECEF si besoin
    # pour le calcul d'élévation. La clé "coordX" / "coordY" / "coordZ" dans le
    # DataFrame est souvent l'ECEF déjà, mais vérifiez si c'est bien votre cas.
    # Si c'est du Lambert-93, il faut convertir. Exemple :
    #   rcv_ecef = ENH_2_XYZ([pt["coordE"], pt["coordN"], pt["H"]], csts.grid_path)
    
    for idx, pt in points_list.iterrows():
        # Simulation du temps
        effective_time = candidate + (pt["time_sod"] - base_point_time)
        sim_dt = base_date + timedelta(seconds=effective_time)
        sim_dt = snap_to_nearest_epoch(sim_dt, snap_threshold=1)
        key = sim_dt.strftime("%Y %m %d %H %M %S")
        gnssdate = gpst.gpsdatetime(yyyy=sim_dt.year, mon=sim_dt.month, dd=sim_dt.day,
                                    h=sim_dt.hour, min=sim_dt.minute, sec=sim_dt.second)
        mjd_time = gnssdate.mjd
        mjd_key = f"{mjd_time:.5f}"

        # Détermination de la position du récepteur en Lambert-93 (E, N, H)
        # S'il s'agit bien de colonnes Lambert-93, on doit passer en ECEF
        # si on veut calculer l'élévation. Exemple :
        if "coordX" in pt:
            # Supposons que coordX, coordY, coordZ soient déjà ECEF
            rcv_ecef = np.array([pt["coordX"], pt["coordY"], pt["coordZ"]], dtype=float)
            rcv_pos_dict = {"coordE": pt["coordX"], "coordN": pt["coordY"], "H": pt["coordZ"]}
        else:
            # Sinon, c'est peut-être la version (E, N, H) Lambert-93
            # => conversion en ECEF
            E, N, H = pt["E"], pt["N"], pt["H"]
            rcv_ecef = ENH_2_XYZ([[E, N, H]], csts.grid_path)[0]
            rcv_pos_dict = {"coordE": E, "coordN": N, "H": H}

        # Chargement / cache des éphémérides
        if mjd_key in ephemerides_cache:
            sat_cepoch_dict = ephemerides_cache[mjd_key]
        else:
            sat_cepoch_dict = {}
            for const in ["G", "R", "E", "C"]:
                # prn max peut être ajusté selon la constellation
                # ex: G = 32, R = 27, E = 36, C = 63, etc.
                for prn in range(1, 40):
                    try:
                        # L'argument "degree" dans calcSatCoord correspond à
                        # un degré pour interpolation polynomiale, et non à un
                        # masque d'élévation. On peut le mettre à 0.
                        Xs, Ys, Zs, dte = Nav.calcSatCoord(const, prn, mjd_time, degree=0)
                        if (Xs, Ys, Zs) != (0, 0, 0) and not np.isnan([Xs, Ys, Zs]).any():
                            # Vérification de l'élévation : on exclut si < 0°
                            sat_ecef = np.array([Xs, Ys, Zs], dtype=float)
                            elev_deg = compute_elevation(rcv_ecef, sat_ecef)
                            if elev_deg >= 5.0:
                                sat_cepoch_dict[f"{const}{prn:02d}"] = {
                                    "X": Xs, "Y": Ys, "Z": Zs, "dte": dte,
                                    # On peut stocker l'élévation si besoin
                                    "elevation_deg": elev_deg
                                }
                    except Exception:
                        pass
            ephemerides_cache[mjd_key] = sat_cepoch_dict

        # Assemblage du dictionnaire satellites/récepteur pour la suite
        current_sat_dict = {key: {"rcvr_infos": rcv_pos_dict, "sat_infos": sat_cepoch_dict}}
        current_sat_dict = compute_collisions(current_sat_dict, buildings_dict, dist_building=300)
        local_sat_infos = current_sat_dict[key]["sat_infos"]

        # Comptage des satellites LOS
        los_count = sum(1 for s in local_sat_infos.values() if s.get("status", "UNKNOWN") == "LOS")

        # Gestion du mode observation RINEX : NLOS => "Obstructed" si non observé
        if Obs is not None:
            epoch_obs = Obs.getEpochByMjd(gnssdate.mjd)
            observed_set = set()
            if epoch_obs is not None:
                for sat in epoch_obs.satellites:
                    if sat is not None and sat.obs.get("C1C", 0) > 0:
                        observed_set.add(f"{sat.const}{sat.PRN}")
            for sat_id, s in local_sat_infos.items():
                if s.get("status", "UNKNOWN") == "NLOS" and (sat_id not in observed_set):
                    s["status"] = "Obstructed"
            nlos_count = sum(1 for s in local_sat_infos.values() if s.get("status", "UNKNOWN") == "NLOS")
            obstructed_count = sum(1 for s in local_sat_infos.values() if s.get("status", "UNKNOWN") == "Obstructed")
        else:
            nlos_count = 0
            # Dans le cas théorique, on n'a pas d'Obs => tout "NLOS" reste NLOS
            obstructed_count = sum(1 for s in local_sat_infos.values() if s.get("status", "UNKNOWN") == "NLOS")

        # Accumulation
        total_los += los_count
        total_nlos += nlos_count
        total_obstructed += obstructed_count

        # Calcul du GDOP à partir des satellites LOS (en Lambert-93)
        # On récupère "sats_pos_l93" pour tous les satellites LOS
        sat_positions = [
            s["sats_pos_l93"] for s in local_sat_infos.values()
            if s.get("status", "UNKNOWN") == "LOS" and "sats_pos_l93" in s
        ]
        if len(sat_positions) >= 4:
            sats_array = np.array(sat_positions)
            rcv_pos = np.array([rcv_pos_dict["coordE"], rcv_pos_dict["coordN"], rcv_pos_dict["H"]])
            try:
                dop_dict = compute_dop(rcv_pos, sats_array)
                dop_value = dop_dict["GDOP"]
            except Exception:
                dop_value = np.nan
        else:
            dop_value = np.nan
        dop_list.append(dop_value)

    avg_gdop = np.nanmean(dop_list) if dop_list else np.nan
    total_observed = total_los + total_nlos + total_obstructed

    if Obs is not None:
        return {
            "Trajectory Start": datetime.utcfromtimestamp(candidate).strftime("%H:%M:%S"),
            "Total LOS": total_los,
            "Total NLOS": total_nlos,
            "Total Obstructed": total_obstructed,
            "Total Observed": total_observed,
            "Avg GDOP": avg_gdop
        }
    else:
        return {
            "Trajectory Start": datetime.utcfromtimestamp(candidate).strftime("%H:%M:%S"),
            "Total LOS": total_los,
            "Total Obstructed": total_obstructed,
            "Total Observed": total_observed,
            "Avg GDOP": avg_gdop
        }


#####################################################################################################################
# --- Fonctions de simulation temporelle ---

def read_and_discretize_kml(kml_file, start_time, end_time, distance_step, velocity):
    """
    Calcul de la fenêtre optimale à partir d'un fichier KML.
    
    Discrétisation de la trajectoire KML, simulation de candidats temporels et agrégation
    des statistiques (LOS, Obstructed, PDOP moyen).
    
    :return: DataFrame des résultats
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

def compute_optimal_window_from_kml(kml_file, rinex_nav_file, date_arg, buildings_dict,
                                    start_time, end_time, distance_step, velocity,
                                    time_step_sec, mnt, output_csv="resultats_optimal_window.csv"):
    """
    Calcul de la fenêtre optimale à partir d'un fichier KML.

    Procédure :
      - Discrétisation de la trajectoire extraite du fichier KML via read_and_discretize_kml.
      - Correction temporelle des points par soustraction du décalage initial.
      - Application d'une altitude fixe (mnt) aux points si spécifiée.
      - Calcul du cumul des distances parcourues pour déterminer la durée de la trajectoire.
      - Définition de l'intervalle temporel candidat (début et fin de simulation).
      - Chargement unique des données RINEX de navigation.
      - Simulation parallèle de candidats temporels via candidate_simulation.
      - Agrégation et tri des résultats basés sur la statistique (GDOP moyen ici).
      - Sauvegarde des résultats dans un fichier CSV.

    Paramètres :
      kml_file (str): Chemin vers le fichier KML contenant la trajectoire.
      rinex_nav_file (str): Chemin vers le fichier RINEX de navigation.
      date_arg (str): Date d'acquisition au format "dd/mm/yyyy".
      buildings_dict (dict): Dictionnaire des bâtiments avec leurs coordonnées.
      start_time (str): Heure de début de la trajectoire (exemple "8h00").
      end_time (str): Heure de fin de la trajectoire (exemple "20h00").
      distance_step (float): Pas de distance pour la discrétisation (en mètres).
      velocity (float): Vitesse utilisée pour la simulation (en m/s).
      time_step_sec (float): Pas temporel entre chaque candidat (en secondes).
      mnt (float, optionnel): Altitude fixe à appliquer aux points, par défaut 60.
      output_csv (str, optionnel): Nom du fichier CSV de sortie.

    Retour :
      DataFrame: Résumé des statistiques pour chaque fenêtre candidate (LOS, Obstructed, GDOP moyen, etc.).
    """
    # Discrétisation via read_and_discretize_kml
    points_df = read_and_discretize_kml(kml_file, start_time, end_time, distance_step, velocity)
    if points_df is None or points_df.empty:
        print("Erreur : Aucun point extrait de la trajectoire KML.")
        return None
    offset = points_df.iloc[0]["time_sod"]
    points_df["time_sod"] = points_df["time_sod"] - offset

    if mnt is not None:
        points_df["coordZ"] = mnt
        points_df["H"] = mnt

    def parse_time(hhmm):
        hh, mm = map(int, hhmm.replace("h", ":").split(":"))
        return hh * 3600 + mm * 60

    candidate_start_min = parse_time(start_time)
    global_end_sec = parse_time(end_time)
    simulation_end = global_end_sec + 600  # marge de 60 s
    base_date = datetime.strptime(date_arg, "%d/%m/%Y")
    base_point_time = points_df.iloc[0]["time_sod"]
    last_point_time = points_df.iloc[-1]["time_sod"]
    trajectory_duration = last_point_time - base_point_time
    candidate_start_max = simulation_end - trajectory_duration
    if candidate_start_max < candidate_start_min:
        candidate_start_max = candidate_start_min

    # Calcul du cumul des distances (en mètres)
    cumulative = [0.0]
    for i in range(1, len(points_df)):
        p1 = points_df.iloc[i-1]
        p2 = points_df.iloc[i]
        d = math.sqrt((p2["coordX"] - p1["coordX"])**2 +
                      (p2["coordY"] - p1["coordY"])**2 +
                      (p2["coordZ"] - p1["coordZ"])**2)
        cumulative.append(cumulative[-1] + d)
    points_df["time_sod"] = cumulative

    # --- Charger le fichier RINEX une seule fois ---
    try:
        with open(rinex_nav_file, 'r') as f:
            Nav_data = f.readlines()
    except Exception:
        print("Erreur lors de l'ouverture du fichier RINEX.")
        return None
    if not any("END OF HEADER" in line for line in Nav_data):
        print("Header RINEX non trouvé.")
        return None
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
            temp.writelines(Nav_data)
            temp_filename = temp.name
    except Exception:
        print("Erreur lors de la création du fichier temporaire.")
        return None
    Nav = orb.orbit()
    with contextlib.redirect_stdout(open(os.devnull, 'w')):
        try:
            Nav.loadRinexN(temp_filename)
        except Exception:
            os.remove(temp_filename)
            print("Erreur lors du chargement des éphémérides.")
            return None
    os.remove(temp_filename)
    # --- Fin du chargement RINEX ---

    results = []
    print("Traitement en cours...")
    candidate_values = list(range(int(candidate_start_min), int(candidate_start_max)+1, int(time_step_sec)))
    
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(candidate_simulation,
                                     candidate,
                                     pd.DataFrame(points_df),
                                     cumulative,
                                     base_date,
                                     base_point_time,
                                     Nav_data,
                                     buildings_dict,
                                     velocity)
                   for candidate in candidate_values]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures),
                           desc="Progression"):
            res = future.result()
            if res is not None:
                results.append(res)
    df_results = pd.DataFrame(results)
    df_results["Total Observed"] = df_results["Total LOS"] + df_results["Total Obstructed"]
    df_results["Trajectory Start_dt"] = pd.to_datetime(df_results["Trajectory Start"], format="%H:%M:%S")
    df_results = df_results.sort_values(by="Trajectory Start_dt").drop(columns=["Trajectory Start_dt"])
    df_results.to_csv(output_csv, index=False)
    # Vérification avant de chercher le minimum
    if df_results["Avg GDOP"].notna().any():
        best_candidate = df_results.loc[df_results["Avg GDOP"].idxmin()]["Trajectory Start"]
        print(f"\nFenêtre optimale estimée : {best_candidate}")
    else:
        print("\nAucune fenêtre avec GDOP valide détectée (tous les GDOP sont NaN). Vérifie la couverture satellite ou les positions dans les bâtiments.")
        best_candidate = None
    return df_results

def compute_optimal_window_from_log(data, rinex_nav_file, buildings_dict,
                                    time_step_sec, date_arg,
                                    end_time, start_time, velocity,
                                    rinex_obs_file, output_csv="resultats_optimal_window_log.csv"):
    """
    Calcul de la fenêtre optimale à partir de données LOG.

    Procédure :
      - Filtrage et limitation des données LOG pour obtenir un sous-ensemble (100 points).
      - Conversion des points LOG en coordonnées Lambert93.
      - Calcul du cumul des distances entre points pour déterminer le temps simulé (en fonction de la vitesse).
      - Définition de l'intervalle temporel candidat à partir de l'heure de début et de fin.
      - Chargement unique des données RINEX de navigation.
      - Chargement conditionnel des données RINEX d'observation (si fournies).
      - Simulation parallèle de candidats temporels via candidate_simulation.
      - Agrégation et tri des résultats selon la statistique (GDOP moyen ici).
      - Sauvegarde des résultats dans un fichier CSV.

    Paramètres :
      data (DataFrame): Données LOG brutes.
      rinex_nav_file (str): Chemin vers le fichier RINEX de navigation.
      buildings_dict (dict): Dictionnaire des bâtiments avec leurs coordonnées.
      time_step_sec (float): Pas temporel entre chaque candidat (en secondes).
      date_arg (str): Date d'acquisition au format "dd/mm/yyyy".
      end_time (str): Heure de fin de simulation (exemple "14:00").
      start_time (str): Heure de début de simulation (exemple "8h00").
      velocity (float): Vitesse utilisée pour la simulation (en m/s).
      rinex_obs_file (str): Chemin vers le fichier RINEX d'observation (peut être None).
      output_csv (str, optionnel): Nom du fichier CSV de sortie.

    Retour :
      DataFrame: Résumé des statistiques pour chaque fenêtre candidate (LOS, NLOS, Obstructed, GDOP moyen, etc.).
    """
    # Filtrage et limitation des données LOG (ici 100 points)
    data = data[(data["lat"].notnull()) & (data["lon"].notnull()) & (data["h"].notnull()) &
                (data["lat"] != "") & (data["lon"] != "") & (data["h"] != "")]
    data = data.head(100)

    def parse_time(hhmm):
        hh, mm = map(int, hhmm.replace("h", ":").split(":"))
        return hh * 3600 + mm * 60

    # Construction de la liste de points LOG (coordonnées en Lambert93)
    log_points = []
    for i, row in data.iterrows():
        try:
            lat = float(row["lat"])
            lon = float(row["lon"])
            h = float(str(row["h"]).replace('"', '').strip())
        except Exception:
            continue
        try:
            coordX = float(row["coordX"])
            coordY = float(row["coordY"])
            coordZ = float(row["coordZ"])
        except Exception:
            try:
                receiver_xyz = llh_2_XYZ(lon, lat, h)
                coordX, coordY, coordZ = receiver_xyz
            except Exception:
                continue
        try:
            E, N, H_val, _, _ = XYZ_2_ENH(coordX, coordY, coordZ, csts.grid_path)
        except Exception:
            continue
        log_points.append({"E": E, "N": N, "H": H_val})
    if not log_points:
        print("Aucun point valide extrait des données LOG.")
        return None

    # Calcul du cumul des distances entre points (en mètres)
    cumulative = [0.0]
    for i in range(1, len(log_points)):
        p1 = log_points[i-1]
        p2 = log_points[i]
        d = math.sqrt((p2["E"] - p1["E"])**2 + (p2["N"] - p1["N"])**2)
        cumulative.append(cumulative[-1] + d)
    for i, pt in enumerate(log_points):
        pt["time_sod"] = cumulative[i]
    trajectory_duration = cumulative[-1] / velocity

    candidate_start_min = parse_time(start_time)
    if end_time:
        simulation_end = parse_time(end_time) + 60
    else:
        simulation_end = candidate_start_min + trajectory_duration + 60
    candidate_start_max = simulation_end - trajectory_duration
    if candidate_start_max < candidate_start_min:
        candidate_start_max = candidate_start_min

    base_date = datetime.strptime(date_arg, "%d/%m/%Y")

    # Chargement du fichier Rinex de navigation une seule fois
    try:
        with open(rinex_nav_file, 'r') as f:
            Nav_data = f.readlines()
    except Exception:
        print("Erreur lors de l'ouverture du fichier Rinex de navigation.")
        return None
    if not any("END OF HEADER" in line for line in Nav_data):
        print("Header Rinex de navigation non trouvé.")
        return None
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
            temp.writelines(Nav_data)
            nav_temp_filename = temp.name
    except Exception:
        print("Erreur lors de la création du fichier temporaire pour navigation.")
        return None
    Nav = orb.orbit()
    with contextlib.redirect_stdout(open(os.devnull, 'w')):
        try:
            Nav.loadRinexN(nav_temp_filename)
        except Exception:
            os.remove(nav_temp_filename)
            print("Erreur lors du chargement des éphémérides de navigation.")
            return None
    os.remove(nav_temp_filename)

    # Chargement du fichier Rinex d'observation, si fourni
    Obs_data = None
    if rinex_obs_file is not None:
        try:
            with open(rinex_obs_file, 'r') as f:
                Obs_data = f.readlines()
        except Exception:
            Obs_data = None
        if Obs_data is not None and not any("END OF HEADER" in line for line in Obs_data):
            Obs_data = None

    results = []
    candidate_values = list(range(int(candidate_start_min), int(candidate_start_max)+1, int(time_step_sec)))
    
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(candidate_simulation,
                                     candidate,
                                     pd.DataFrame(log_points),
                                     cumulative,
                                     base_date,
                                     pd.DataFrame(log_points).iloc[0]["time_sod"],
                                     Nav_data,
                                     buildings_dict,
                                     velocity,
                                     obs_data=Obs_data)
                   for candidate in candidate_values]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures),
                           desc="Progression"):
            res = future.result()
            if res is not None:
                results.append(res)
    df_results = pd.DataFrame(results)
    df_results["Total Observed"] = (df_results["Total LOS"] +
                                    df_results["Total NLOS"] +
                                    df_results["Total Obstructed"])
    df_results["Trajectory Start_dt"] = pd.to_datetime(df_results["Trajectory Start"], format="%H:%M:%S")
    df_results = df_results.sort_values(by="Trajectory Start_dt").drop(columns=["Trajectory Start_dt"])
    df_results.to_csv(output_csv, index=False)
    # Vérification avant de chercher le minimum
    if df_results["Avg GDOP"].notna().any():
        best_candidate = df_results.loc[df_results["Avg GDOP"].idxmin()]["Trajectory Start"]
        print(f"\nFenêtre optimale estimée : {best_candidate}")
    else:
        print("\nAucune fenêtre avec GDOP valide détectée (tous les GDOP sont NaN). Vérifie la couverture satellite ou les positions dans les bâtiments.")
        best_candidate = None
    return df_results



