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
import csts,functions
# Packages:
import os,simplekml,pyproj,fiona
import numpy as np
import pandas as pd


""" Main Function, transform the input data into a KML file (with many options) """
def csv_to_kml(
		       input_file, # string
			   input_type, # string
			   separator=",", # string
			   output_file="", # string
			   doc_name="", # string
			   quiet=True, # boolean
			   mode="icon", # string
			   label_scale=2, # integer
			   icon_scale=1, # integer
			   icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png", # string
			   show_pt_name=False, # boolean
			   data_range='default', # string
			   altitude_mode="absolute", # string
			   hide_pts=False, # boolean
			   hide_lines=False, # boolean
			   hide_conf_int=False, # boolean
			   scale_factor_pla=1, # float
			   incert_pla_max=np.nan, # float
			   scale_factor_hig=1, # float
			   incert_hig_max=np.nan, # float
			   hide_buildings=True, # boolean
			   margin=250, # float
			   buildings='', # string
			   save_buildings='intersection', # string
			   hide_frustum=False, # boolean
			   fr_sensor=1, # float
			   fr_focal=10, # float
			   fr_distance=5, # float
			   fr_alpha=0, # float
			   fr_beta=0, # float
			   fr_gamma=0, # float
			   detect_nlos=False, # boolean
			   rinex_obs="",
			   rinex_nav="",
			   line_length=250,
			   show_extent=True
			   ):
	
	if(not quiet):
		print(csts.desc_tool)
		print("==> Input File : %s\n"%input_file)

	# Import the data
	if input_type == "extevent" :
		labels = csts.extevent_labels
	elif input_type == "log" :
		labels = csts.log_labels
	data = pd.read_csv(input_file, sep=separator, header=None)
	try :
		data.columns = labels
	except :
		print("The input type isn't the right one, or isn't supported. \nYou can change the input type by using the command -it.")
		return None

	# Save number of element in the original input data
	nb_elem = len(data)

	# Check if data_range is in the right format
	if data_range == 'default' :
		if input_type == 'extevent' :
			data_range = csts.default_data_range_extevent
		elif input_type == 'log' :
			data_range = csts.default_data_range_log
	try :
		data_range = np.array(data_range[1:-1].split(",")).astype(int)
	except :
		print("The data_range parameter (-dr) isn't in the right format :\n Range of data from start (s), to end (e), with a step (t) : (s,e,t). e and t are optionnal. If -it 'extevent' Default=(0,-1,1), -it 'log' Default=(0,-1,10)")
		return 
	
	# Clear empty coordinates
	lon_lat = data[['lon','lat']].values
	empty = np.union1d(data[np.isnan(lon_lat[:,0])].index,data[np.isnan(lon_lat[:,1])].index)
	data = data.drop(empty)
	nb_elem_rm_empty = len(data) # number of elements removed because of empty coordinates

	# Decimation of input data with data_range: #FIXME: the way decimation is done, last element in not included in the output even when data_range=(0,-1,1)
	# Handle case of single element in data
	if len(data) == 1:
		pass
	elif len(data_range) == 3 :
		data = data[data_range[0]: data_range[1]: data_range[2]]
	elif len(data_range) == 2 :
		data = data[data_range[0]: data_range[1]: 1]
	elif len(data_range) == 1 :
		data = data[data_range[0]: -1: 1]
	
	# number of elements after decimation
	nb_elem_decim = len(data)

	# show samples numbers
	if(not quiet):
		print(csts.sep_line)
		print("(#) original samples \t = %d" % nb_elem)
		print("(#) samples after removing empty coordinates \t = %d" % nb_elem_rm_empty)
		print("(#) samples after decimation \t = %d" % nb_elem_decim)
		print(csts.sep_line)
	
	# Reorganise indexes without loosing previous
	data = data.reset_index()

	# show some statistics
	if(not quiet):
		print(csts.sep_line)
		print("(#) samples \t = %d" % len(data))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["R"]["name"],[pt["state"] for index, pt in data.iterrows()].count("R"),100*[pt["state"] for index, pt in data.iterrows()].count("R")/len(data)))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["F"]["name"],[pt["state"] for index, pt in data.iterrows()].count("F"),100*[pt["state"] for index, pt in data.iterrows()].count("F")/len(data)))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["N"]["name"],[pt["state"] for index, pt in data.iterrows()].count("N"),100*[pt["state"] for index, pt in data.iterrows()].count("N")/len(data)))
		print(csts.sep_line)

	# Instance simplekml class
	kml=simplekml.Kml()

	# Assign a document name
	if(doc_name=="") : 
		doc_name=os.path.basename(input_file)
	kml.document.name = doc_name

	# Assign an output path
	if(output_file==""): 
		output_file="".join([os.path.splitext(input_file)[0],".kml"])

	# Adding attributes
	# Coordinates transformation llh (geographic) --> XYZ (geocentric)
	# print lon,lat,h
	coord_XYZ = functions.llh_2_XYZ(data[['lon']],data[['lat']],data[['h']])
	data[['coordX','coordY','coordZ']] = coord_XYZ.T.reshape(-1, 3).round(3)

	# Adding attributes
	# coordinate transformation XYZ (geocentric) --> ENh (cartographic Lambert93)
	coord_ENh = functions.XYZ_2_ENh(data[['coordX']],data[['coordY']],data[['coordZ']])
	data[['coordE','coordN','coordh']] = coord_ENh.T.reshape(-1, 3).round(3)

	# Adding attributes
	# altitude from ellispoidal height
	coord_LLH = functions.llh_2_llH(data[['lon']],data[['lat']],data[['h']])
	data["H"] = coord_LLH[2].round(3)

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
	incert_pla_factor_E, incert_pla_factor_N = functions.calcul_incert_pla_factor(data,size)		
	
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
	if(buildings != ''):

		# Adding buildings layer
		kml_buildings_layer = kml.newfolder(name='Buildings')

		# Outside box determination
		E = np.array([np.min(data["coordE"]), np.max(data["coordE"])])
		N = np.array([np.min(data["coordN"]), np.max(data["coordN"])])
		bbox = (E[0]-margin,N[0]-margin,E[1]+margin,N[1]+margin) # (Est_min,Nord_min,Est_max,Nord_max)
		
		# Intersection between buildings and workfield
		layers = []
		shp_out_file = ''
		if buildings[-4:] == ".shp" :
			layers = [buildings.split('/')[-1][:-4]]
			buildings = "/".join(buildings.split('/')[:-1]) + '/'
		if "/" not in save_buildings :
			shp_out_file = "/".join(buildings.split('/')) + '/'
		if save_buildings[-4:] == ".shp" :
			shp_out_file = shp_out_file + save_buildings
		else :
			shp_out_file = shp_out_file + save_buildings + ".shp"

		# Opening buildings shapefile
		if layers == [] :
			layers = fiona.listlayers(buildings)
		with fiona.open(buildings, 'r', layer=layers[0]) as source :
			schema = source.schema
		# Intersection of buildings file and workfield
		with fiona.open(shp_out_file, 'w', driver='ESRI Shapefile', schema=schema) as sink:
			if not quiet:
				print("Selecting buildings on the workfield ...\r", end="")
			for layer in layers :
				with fiona.open(buildings, 'r', layer=layer) as source:
					if source.schema == schema :
						# selecting buildings inside the convex envelop
						filtered_buildings = source.filter(bbox=bbox)
						# saving thoses buildings in the output file
						sink.writerecords(filtered_buildings)
					else :
						print(f"The shapefile '{layer}' schema is different from the used schema of '{layers[0]}'. The buildings of '{layer}' aren't saved to the kml.")
		if(not quiet):
			print("Selecting buildings on the workfield done.")	
		
		# Transformation to kml & return useful informations related to buildings ; will be used for NLOS computation
		buildings_infos = functions.shp2kml(
			                                shp_out_file,
											kml_buildings_layer,
											quiet
											)

		# Delete .shp files if wanted
		if save_buildings == 'intersection' :
			if(not quiet):
				print("Deleting temporary files ...")
			for end in [".shp", ".dbf", ".cpg", ".shx"] :
				if os.path.exists(shp_out_file[:-4] + end):
					# Supprimez le fichier
					os.remove(shp_out_file[:-4] + end)

	# separation of data type in the kml (buildings layer is created upward)
	if(not hide_pts): kml_points_layer = kml.newfolder(name="Measured points")
	if(not hide_lines): kml_lines_layer = kml.newfolder(name="Trace")
	if(not hide_conf_int): kml_int_conf_layer = kml.newfolder(name="Confidences intervals")
	if(not hide_frustum and input_type == "extevent"): kml_frustum_layer = kml.newfolder(name="Frustums")
	if(detect_nlos): kml_collisions_layer = kml.newfolder(name="Collisions")

	line = []
	index_line = 0

	# extent
	if(show_extent and buildings != ''):
		# convert ENh to llh : bbox = (E[0]-margin,N[0]-margin,E[1]+margin,N[1]+margin) # (Est_min,Nord_min,Est_max,Nord_max)
		h_min = np.min(data["coordh"])
		coordMinLLh = functions.ENh_2_llh(bbox[0],bbox[1],h_min)
		coordMaxLLh = functions.ENh_2_llh(bbox[2],bbox[3],h_min)
		lat_min, lat_max = coordMinLLh[0], coordMaxLLh[0]
		lon_min, lon_max = coordMinLLh[1], coordMaxLLh[1]
		bbox_llh = [
        			(lon_min, lat_min, h_min),
        			(lon_max, lat_min, h_min),
        			(lon_max, lat_max, h_min),
        			(lon_min, lat_max, h_min),
        			(lon_min, lat_min, h_min)
    			   ]
		kml_bbox_layer = kml.newfolder(name="Extent")
		polygon_extent = kml_bbox_layer.newpolygon(name="Bounding Box")
		polygon_extent.outerboundaryis = bbox_llh
		polygon_extent.style.polystyle.color = simplekml.Color.changealpha("7f", simplekml.Color.red)
	
	# receiver-satellites buildings collision computation
	if(detect_nlos and buildings != ''):
		
		# Get sattelite informations
		sat_infos = functions.get_sat_infos(
			                      			data, # dataframe
								  			rinex_obs, # rinex observation file
								  			rinex_nav # rinex navigation file
							     			)
		
		# Compute receiver-satellite & buildings collisions
		sat_infos = functions.compute_collisions(
			                           			 sat_infos,
							 		   			 buildings_infos
								      			)

	# Iterate over the points
	for index, pt in data.iterrows():

		# Insert points in the kml
		if(not hide_pts):
			
			# Generate the description of the point:
			description_pt = functions.gen_description_pt(pt, np.max(data["index"]))
			functions.custom_pt(
				      			kml_points_layer,
					  			pt,
					  			mode=mode,
					  			name="Point n° " + str(index),
					  			desc=description_pt,
					  			label_scale=label_scale,
					  			icon_scale=icon_scale,
					  			icon_href=icon_href,
					  			show_pt_name=show_pt_name,
					  			altitude_mode=altitude_mode
					  			)
			
		# Insert the confidences intervals into the kml
		if(not hide_conf_int):
			functions.custom_int_conf(
				            		  kml_int_conf_layer,
									  pt,
							          mode="pyr",
							          name="Point n° " + str(index),
							          altitudemode=altitude_mode,
							          color=csts.colors_dict[csts.status_dict[pt["state"]]["color"]],
							          incert_pla_factor_E=incert_pla_factor_E, 
							          incert_pla_factor_N=incert_pla_factor_N,
							          scale_factor_pla=scale_factor_pla,
							          incert_pla_max=incert_pla_max,
							          scale_factor_hig=scale_factor_hig,
							          incert_hig_max=incert_hig_max
									)

		# Insert the frustums into the kml
		if(not hide_frustum and input_type == "extevent"):
				functions.custom_frustum(
					                     kml_frustum_layer,
							             pt,
							             product_rotation_matrix,
							             mode="fur",  
							             name="",	  
							             description="",  
							             altitudemode=altitude_mode,  
							             incert_pla_factor_E=incert_pla_factor_E,
							             incert_pla_factor_N= incert_pla_factor_N,
							             fr_sensor=fr_sensor,
							             fr_focal=fr_focal,
							             fr_distance=fr_distance
										 )
				
		# Insert the lines into the kml
		if(not hide_lines):
			# prepare a segmentation of the trajectory by GNSS status
			if(index+1 < len(data)):
				if len(line) == 0 :
					line = [[pt["state"]], 
							[pt["index"]], 
							[(pt["lon"], pt["lat"], pt["H"])]]
				elif line[0][0] == pt["state"] :
					line[0].append(pt["state"])
					line[1].append(pt["index"])
					line[2].append((pt["lon"],pt["lat"], pt["H"]))
				else :
					if len(line[0]) > 1 :
						# insert the lines into the kml
						description_line = functions.gen_description_line(line)
						
						functions.custom_line(
									          kml_lines_layer,
									          line[2],
									          status=line[0][0],
									          mode="line",
									          name="Segment n° " + str(index_line),
									          description=description_line,
									          width=5,
									          altitudemode=altitude_mode
									         )
						index_line+=1
					line = [[pt["state"]], 
							[pt["index"]], 
							[(pt["lon"], pt["lat"], pt["H"])]]
		
		# Print %
		if(not quiet):
			print(f"Generating kml objects {100*index//len(data)} % \r",end="")
	
	# Insert collision informations
	if(detect_nlos and buildings != ''):
		functions.draw_collision_rays(
				                          sat_infos,
						                  kml_collisions_layer
						                 )
	# Print
	if(not quiet):
		print("Generating kml objects done.")
		print("Saving kml file ...\r", end="")
	
	# save kml file
	kml.save(output_file)		

	if(not quiet):
		print(csts.sep_line)
		print("\n==> Job done")
		print("==> KML output saved as", output_file)
		if save_buildings != "intersection" :
			print("==> SHP output saved as", shp_out_file)
		print(csts.sep_line)
	return None

