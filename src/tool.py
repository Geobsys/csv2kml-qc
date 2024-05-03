# -*- coding: utf-8 -*-
"""
@author: mehdi daakir, gabin bourlon, axel debock, felix mercier, clement cambours
"""
# Imports :
# Python files :
import csts
from functions import *
# Common packages :
import os
import pandas as pd
import gpsdatetime as gpst								# GNSS date management
import gnsstoolbox.orbits as orb						# Orbit rinex management
import gnsstoolbox.rinex_o as rx						# Navigation rinex management
									

# To use this programm, see the README.md file, but there is some example line below
# python3 src/csv_to_kml.py test/EXTENVENT.LOG

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
			   margin=20, # float
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

	# Adding attributes
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
		E = np.array([np.min(data["lon"]), np.max(data["lon"])])
		N = np.array([np.min(data["lat"]), np.max(data["lat"])])
		coordLambert = transformer.transform(N,E)

		bbox = (coordLambert[0][0]-margin, coordLambert[1][0]-margin, coordLambert[0][1]+margin, coordLambert[1][1]+margin) #xmin,ymin,xmax,ymax

		# intersection between buildings and workfield
		layers = []
		shp_out_file = ''
		if departments[-4:] == ".shp" :
			layers = [departments.split('/')[-1][:-4]]
			departments = "/".join(departments.split('/')[:-1]) + '/'
		if "/" not in save_buildings :
			shp_out_file = "/".join(departments.split('/')) + '/'
		if save_buildings[-4:] == ".shp" :
			shp_out_file = shp_out_file + save_buildings
		else :
			shp_out_file = shp_out_file + save_buildings + ".shp"

		# opening buildings shapefile
		if layers == [] :
			layers = fiona.listlayers(departments)
		with fiona.open(departments, 'r', layer=layers[0]) as source :
			schema = source.schema
		# intersection of bildings file and workfield
		with fiona.open(shp_out_file, 'w', driver='ESRI Shapefile', schema=schema) as sink:
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
		shp2kml(shp_out_file, kml_buildings, quiet)

		# delete shp files if wanted
		if save_buildings == 'intersection' :
			if not quiet:
				print("Deleting temporary files ...")
			for end in [".shp", ".dbf", ".cpg", ".shx"] :
				if os.path.exists(shp_out_file[:-4] + end):
					# Supprimez le fichier
					os.remove(shp_out_file[:-4] + end)

	# Search all viewed satellites
	if calc_ephemerids and rinex_name != '' :
		#loading rinex files
		if rinex_name[-1] in ['o', 'p'] :
			rinex_name = rinex_name[:-1]
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
		print("==> KML output saved as", output_file)
		if save_buildings != "intersection" :
			print("==> SHP output saved as", shp_out_file)
		print("\n############################################\n")
	return None

