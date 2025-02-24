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
import pyproj						# Coordinates transformations
import fiona						# Shapefile management
import simplekml	                # KML management
import gpsdatetime as gpst			# GNSS date management
import gnsstoolbox.orbits as orb	# Orbit rinex management
import gnsstoolbox.rinex_o as rx	# Navigation rinex management

""" Creation of a kml point """
def custom_pt(
		      kml, # simplekml object
			  pt, # a point from imported data, pd.DataFrame object
			  mode="icon", # point representation, string
			  name="", # point name, string python3 src/csv_to_kml.py test/EXTENVENT.LOG
			  desc="", # point description, string
			  label_scale=2, # point name scale, int
			  icon_scale=1, # point icon scale, int
			  icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png", # point icon reference, string
			  show_pt_name=False, # show the point name, bool
			  altitude_mode="absolute" # altitude mode in kml, string ("absolute", "relativeToGround", "clampToGround")
			  ):
     
	if(mode=="icon"):
		# append a point to the simplekml object
		pnt = kml.newpoint(
                           altitudemode=altitude_mode,
                           description=desc
                           )
		if(show_pt_name): 
			pnt.style.labelstyle.color = csts.colors_dict[csts.status_dict[pt['state']]["color"]]
			pnt.style.labelstyle.scale = label_scale
			pnt.name = name
        
		pnt.coords = [(pt['lon'],pt['lat'],pt['H'])]
		pnt.style.iconstyle.color = csts.colors_dict[csts.status_dict[pt['state']]["color"]]
		pnt.style.iconstyle.scale = icon_scale
		pnt.style.iconstyle.icon.href = icon_href
          
	return None

""" Creation of a kml line """
def custom_line(
		        kml, # simplekml object
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

""" Creation of a kml confidence interval """
def custom_int_conf(
		            kml, # simplekml object
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
		corners = np.array([(pt["lon"]-incert_lon, pt["lat"]		   , pt["H"]), 
			 	   			(pt["lon"]	   	     , pt["lat"]+incert_lat, pt["H"]), 
				   			(pt["lon"]+incert_lon, pt["lat"]		   , pt["H"]), 
				   			(pt["lon"]		     , pt["lat"]-incert_lat, pt["H"]), 
				   			(pt["lon"]		     , pt["lat"]		   , pt["H"] + pt["incert_hig"] )])
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
def custom_frustum(
		           kml,  # simplekml object
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
def gen_description_pt(
                       pt,
                       max_index
                       ) :
	# Generate a description for a point based on the dataframes columns
	index = pt.index
	text = '<table style="border: 1px solid black;>'
	text += f'<tr><td">{" "}</td><td">{" "}</td></tr>\n'
	for i in index:
		if i == "state" :
			value = f"{csts.status_dict[pt[i]]['name']}"
		elif csts.param_dict[i]["unity"] != 's' :
			if i == "index" :
				value = f"{pt[i]}/{max_index}"
			else :
				value = f"{pt[i]} {csts.param_dict[i]['unity']}"
		else :
			value = f"{int(pt[i]//3600)}h {int((pt[i]%3600)//60)}min {round((pt[i]%3600)%60,3)}s"
		text += f'<tr><td style="text-align: left;">{csts.param_dict[i]["name"]}</td><td style="text-align: left;">{value}</td></tr>\n'
	text += '</table>'
	return text

""" Generate a description text for a line """
def gen_description_line(line):
	# generate a description for a line based on the line points
	text = '<table style="border: 1px solid black;>'
	text += f'<tr><td">{" "}</td><td">{" "}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">{"Start"}</td><td style="text-align: left;">{line[1][0]}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">{"End"}</td><td style="text-align: left;">{line[1][-1]}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">{"Status"}</td><td style="text-align: left;">{csts.status_dict[line[0][0]]["name"]}</td></tr>\n'
	text += '</table>'
	return text

""" Generate a description text for a confidence interval """
def gen_description_conf_int(conf_int):
	text = '<table style="border: 1px solid black;>'
	text += f'<tr><td">{" "}</td><td">{" "}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">Planimetric uncertainty (E/N)</td><td style="text-align: left;">{conf_int[0]}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">Altimetric uncertainty</td><td style="text-align: left;">{conf_int[1]}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">Latitude uncertainty </td><td style="text-align: left;">{conf_int[2]}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">Longitude uncertainty </td><td style="text-align: left;">{conf_int[3]}</td></tr>\n'
	text += '</table>'
	return text

""" Generate a description text for a building """
def gen_description_buildings(building):
	text = '<table style="border: 1px solid black;>'
	text += f'<tr><td">{" "}</td><td">{" "}</td></tr>\n'
	for champ in ["ID", "HAUTEUR", "Z_MIN_SOL", "Z_MAX_SOL", "Z_MIN_TOIT", "Z_MAX_TOIT"] :
		try :
			if champ != "ID" :
				text += f'<tr><td style="text-align: left;">{champ}</td><td style="text-align: left;">{building[champ]} m</td></tr>\n'
			else :
				text += f'<tr><td style="text-align: left;">{champ}</td><td style="text-align: left;">{building[champ]}</td></tr>\n'
		except :
			print("Your Buildings file is different from IGN BDTOPO.")
	text += '</table>'
	return text

""" Calculate the scale factor between projected meters (L93) and geographical degrees (WGS84) """
def calcul_incert_pla_factor(
                             data,
                             size
                             ):
	transformer1 = pyproj.Transformer.from_crs(4326,2154)
	transformer2 = pyproj.Transformer.from_crs(2154,4326)
	
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

"""Convert a Shapefile to KML and extract building information."""
def shp2kml(
            shp_file,
            kml,
            show=False
            ):

    # Create a dictionary to store building information
    buildings_infos = {}

    # Check if the file is a Shapefile
    if shp_file.endswith('.shp'):
        
        # Open the Shapefile
        with fiona.open(shp_file, 'r') as shp:
            
            loading = 0
            unshowed_bat = 0

            # Iterate over each building in the Shapefile
            for building in shp:
                building_id = str(building['properties']['ID'])
                building_height = building['properties']['HAUTEUR']
                building_ground_coords = np.array(building['geometry']['coordinates'][0])

                # Debugging prints
                if(show):
                    print(f"\nChecking building {building_id}: height={building_height}, ground_coords shape={building_ground_coords.shape}")

                try:
                    # Ensure data is valid
                    if building_height is not None and building_ground_coords.size > 0 and np.all(building_ground_coords[:, -1] != -1000):
                        if(show):
                            print(f"Valid building: {building_id}")

                        # Make a copy before modifying
                        building_roof_coords = building_ground_coords.copy()
                        building_roof_coords[:,-1] += building_height

                        # Store in dictionary
                        buildings_infos[building_id] = {
                                                        "height": building_height,
                                                        "base_coords": building_ground_coords,
                                                        "roof_coords": building_roof_coords
                                                       }

                        # Debugging prints
                        if(show):
                            print(f"Inserted {building_id} into buildings_infos")
                            print("Current dictionary keys:", list(buildings_infos.keys()))
                    
                    # Reshape and convert coordinates
                    building_ground_coords = building_ground_coords.reshape((len(building_ground_coords), 3))[:, :2]
                    transformer = pyproj.Transformer.from_crs(2154,4326)
                    coordsWGS = transformer.transform(building_ground_coords[:, :1], building_ground_coords[:, 1:2])
                    coords = [(coordsWGS[1][i][0], coordsWGS[0][i][0], building_height) for i in range(len(building_ground_coords))]
                    
                    pol = kml.newpolygon(
                                         name=building['properties']['ID'],
                                         altitudemode="relativeToGround"
                                         )
                    pol.outerboundaryis = coords
                    pol.extrude = 1
                    pol.description = gen_description_buildings(building['properties'])

                    if(show):
                        loading += 1
                        print(f"Conversion shp to kml {100 * loading // len(shp)} % \r", end="")

                except Exception as e:
                    unshowed_bat += 1
                    print(f"Error processing {building_id}: {e}")

    else:
        print("The file format is not supported.")
        return None
    
    return buildings_infos

def llh_2_XYZ(
              lon,
              lat,
              h             
              ):
    transformer = pyproj.Transformer.from_crs(4326,4964)
    coord_XYZ = transformer.transform(lat,lon,h)
    return np.array(coord_XYZ)

def XYZ_2_ENh(
              X,
              Y,
              Z
              ):
     
     transformer = pyproj.Transformer.from_crs(4964,2154)
     coord_ENh = transformer.transform(X,Y,Z)
     return np.array(coord_ENh)

def llh_2_llH(
              lon,
              lat,
              h,
              grid_path=csts.grid_path
              ):
    try:
        transformer = pyproj.Transformer.from_pipeline("cct +proj=vgridshift +grids=" + grid_path)
        coord_LLH = transformer.transform(lon,lat,h)
        return np.array(coord_LLH)
    except Exception as e:
        if " " in grid_path:
            print("Error: your folder path contains a space, and pyproj doesn't manage it ...")
        else:
            print(f"Error: There is an error with pyproj: {e}")
        return None

def XYZ_2_ENH(
              X,
              Y,
              Z,
              grid_path=csts.grid_path
              ):
     
    # Transformer for XYZ to LLh
    transformer1 = pyproj.Transformer.from_crs(4964,4326)
    coordLLh = transformer1.transform(X,Y,Z)

    # Transformer for LLh to LLH
    transformer2 = pyproj.Transformer.from_pipeline("cct +proj=vgridshift +grids=" + grid_path)
    coordLLH = transformer2.transform(coordLLh[1],coordLLh[0],coordLLh[2])

    # Transformer for LLH to ENH
    transformer3 = pyproj.Transformer.from_crs(4326,2154)
    coordENH = transformer3.transform(coordLLH[1],coordLLH[0],coordLLH[2])
    
    return coordENH[0],coordENH[1],coordENH[2],coordLLH[0],coordLLH[1]

def ENH_2_XYZ(
              pts,
              grid_path
              ):
    
    # Ensure pts is a numpy array
    pts = np.array(pts)
    
    # Initialize the result array
    result = np.zeros_like(pts)
    
    # Transformer for ENH to LLH
    transformer1 = Transformer.from_crs(2154, 4326)
    
    # Transformer for LLH to LLh
    transformer2 = Transformer.from_pipeline("cct +proj=vgridshift +grids=" + grid_path)
    
    # Transformer for LLh to XYZ
    transformer3 = Transformer.from_crs(4326, 4964)
    
    for i, pt in enumerate(pts):
        # Transform ENH to LLH
        coordLLH = transformer1.transform(pt[0], pt[1], pt[2])
        
        # Transform LLH to LLh
        coordLLh = transformer2.transform(coordLLH[1], coordLLH[0], coordLLH[2])
        
        # Calculate ondulation value
        O = coordLLH[2] - coordLLh[2]
        
        # LLh point
        llhPt = (coordLLh[0], coordLLh[1], pt[2] + O)
        
        # Transform LLh to XYZ
        coordXYZ = transformer3.transform(llhPt[1], llhPt[0], llhPt[2])
        
        # Store the result
        result[i] = coordXYZ
    
    return result

def ENh_2_llh(
              E,
              N,
              h
              ):
          
    # Convert ENh to llh
    transformer = pyproj.Transformer.from_crs(2154,4326)
    coord_llh = transformer.transform(E,N,h)
    return np.array(coord_llh) 

""" get sattelite informations """
def get_sat_infos(
                  data,
                  rinex_obs,
                  rinex_nav
                ):

    #load rinex observation file
    Obs = rx.rinex_o()
    Obs.loadRinexO(rinex_obs)

    #load rinex navigation file
    Nav = orb.orbit()
    Nav.loadRinexN(rinex_nav)

    #dictionnary to store useful informations of satellites
    sat_dict = {}

    for row in data.itertuples(index=False, name="Pandas"):
        
        #get the index of the row
        ind = data.loc[data["hour"] == getattr(row, "hour")].index[0]
        
        #dictionnary to store informations of the receiver
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
        
        #retreive the epoch of the observation
        date = getattr(row, "date").split("/")
        year,month,day = date[2],date[1],date[0],
        hour = getattr(row, "hour").split(':')
        h,m,s = hour[0],hour[1],round(float(hour[2]),0)
        date_hour = f"{year} {month} {day} {h} {m} {s}"

        gnssdate=gpst.gpsdatetime()
        gnssdate.rinex_t(date_hour)
        Ep = Obs.getEpochByMjd(gnssdate.mjd)

        if(Ep != None):
            
            #dictionnary to store informations of satellites for a specific date and hour
            sat_cepoch_dict = {} # satellites in the current epoch dictionnary

            for sat in Ep.satellites:
                if sat != None:
                    name_sat = f"{sat.const}{sat.PRN}"
                    try:
                        X,Y,Z,dte = Nav.calcSatCoord(sat.const,sat.PRN,gnssdate)
                        if not np.isnan(X):
                            sat_cepoch_dict[name_sat] = {
                                                         "X": X,
                                                         "Y": Y,
                                                         "Z": Z,
                                                         "dte": dte
                                                        }
                    except:
                        pass
            #store the informations of the receiver and satellites for a specific date and hour
            sat_dict[date_hour] = {
                                    "rcvr_infos": rcvr_dict,
                                    "sat_infos": sat_cepoch_dict
                                    }

    return sat_dict

def pt_along_line(
                  P1,
                  P2,
                  distance=1000 #1km
                 ):
    
    P1 = np.array(P1)
    P2 = np.array(P2)
    
    # Compute the direction vector and its unit vector
    direction = P2 - P1
    length = np.linalg.norm(direction)
    
    if(length == 0):
        raise ValueError("P1 and P2 cannot be the same point")
    
    unit_direction = direction / length
    
    # Compute the new point
    xn,y_n,z_n = P1 + unit_direction * distance
    
    return xn,y_n,z_n

def segment_intersects_bbox(
                            ray_origin,
                            ray_end,
                            aabb_min,
                            aabb_max
                            ):
    
    # Compute the ray direction (normalized)
    ray_direction = ray_end - ray_origin
    ray_length = np.linalg.norm(ray_direction)  # Compute segment length
    
    if(ray_length == 0):
        return False, None, None  # Avoid division by zero

    ray_direction /= ray_length  # Normalize

    # Compute t_min and t_max for each axis
    t_min = (aabb_min - ray_origin) / ray_direction
    t_max = (aabb_max - ray_origin) / ray_direction

    t1 = np.minimum(t_min, t_max)  # Entry points
    t2 = np.maximum(t_min, t_max)  # Exit points

    t_entry = np.max(t1)  # Furthest entry point
    t_exit = np.min(t2)   # Closest exit point

    # Check if there's an intersection within the segment range (0 <= t <= ray_length)
    if t_entry <= t_exit and 0 <= t_exit <= ray_length:
        return True, t_entry, t_exit  # Intersection occurs within segment
    return False, None, None  # No intersection

def compute_collisions(
                       sat_dict,
                       building_dict,
                       dist_building=300, #FIXME: to be exposed via argparse
                       show=False
                      ):
    
    # Iterate over each epoch
    for ekey in sat_dict:

        # Get the receiver coordinates XYZ
        xr = sat_dict[ekey]["rcvr_infos"]["coordX"]
        yr = sat_dict[ekey]["rcvr_infos"]["coordY"]
        zr = sat_dict[ekey]["rcvr_infos"]["coordZ"]
        
        # Get the receiver coordinates in ENH
        er = sat_dict[ekey]["rcvr_infos"]["coordE"]
        nr = sat_dict[ekey]["rcvr_infos"]["coordN"]
        Hr = sat_dict[ekey]["rcvr_infos"]["H"]

        if(show):
            print(f'Processing epoch {ekey} with {len(sat_dict[ekey]["sat_infos"])} satellites')

        # Iterate over each satellite in the epoch
        for skey in sat_dict[ekey]["sat_infos"]:
            
            # Get the satellite coordinates
            xs = sat_dict[ekey]["sat_infos"][skey]["X"]
            ys = sat_dict[ekey]["sat_infos"][skey]["Y"]
            zs = sat_dict[ekey]["sat_infos"][skey]["Z"]

            # Check if the satellite coordinates are valid
            if not np.isnan([xs, ys, zs]).any():
                
                # Compute the point along the line
                xn, yn, zn = pt_along_line((xr, yr, zr), (xs, ys, zs))

                # Convert coordinates to E,N,H
                en,nn,Hn,lon,lat = XYZ_2_ENH(xn,yn,zn,csts.grid_path)

                # Add lon lat to dictionary --> useful at drawing step
                sat_dict[ekey]["sat_infos"][skey]["lon_apparente"] = lon
                sat_dict[ekey]["sat_infos"][skey]["lat_apparente"] = lat
                sat_dict[ekey]["sat_infos"][skey]["H_apparente"] = Hn
                
                if(show):
                    print(f"Checking satellite {skey} with {len(building_dict)} buildings")

                # Check for collision with each building
                collision_detected = False
                
                # Iterate over each building
                for bkey in building_dict:

                    # Check distance to the building
                    base_coords = np.array(building_dict[bkey]["base_coords"])
                    distances = np.linalg.norm(base_coords - np.array([er, nr, Hr]), axis=1)
                    distance = np.min(distances)

                    # if the distance is less than the threshold
                    if(distance < dist_building):
                        
                        # Get the bounding box of the building
                        aabb_min = np.min(building_dict[bkey]["base_coords"], axis=0)
                        aabb_max = np.max(building_dict[bkey]["roof_coords"], axis=0)

                        if(show):
                            print(f"Checking building {bkey} with aabb_min={np.array2string(aabb_min, precision=1, suppress_small=True)}, aabb_max={np.array2string(aabb_max, precision=1, suppress_small=True)}")
                            
                        collision_status, _, _ = segment_intersects_bbox(
                                                                             np.array([er, nr, Hr]),
                                                                             np.array([en, nn, Hn]),
                                                                             aabb_min,
                                                                             aabb_max
                                                                            )
                        # Check if a collision was detected
                        if(collision_status):
                            collision_detected = True
                            if(show):
                                print(f"Collision detected with building {bkey}")
                            break
                    if(collision_detected):
                        break

                # Set the status based on collision detection
                if collision_detected:
                    sat_dict[ekey]["sat_infos"][skey]["status"] = "NLOS"
                    sat_dict[ekey]["sat_infos"][skey]["Building ID"] = bkey
                else:
                    sat_dict[ekey]["sat_infos"][skey]["status"] = "LOS"
                    sat_dict[ekey]["sat_infos"][skey]["Building ID"] = "None"
            else:
                # Initialize status
                sat_dict[ekey]["sat_infos"][skey]["status"] = "UNKNOWN"
                sat_dict[ekey]["sat_infos"][skey]["Building ID"] = "None"
    
    return sat_dict

def draw_collision_rays(
                        sat_dict,
                        kml_layer
                        ):

    line_style_dict = {}

    for key, style in csts.line_styles.items():
        s = simplekml.Style()
        s.linestyle.color = style['color']
        s.linestyle.width = 2
        line_style_dict[key] = s
    
    for key in sat_dict:

        folder = kml_layer.newfolder(
                                      name=f"Vectors for Point at Epoch {key}",
                                      visibility=0
                                      )
    
        # Create a line between the current position of the receiver and each sattelite in the list
        for skey in sat_dict[key]["sat_infos"]:

            sat_status = sat_dict[key]["sat_infos"][skey]["status"]

            desc = '<table style="border: 1px solid black;>'
            desc += f'<tr><td">{" "}</td><td">{" "}</td></tr>\n'
            desc += f'<tr><td style="text-align: left;">{"Nom :"}</td><td style="text-align: left;">{skey}</td></tr>\n'
            desc += f'<tr><td style="text-align: left;">{"Epoch :"}</td><td style="text-align: left;">{key}</td></tr>\n'
            desc += f'<tr><td style="text-align: left;">{"Status :"}</td><td style="text-align: left;">{sat_status}</td></tr>\n'
            desc += f'<tr><td style="text-align: left;">{"Building ID :"}</td><td style="text-align: left;">{sat_dict[key]["sat_infos"][skey]["Building ID"]}</td></tr>\n'
            desc += '</table>'

            # receiver position
            rcvr_lon = sat_dict[key]["rcvr_infos"]["lon"]
            rcvr_lat = sat_dict[key]["rcvr_infos"]["lat"]
            rcvr_H = sat_dict[key]["rcvr_infos"]["H"]
            
            # satellite apparent position
            sat_lon_app = sat_dict[key]["sat_infos"][skey]["lon_apparente"]
            sat_lat_app = sat_dict[key]["sat_infos"][skey]["lat_apparente"]
            sat_H_app = sat_dict[key]["sat_infos"][skey]["H_apparente"]

            end_coords = [(rcvr_lon, rcvr_lat, rcvr_H), (sat_lon_app, sat_lat_app, sat_H_app)]

            vector_placemark = folder.newlinestring(
                                                    name=f"Vector to {skey} ({sat_status})",
                                                    description=desc
                                                    )
            vector_placemark.coords = end_coords
            vector_placemark.altitudemode = simplekml.AltitudeMode.absolute
            style_key = 'LOS' if sat_status == 'LOS' else 'NLOS'
            vector_placemark.style = line_style_dict[style_key]