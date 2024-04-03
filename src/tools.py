# -*- coding: utf-8 -*-
"""
@author: mehdi daakir
"""

import csts,os,simplekml
import numpy as np
import pandas as pd
from pyproj import Transformer

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

def csv_to_kml(
               input_file,
			   input_type,
               output_file="",
               separator=",",
               doc_name="",
               quiet=False,
               mode="icon",
               label_scale=2,
               icon_scale=1,
               icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png",
			   show_pt_name=False,
			   altitudemode="absolute",
			   show_point=True,
			   show_line=True, 
              ):

	#my data
	if input_type == "extevent" :
		labels = ["time", "day", "state", "lat", "lon", "h", "incert_pla", "incert_hig", "oX", "oY", "oZ"]
	elif input_type == "log" :
		labels = ["uk1", "GNSS", "uk2", "time", "date", "hour", "state", "lat", "lon", "h", "incert_pla", "incert_hig"]	
	data = pd.read_csv(input_file, sep=separator)
	data.columns = labels

	#clear empty coordinates
	lonlat = data[['lon', 'lat']].values
	empty = np.union1d(data[np.isnan(lonlat[:,0])].index, data[np.isnan(lonlat[:,1])].index)
	data = data.drop(empty)

	#reorganise indexes without loosing previous
	data = data.reset_index()


	#show some statistics
	if(not quiet):
		print("\n################ csv to kml ################\n")
		print("==> Input File : %s\n"%input_file)
		print("(#) samples \t = %d" % len(data))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["R"]["name"],[pt["state"] for index, pt in data.iterrows()].count("R"),100*[pt["state"] for index, pt in data.iterrows()].count("R")/len(data)))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["F"]["name"],[pt["state"] for index, pt in data.iterrows()].count("F"),100*[pt["state"] for index, pt in data.iterrows()].count("F")/len(data)))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["N"]["name"],[pt["state"] for index, pt in data.iterrows()].count("N"),100*[pt["state"] for index, pt in data.iterrows()].count("N")/len(data)))

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
	grid_path = "fr_ign_RAF20.tif" 
	transformer = Transformer.from_pipeline("cct +proj=vgridshift +grids=" + grid_path)
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

	# Separation of data type in the kml
	kml_points = kml.newfolder(name="Measured points")
	kml_lines = kml.newfolder(name="Trace")

	line = []
	index_line = 0
	#iterate over the pts
	for index, pt in data.iterrows():
		if show_point :
			description_pt = gen_description_pt(pt)
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
			print(f"Loading {100*index//len(data)} % \r",end="")
	#save kml
	kml.save(output_file)

	if not quiet:
		print("                            ")		
		print("\n==> Job done")
		print("==> Saved as", output_file)
		print("\n############################################\n")

	return None

def gen_description_pt(pt) :
	# generate a description for a point based on the dataframes columns
	index = pt.index
	text = '<table style="border: 1px solid black;>'
	text += f'<tr><td">{" "}</td><td">{" "}</td></tr>\n'
	for i in index :
		if i == "state" :
			value = f"{csts.status_dict[pt[i]]['name']}"
		elif csts.param_dict[i]["unity"] != 's' :
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
