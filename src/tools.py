# -*- coding: utf-8 -*-
"""
@author: mehdi daakir, gabin bourlon, axel debock, felix mercier, clement cambours
"""
# Imports :
# Python files :
import csts
# Common packages :
import os
import numpy as np
import pandas as pd
# Geodata packages :
from pyproj import Transformer 							# Coordinates transformations
from shapely.geometry import Polygon, shape, mapping 	# Shapefile management
from shapely import intersects 							# Shapefile management
import fiona											# Shapefile management
import gpsdatetime as gpst								# GNSS date management
import gnsstoolbox.orbits as orb						# Orbit rinex management
import gnsstoolbox.rinex_o as rx						# Navigation rinex management
import simplekml										# KML management

# To use this programm, see the README.md file, but there is some example line below
# python3 src/csv_to_kml.py test/EXTENVENT.LOG

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
		corners = np.array([(pt["lon"]-incert_lat, pt["lat"]		   , pt["altitude"]), 
			 	   			(pt["lon"]	   	     , pt["lat"]+incert_lon, pt["altitude"]), 
				   			(pt["lon"]+incert_lat, pt["lat"]		   , pt["altitude"]), 
				   			(pt["lon"]		     , pt["lat"]-incert_lon, pt["altitude"]), 
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
					fr_captor=1,	# size of the captor
					fr_focal=10,	# size of the focal
					fr_distance=5,	# distance between the two faces of the frustum
					):
	if (mode == "fur") :
		far = (fr_captor/fr_focal*fr_distance)
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
		frustum = [[ fr_captor, 0        , fr_focal],
				   [ 0        , fr_captor, fr_focal],
				   [-fr_captor, 0        , fr_focal],
				   [ 0        ,-fr_captor, fr_focal],
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

""" Main Function, transform the input data into a kml file, with many options """
def csv_to_kml(input_file, # string
			   input_type, # string
			   separator=",", # string
			   output_file="", # string
			   doc_name="", # string
			   quiet=False, # boolean
			   mode="icon", # string
			   label_scale=2, # integer
			   icon_scale=1, # integer
			   icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png", # string
			   show_pt_name=False, # boolean
			   data_range='()', # string
			   altitudemode="absolute", # string
			   show_point=True, # boolean
			   show_line=True, # boolean
			   show_conf_int=True, # boolean
			   scale_factor_pla=1, # float
			   incert_pla_max=np.nan, # float
			   scale_factor_hig=1, # float
			   incert_hig_max=np.nan, # float
			   show_buildings=True, # boolean
			   margin=0.001, # float
			   departments='', # string
			   save_buildings='intersection', # string
			   calc_ephemerids=True, # boolean
			   rinex_name='', # string
			   show_orientation=True, # boolean
			   fr_captor=1, # float
			   fr_focal=10, # float
			   fr_distance=5, # float
			   fr_alpha=0, # float
			   fr_beta=0, # float
			   fr_gamma=0 # float
			   ):
	if not quiet :
		print("\n################ csv to kml ################\n")
		print("==> Input File : %s\n"%input_file)

	# import the data
	if input_type == "extevent" :
		labels = ["time", "day", "state", "lat", "lon", "h", "incert_pla", "incert_hig", "oX", "oY", "oZ"]
	elif input_type == "log" :
		labels = ["uk1", "GNSS", "uk2", "time", "date", "hour", "state", "lat", "lon", "h", "incert_pla", "incert_hig"]	
	data = pd.read_csv(input_file, sep=separator)
	try :
		data.columns = labels
	except :
		print("The input type isn't the right one, or isn't supported. \nYou can change the input type by using the command -it.")
		return None

	# clear empty coordinates
	data_range = np.array(data_range[1:-1].split(",")).astype(int)
	lonlat = data[['lon', 'lat']].values
	empty = np.union1d(data[np.isnan(lonlat[:,0])].index, data[np.isnan(lonlat[:,1])].index)
	data = data.drop(empty)

	# decimation of data with data_range
	if len(data_range) == 3 :
		data = data[data_range[0]: data_range[1]: data_range[2]]
	elif len(data_range) == 2 :
		data = data[data_range[0]: data_range[1]: 1]
	elif len(data_range) == 1 :
		data = data[data_range[0]: -1: 1]

	# reorganise indexes without loosing previous
	data = data.reset_index()

	# show some statistics
	if(not quiet):
		print("(#) samples \t = %d" % len(data))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["R"]["name"],[pt["state"] for index, pt in data.iterrows()].count("R"),100*[pt["state"] for index, pt in data.iterrows()].count("R")/len(data)))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["F"]["name"],[pt["state"] for index, pt in data.iterrows()].count("F"),100*[pt["state"] for index, pt in data.iterrows()].count("F")/len(data)))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["N"]["name"],[pt["state"] for index, pt in data.iterrows()].count("N"),100*[pt["state"] for index, pt in data.iterrows()].count("N")/len(data)))
		print()

	# instance simplekml class
	kml=simplekml.Kml()

	# assign a name
	if(doc_name=="") : 
		doc_name=os.path.basename(input_file)
	kml.document.name = doc_name

	# assign an output path
	if(output_file==""): 
		output_file="".join([os.path.splitext(input_file)[0],".kml"])

	### Adding attributes
	# coordinates transformation to cartesian geocentric 
	transformer = Transformer.from_crs(4326, 4964)
	coordRGF93 = transformer.transform(data['lon'], data['lat'], data['h'])
	coordRGF93 = np.array(coordRGF93)
	
	data[['coordX', 'coordY', 'coordZ']] = coordRGF93.T.round(3)

	# altitude from ellispoidal height
	location_file = os.path.abspath(__file__)
	grid_path = "/".join(location_file.split('/')[:-2]) + "/params/fr_ign_RAF20.tif"

	try  :
		transformer = Transformer.from_pipeline("cct +proj=vgridshift +grids=" + grid_path)
	except :
		if " " in grid_path :
			print("Error : your folder path contain a space, and pyproj doesn't manage it ...")
		else :
			print("Error : There is an error with pyproj.")
	coordalt = transformer.transform(data['lon'], data['lat'], data['h'])
	coordalt = np.array(coordalt)

	data["altitude"] = coordalt[2].round(3)

	# calculate distance between two points
	data["dist"] = np.sqrt(data["coordX"].diff()**2 + data["coordY"].diff()**2 + data["coordZ"].diff()**2).round(3)
	data.loc[data.index[0],"dist"] = 0.

	# calculate time between two points
	data["time_laps"] = data["time"].diff().round(3)
	data.loc[data.index[0],"time_laps"] = 0.

	# calculate time since start, and until end
	data["time_elapsed"] = data["time_laps"].cumsum().round(3)
	data["time_left"] = data["time_elapsed"].values[-1] - data["time_elapsed"]
	data["time_left"] = data["time_left"].round(3)

	# calculate instantaneous velocity
	data["velocity"] = data["dist"]/data["time_laps"]
	data["velocity"] = (data["velocity"].shift(-1) + data["velocity"])/2
	data["velocity"] = data["velocity"].round(3)	

	# calcul of a factor for incertainty
	size = 1000
	incert_pla_factor_E, incert_pla_factor_N = calcul_incert_pla_factor(data, size)		
	
	# rotation matrix2 allow to change the reference frame of the camera to the geographical reference frame
	rotation_matrixX2 = np.array([[ 1, 0               , 0               ],
								  [ 0, np.cos(fr_alpha),-np.sin(fr_alpha)],
								  [ 0, np.sin(fr_alpha), np.cos(fr_alpha)]])
	rotation_matrixY2 = np.array([[ np.cos(fr_beta), 0, np.sin(fr_beta)],
								  [ 0              , 1, 0              ],
								  [-np.sin(fr_beta), 0, np.cos(fr_beta)]])
	rotation_matrixZ2 = np.array([[ np.cos(fr_gamma),-np.sin(fr_gamma), 0],
								  [ np.sin(fr_gamma), np.cos(fr_gamma), 0],
								  [ 0               , 0               , 1]])
	product_rotation_matrix = rotation_matrixX2 @ rotation_matrixY2 @ rotation_matrixZ2

	# Adding buildings to the kml 
	if show_buildings and departments != '' :		
		# adding buildings folder
		kml_buildings = kml.newfolder(name='Buildings')

		# outside box determination
		transformer = Transformer.from_crs(4326, 2154)  
		E = np.array([np.min(data["lon"]) - margin, np.max(data["lon"]) + margin])
		N = np.array([np.min(data["lat"]) - margin, np.max(data["lat"]) + margin])
		coordLambert = transformer.transform(N,E)

		bbox = (coordLambert[0][0], coordLambert[1][0], coordLambert[0][1], coordLambert[1][1])

		# intersection between buildings and workfield
		layers = []
		res_file = ''
		if departments[-4:] == ".shp" :
			layers = [departments.split('/')[-1][:-4]]
			departments = "/".join(departments.split('/')[:-1]) + '/'
		if "/" not in save_buildings :
			res_file = "/".join(departments.split('/')) + '/'
		if save_buildings[-4:] == ".shp" :
			res_file = res_file + save_buildings
		else :
			res_file = res_file + save_buildings + ".shp"

		# opening buildings shapefile
		if layers == [] :
			layers = fiona.listlayers(departments)
		with fiona.open(departments, 'r', layer=layers[0]) as source :
			schema = source.schema
		# intersection of bildings file and workfield
		with fiona.open(res_file, 'w', driver='ESRI Shapefile', schema=schema) as sink:
			if not quiet:
				print("Selecting buildings on the workfield ...\r", end="")
			for layer in layers :
				with fiona.open(departments, 'r', layer=layer) as source:
					if source.schema == schema :
						# selecting buildings inside the convex envelop
						filtered_buildings = source.filter(bbox=bbox)
						# saving thoses buildings in the output file
						sink.writerecords(filtered_buildings)
					else :
						print(f"The shapefile '{layer}' schema is different from the used schema of '{layers[0]}'. The buildings of '{layer}' aren't saved to the kml.")
		if not quiet:
			print("Selecting buildings on the workfield done.")	
		
		#transformation to kml
		shp2kml(res_file, kml_buildings, quiet)

		# delete shp files if wanted
		if save_buildings == 'intersection' :
			if not quiet:
				print("Deleting temporary files ...")
			for end in [".shp", ".dbf", ".cpg", ".shx"] :
				if os.path.exists(res_file[:-4] + end):
					# Supprimez le fichier
					os.remove(res_file[:-4] + end)

	# Search all viewed satellites
	if calc_ephemerids and rinex_name != '' :
		#loading rinex files
		Obs = rx.rinex_o()
		Obs.loadRinexO(rinex_name + 'o')
		Nav = orb.orbit()
		Nav.loadRinexN(rinex_name + 'p')  

		#finding all the observed sats during the observation
		tot_observed_sats = []
		for epoch in Obs.headers[0].epochs :
			for sat in epoch.satellites :
				if sat.const + str(sat.PRN) not in tot_observed_sats :
					tot_observed_sats.append(sat.const + str(sat.PRN))
		tot_observed_sats.sort()
		dic_tot_observed_sats = {}
		i = 1
		for sat in tot_observed_sats :
			dic_tot_observed_sats[sat] = i
			i+=1
		
		#preparing the observation matrix of satellites for each point
		mat_sat_obs = np.zeros((len(data),len(tot_observed_sats),4))*np.nan

	# separation of data type in the kml (buildings folder is created upward)
	if show_point :
		kml_points = kml.newfolder(name="Measured points")
	if show_line :
		kml_lines = kml.newfolder(name="Trace")
	if show_conf_int :
		kml_int_conf = kml.newfolder(name="Confidences intervals")
	if show_orientation:
		kml_frustum = kml.newfolder(name="Frustums")

	line = []
	index_line = 0

	# Iterate over the points
	for index, pt in data.iterrows():
		# Searching all the viewed satellites from each point
		if calc_ephemerids and rinex_name != '' and input_type == "log":
			date = pt["date"].split("/")
			year = date[2]
			month = date[1]
			day = date[0]
			hour = pt['hour'].split(':')
			h = hour[0]
			m = hour[1]
			s = round(float(hour[2]),0)
			date_hour = f"{year} {month} {day} {h} {m} {s}"
			
			gnssdate=gpst.gpsdatetime()
			gnssdate.rinex_t(date_hour) 
			Ep = Obs.getEpochByMjd(gnssdate.mjd)
			if Ep != None :
				visible_sats = []
				uncalculable_sat = []
				for sat in Ep.satellites :
					name_sat = f"{sat.const}{sat.PRN}"
					try :
						X,Y,Z,dte = Nav.calcSatCoord(sat.const, sat.PRN, gnssdate)
						mat_sat_obs[index, dic_tot_observed_sats[name_sat]] = X,Y,Z,dte
					except :
						uncalculable_sat.append(name_sat)
					visible_sats.append(name_sat)
				pt["n_visible_sat"] = len(visible_sats)
				pt["visible_sat"] = visible_sats
			else :
				pt["n_visible_sat"] = "Rinex file seems to be empty for this date."
				pt["visible_sat"] = "Rinex file seems to be empty for this date."

		# Insert points in the kml
		if show_point :
			description_pt = gen_description_pt(pt, np.max(data["index"]))
			custom_pt(kml_points,
					  pt,
					  mode=mode,
					  name="Point n° " + str(index),
					  description=description_pt,
					  label_scale=label_scale,
					  icon_scale=icon_scale,
					  icon_href=icon_href,
					  show_pt_name=show_pt_name,
					  altitudemode=altitudemode)
			
		# Insert the confidences intervals into the kml
		if show_conf_int :
			custom_int_conf(kml_int_conf,
							pt,
							mode="pyr",
							name="Point n° " + str(index),
							altitudemode=altitudemode,
							color=csts.colors_dict[csts.status_dict[pt["state"]]["color"]],
							incert_pla_factor_E=incert_pla_factor_E, 
							incert_pla_factor_N=incert_pla_factor_N,
							scale_factor_pla=scale_factor_pla,
							incert_pla_max=incert_pla_max,
							scale_factor_hig=scale_factor_hig,
							incert_hig_max=incert_hig_max)
		
		# Insert the frustums into the kml
		if show_orientation:
			if input_type == "extevent":
				custom_frustum(kml_frustum,  
							   pt,
							   product_rotation_matrix,
							   mode="fur",  
							   name="",	  
							   description="",  
							   altitudemode="absolute",  
							   incert_pla_factor_E=incert_pla_factor_E,
							   incert_pla_factor_N= incert_pla_factor_N,
							   fr_captor=fr_captor,
							   fr_focal=fr_focal,
							   fr_distance=fr_distance)
				
		# Insert the lines into the kml
		if show_line:
			# prepare a segmentation of the trajectory by GNSS status
			if index+1 < len(data) :
				if len(line) == 0 :
					line = [[pt["state"]], 
							[pt["index"]], 
							[(pt["lon"], pt["lat"], pt["altitude"])]]
				elif line[0][0] == pt["state"] :
					line[0].append(pt["state"])
					line[1].append(pt["index"])
					line[2].append((pt["lon"],pt["lat"], pt["altitude"]))
				else :
					if len(line[0]) > 1 :
						# insert the lines into the kml
						description_line = gen_description_line(line)
						custom_line(
									kml_lines,
									line[2],
									status=line[0][0],
									mode="line",
									name="Segment n° " + str(index_line),
									description=description_line,
									width=5,
									altitudemode=altitudemode
									)
						index_line+=1
					line = [[pt["state"]], 
							[pt["index"]], 
							[(pt["lon"], pt["lat"], pt["altitude"])]]
		if not quiet :
			print(f"Generating kml objects {100*index//len(data)} % \r",end="")
	if not quiet :
		print("Generating kml objects done.")
		print("Saving kml file ...\r", end="")
	
	# save kml file
	kml.save(output_file)		

	if not quiet:
		print("                      ")
		print("\n==> Job done")
		print("==> Saved as", output_file)
		print("\n############################################\n")
	return None

""" Generate a description text for a point """
def gen_description_pt(pt, maxindex) :
	# generate a description for a point based on the dataframes columns
	index = pt.index
	text = '<table style="border: 1px solid black;>'
	text += f'<tr><td">{" "}</td><td">{" "}</td></tr>\n'
	for i in index :
		if i == "state" :
			value = f"{csts.status_dict[pt[i]]['name']}"
		elif csts.param_dict[i]["unity"] != 's' :
			if i == "index" :
				value = f"{pt[i]}/{maxindex}"
			else :
				value = f"{pt[i]} {csts.param_dict[i]['unity']}"
		else :
			value = f"{int(pt[i]//3600)}h {int((pt[i]%3600)//60)}min {round((pt[i]%3600)%60,3)}s"
		text += f'<tr><td style="text-align: left;">{csts.param_dict[i]["name"]}</td><td style="text-align: left;">{value}</td></tr>\n'
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
	transformer1 = Transformer.from_crs(4326, 2154)
	transformer2 = Transformer.from_crs(2154, 4326)
	
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
	# for each building in the shp, the coords are used to create a kml polygon
	if shp_file.endswith('.shp'):
		with fiona.open(shp_file, 'r') as shp:
			loading = 0
			unshowed_bat = 0
			for batiment in shp : 
				hbat = batiment['properties']['HAUTEUR']
				coords_gr = np.array(batiment['geometry']['coordinates'][0])
				try :
					coords_gr = coords_gr.reshape((len(coords_gr), 3))[:,:2]
					transformer = Transformer.from_crs(2154, 4326)
					coordsWGS = transformer.transform(coords_gr[:,:1], coords_gr[:,1:2])
					coords = []
					for i in range(len(coords_gr)):
						coords.append((coordsWGS[1][i][0], coordsWGS[0][i][0], hbat))
					pol = kml.newpolygon(name='Batiment', altitudemode = "relativeToGround")
					pol.outerboundaryis = coords
					pol.extrude = 1
					pol.description = gen_description_buildings(batiment['properties'])
					if not quiet :
						loading+=1
						print(f"Conversion shp to kml {100*loading//len(shp)} % \r",end="")
				except :
					unshowed_bat += 1
	else : 
		print("the format of the file does not match")
		return None
	return None
