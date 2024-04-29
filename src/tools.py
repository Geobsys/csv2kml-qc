# -*- coding: utf-8 -*-
"""
@author: mehdi daakir, gabin bourlon, axel debock, felix mercier, clement cambours
"""

import csts,os,simplekml
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Polygon, shape, mapping
from shapely import intersects
import fiona
import os
from re import findall
import gpsdatetime as gpst
""" Ephemerides management """
import gnsstoolbox.orbits as orb

""" GNSS data (rinex "o" files) """ 
import gnsstoolbox.rinex_o as rx
# exemple line :
# python3 src/csv_to_kml.py test/EXTENVENT.LOG
# python3 src/csv_to_kml.py test/20240223.LOG -it 'log' -dr '(0,-1,100)' -departments "/Users/gabinbourlon/Desktop/PDI - git/D094" -mp 2 -mh 2 -rn "test/rinex/sept054n.24"


def custom_pt( # Creation of a kml point
			  kml, # simplekml object
			  lon, # longitude (WGS84), float
			  lat, # latitude  (WGS84), float
			  h,   # altitude, float
			  status="None", # GNSS measure status (R, F, N or None), string
			  mode="icon", # point representation, string
			  name="", # point name, string
			  description="", # point description, string
			  label_scale=2, # point name scale, int
			  icon_scale=1, # point icon scale, int
			  icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png", # point icon reference, string
			  show_pt_name=False, # show the point name, bool
			  altitudemode="absolute" # altitude mode in kml, string ("absolute", "relativeToGround", "clampToGround")
			 ):
	if(mode=="icon"):
		#append a pt
		pnt = kml.newpoint(altitudemode = altitudemode)

		#edit the point
		if show_pt_name : 
			pnt.name = name
			pnt.style.labelstyle.color = csts.colors_dict[csts.status_dict[status]["color"]]
			pnt.style.labelstyle.scale = label_scale
		pnt.description = description
		pnt.coords = [(lon,lat,h)]
		pnt.style.iconstyle.color = csts.colors_dict[csts.status_dict[status]["color"]]
		pnt.style.iconstyle.scale = icon_scale
		pnt.style.iconstyle.icon.href = icon_href
	return None

def custom_line( # Creation of a kml line
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

def custom_int_conf( # Creation of a kml line
				kml, # simplekml object
				pt,  # point object, pandas DataFrame
				mode="pyr", # confidence interval representation, string
				name="", # confidence interval name, string
				description="", # confidence interval description, string
				altitudemode="absolute", # altitude mode in kml, string ("absolute", "relativeToGround", "clampToGround")
				color=csts.colors_dict["green"], # confidence interval color, string
				incert_pla_factor_E=1e5, # scale factor meters to degres Est
				incert_pla_factor_N=1e5, # scale factor meters to degres North
				scale_factor_pla=1, # scale factor planimetric show
				incert_pla_max=np.nan, # maximum planimetric uncertainty showed
				scale_factor_hig=1, # scale factor altimetric show
				incert_hig_max=np.nan # maximum altimetric uncertainty showed
				):
	if (mode=="pyr"):
		# Adjusting showing options
		if pt["incert_pla"] > incert_pla_max :
			pt["incert_pla"] = incert_pla_max
		pt["incert_pla"] *= scale_factor_pla
		if pt["incert_hig"] > incert_hig_max :
			pt["incert_hig"] = incert_hig_max
		pt["incert_hig"] *= scale_factor_hig
		# switching from meters to equivalent degres
		incert_E = pt["incert_pla"]*incert_pla_factor_E
		incert_N = pt["incert_pla"]*incert_pla_factor_N
		# creating the pyramid (confidence interval) corners
		corners = np.array([(pt["lon"]-incert_E, pt["lat"]		   , pt["altitude"]), 
			 	   			(pt["lon"]	   	   , pt["lat"]+incert_N, pt["altitude"]), 
				   			(pt["lon"]+incert_E, pt["lat"]		   , pt["altitude"]), 
				   			(pt["lon"]		   , pt["lat"]-incert_N, pt["altitude"]), 
				   			(pt["lon"]		   , pt["lat"]		   , pt["altitude"] + pt["incert_hig"] )])
		#append the four faces of the pyramid
		pol = kml.newpolygon(name=name, description=description, altitudemode=altitudemode, extrude = 0)
		pol.outerboundaryis = [corners[0], corners[1], corners[-1], corners[0]]
		pol.style.polystyle.color = color
		pol = kml.newpolygon(name=name, description=description, altitudemode=altitudemode, extrude = 0)
		pol.outerboundaryis = [corners[1], corners[2], corners[-1], corners[1]]
		pol.style.polystyle.color = color
		pol = kml.newpolygon(name=name, description=description, altitudemode=altitudemode, extrude = 0)
		pol.outerboundaryis = [corners[2], corners[3], corners[-1], corners[2]]
		pol.style.polystyle.color = color
		pol = kml.newpolygon(name=name, description=description, altitudemode=altitudemode, extrude = 0)
		pol.outerboundaryis = [corners[3], corners[0], corners[-1], corners[3]]
		pol.style.polystyle.color = color
	return None

def calcul_incert_pla_factor(data, size):
	# calculate the factor to convert planimetric meters into geographical degres
	transformer1 = Transformer.from_crs(4326, 2154)
	transformer2 = Transformer.from_crs(2154, 4326)
	
	point93 = transformer1.transform(np.mean(data['lat']), np.mean(data['lon']), np.mean(data['h']))
	E = point93[0] 
	N = point93[1] 
	h = point93[2]
	point1 = transformer2.transform(E       , N	   , h)
	point2 = transformer2.transform(E + size, N + size, h)
	sigmaLon = point2[1] - point1[1]
	sigmaLat = point2[0] - point1[0]

	incert_pla_factor_E = sigmaLon / size
	incert_pla_factor_N = sigmaLat / size
	return incert_pla_factor_E, incert_pla_factor_N

def csv_to_kml(
			   input_file,
			   input_type,
			   separator=",",
			   output_file="",
			   doc_name="",
			   quiet=False,
			   mode="icon",
			   label_scale=2,
			   icon_scale=1,
			   icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png",
			   show_pt_name=False,
			   data_range=(),
			   altitudemode="absolute",
			   show_point=True,
			   show_line=True, 
			   show_conf_int=True,
			   scale_factor_pla=1,
               incert_pla_max=np.nan,
               scale_factor_hig=1,
               incert_hig_max=np.nan,
			   show_buildings=True,
			   margin=0.001,
			   departments='',
			   save_buildings=False,
			   calc_ephemerids=True,
			   rinex_name=''
			  ):
	if not quiet :
		print("\n################ csv to kml ################\n")
		print("==> Input File : %s\n"%input_file)

	#my data
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

	#clear empty coordinates
	data_range = np.array(data_range[1:-1].split(",")).astype(int)
	lonlat = data[['lon', 'lat']].values
	empty = np.union1d(data[np.isnan(lonlat[:,0])].index, data[np.isnan(lonlat[:,1])].index)
	data = data.drop(empty)

	#decimation of data with data_range
	if len(data_range) == 3 :
		data = data[data_range[0]: data_range[1]: data_range[2]]
	elif len(data_range) == 2 :
		data = data[data_range[0]: data_range[1]: 1]
	elif len(data_range) == 1 :
		data = data[data_range[0]: -1: 1]

	#reorganise indexes without loosing previous
	data = data.reset_index()


	#show some statistics
	if(not quiet):
		print("(#) samples \t = %d" % len(data))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["R"]["name"],[pt["state"] for index, pt in data.iterrows()].count("R"),100*[pt["state"] for index, pt in data.iterrows()].count("R")/len(data)))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["F"]["name"],[pt["state"] for index, pt in data.iterrows()].count("F"),100*[pt["state"] for index, pt in data.iterrows()].count("F")/len(data)))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["N"]["name"],[pt["state"] for index, pt in data.iterrows()].count("N"),100*[pt["state"] for index, pt in data.iterrows()].count("N")/len(data)))
		print()
	#instance class
	kml=simplekml.Kml()

	#assign a name
	if(doc_name==""): doc_name=os.path.basename(input_file)
	kml.document.name = doc_name

	#assign a name
	if(output_file==""): output_file="".join([os.path.splitext(input_file)[0],".kml"])

	### Adding attributes
	# Coordinates transformation to cartesian geocentric 
	transformer = Transformer.from_crs(4326, 4964)
	coordRGF93 = transformer.transform(data['lon'], data['lat'], data['h'])
	coordRGF93 = np.array(coordRGF93)
	
	data[['coordX', 'coordY', 'coordZ']] = coordRGF93.T.round(3)

	# Altitude from ellispoidal height
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

	# Calculate distance between two points
	data["dist"] = np.sqrt(data["coordX"].diff()**2 + data["coordY"].diff()**2 + data["coordZ"].diff()**2).round(3)
	data.loc[data.index[0],"dist"] = 0.

	# Calculate time between two points
	data["time_laps"] = data["time"].diff().round(3)
	data.loc[data.index[0],"time_laps"] = 0.

	# Calculate time since start, and until end
	data["time_elapsed"] = data["time_laps"].cumsum().round(3)
	data["time_left"] = data["time_elapsed"].values[-1] - data["time_elapsed"]
	data["time_left"] = data["time_left"].round(3)

	# Calculate instantaneous velocity
	data["velocity"] = data["dist"]/data["time_laps"]
	data["velocity"] = (data["velocity"].shift(-1) + data["velocity"])/2
	data["velocity"] = data["velocity"].round(3)	

	# Calcul of a factor for incertainty
	size = 1000
	incert_pla_factor_E, incert_pla_factor_N = calcul_incert_pla_factor(data, size)		
	
	if show_buildings and departments != '' :
		#adding buildings
		kml_buildings = kml.newfolder(name='Buildings')
		#Outside box determination
		transformer = Transformer.from_crs(4326, 2154)  
		Nmax = np.max(data["lat"]) + margin
		Nmin = np.min(data["lat"]) - margin
		Emax = np.max(data["lon"]) + margin
		Emin = np.min(data["lon"]) - margin
		E = np.array([[Emin, Emax]])
		N = np.array([[Nmin, Nmax]])
		
		coordLambert = transformer.transform(N,E)

		Emin = coordLambert[0][0][0]
		Emax = coordLambert[0][0][1]
		Nmin = coordLambert[1][0][0]
		Nmax = coordLambert[1][0][1]

		frame = [(Emin, Nmin), (Emin, Nmax), (Emax, Nmax), (Emax, Nmin), (Emin, Nmin)]
		polygon = Polygon(frame)

		#intersection between buildings and workfield
		res_fold = departments.split('/')
		res_file = ''
		for e in res_fold :
			res_file += e +"/"
		res_name = "intersection"
		res_file = res_file + res_name + ".shp"

		with fiona.open(departments, 'r') as couche:
			with fiona.open(res_file, 'w', 'ESRI Shapefile', couche.schema) as output:
				i = 0
				for batiment in couche:
					if batiment['geometry']['type'] == 'Polygon':
						coords = batiment['geometry']['coordinates']						
						bat_polygon = Polygon(coords[0])
						if intersects(bat_polygon, polygon):
							output.write(batiment)
					if not quiet :
						i+=1
						print(f"Intersection {100*i//len(couche)} % \r",end="")
		if not quiet :
			print("Intersection done.")
		

		#transformation to kml
		shp2kml(res_file, kml_buildings, quiet)

		# delete shp files if wanted
		if not save_buildings :
			for end in [".shp", ".dbf", ".cpg", ".shx"] :
				if os.path.exists(res_file[:-4] + end):
					# Supprimez le fichier
					os.remove(res_file[:-4] + end)

	# Define index_color for the confidence intervals
	index_color = np.zeros(len(data)).astype(int) + 3

	if not np.isnan(incert_pla_max) :
		index_color[data["incert_pla"] <   incert_pla_max  ] = 2
		index_color[data["incert_pla"] < 2*incert_pla_max/3] = 1
		index_color[data["incert_pla"] <   incert_pla_max/3] = 0
	else :
		index_color[data["incert_pla"] <   np.max(data["incert_pla"])  ] = 2
		index_color[data["incert_pla"] < 2*np.max(data["incert_pla"])/3] = 1
		index_color[data["incert_pla"] <   np.max(data["incert_pla"])/3] = 0

	# ephemerids
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


	# Separation of data type in the kml
	if show_point :
		kml_points = kml.newfolder(name="Measured points")
	if show_line :
		kml_lines = kml.newfolder(name="Trace")
	if show_conf_int :
		kml_int_conf = kml.newfolder(name="Confidence interval")		

	line = []
	index_line = 0
	#iterate over the pts
	for index, pt in data.iterrows():
		#ephemerids
		if calc_ephemerids and rinex_name != '' and input_type == "log":
			#finding the observed satellites on each point
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

		if show_point :
			# insert points into the kml
			description_pt = gen_description_pt(pt, np.max(data["index"]))
			custom_pt(
					kml_points,
					float(pt["lon"]),
					float(pt["lat"]),
					float(pt["altitude"]),
					status=pt["state"],
					mode=mode,
					name="Point n° " + str(index),
					description=description_pt,
					label_scale=label_scale,
					icon_scale=icon_scale,
					icon_href=icon_href,
					show_pt_name=show_pt_name,
					altitudemode=altitudemode
					)
		if show_conf_int :
			#insert the confidences intervals into the kml
			#color choose
			color = csts.colors_list[index_color[index]]
			custom_int_conf(
						kml_int_conf,
						pt,
						mode="pyr",
						name="Point n° " + str(index),
						description="",
						altitudemode=altitudemode,
						color=color,
						incert_pla_factor_E=incert_pla_factor_E, 
						incert_pla_factor_N=incert_pla_factor_N,
						scale_factor_pla=scale_factor_pla,
						incert_pla_max=incert_pla_max,
						scale_factor_hig=scale_factor_hig,
						incert_hig_max=incert_hig_max
						)
		
		if show_line :
			#prepare a segmentation of the trajectory by GNSS status
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
						#insert the lines into the kml
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
	#save kml
	kml.save(output_file)

	if not quiet:
		print("\n==> Job done")
		print("==> Saved as", output_file)
		print("\n############################################\n")

	return None

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

def gen_description_line(line) :
	# generate a description for a line based on the line points
	text = '<table style="border: 1px solid black;>'
	text += f'<tr><td">{" "}</td><td">{" "}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">{"Start"}</td><td style="text-align: left;">{line[1][0]}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">{"End"}</td><td style="text-align: left;">{line[1][-1]}</td></tr>\n'
	text += f'<tr><td style="text-align: left;">{"Status"}</td><td style="text-align: left;">{csts.status_dict[line[0][0]]["name"]}</td></tr>\n'
	text += '</table>'
	return text

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


def shp2kml(shp_file, kml, quiet=False):
	# for each building in the shp, the coords are used to create a kml polygon
	if shp_file.endswith('.shp'):
		with fiona.open(shp_file, 'r') as shp:
			loading = 0
			for batiment in shp : 
				hbat = batiment['properties']['HAUTEUR']
				coords_gr = batiment['geometry']['coordinates'][0]
				coords_gr = np.array(coords_gr).reshape((len(coords_gr), 3))[:,:2]
				
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

					
	else : 
		print("Le format de fichier ne correspond pas")
		return None
	return None
