# -*- coding: utf-8 -*-
"""
@author: mehdi daakir
"""

import csts,os,simplekml
import numpy as np
import pandas as pd
from pyproj import Transformer
import matplotlib.pyplot as plt

# exemple line :
# python3 src/csv_to_kml.py test/EXTENVENT.LOG
# python3 src/csv_to_kml.py test/20240223.LOG -it 'special' -dr '(0,-1,100)'
import numpy as np


def custom_pt(
			  kml,
			  lon,
			  lat,
			  h,
			  status="None",
			  mode="icon",
			  name="",
			  description="",
			  label_scale=2,
			  icon_scale=1,
			  icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png",
			  show_pt_name=False,
			  altitudemode="absolute"
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


def custom_line(
				kml,
				pts_coords,
				status="None",
				mode="line",
				name="",
				description="",
				width=1,
				altitudemode="absolute"
				):
	if (mode=="line"):
		#append a line
		ls = kml.newlinestring(name=name, description=description, altitudemode = altitudemode)
		ls.coords = pts_coords
		ls.extrude = 0
		ls.style.linestyle.width = width
		ls.style.linestyle.color = csts.colors_dict[csts.status_dict[status]["color"]]
	return None

def custom_int_conf(
				kml,
				pt,
				mode="pyr",
				name="",
				description="",
				altitudemode="absolute",
				color=csts.colors_dict["green"],
				incert_pla=2
				):
	if (mode=="pyr"):
		corners = np.array([(pt["lon"]-incert_pla, pt["lat"]           , pt["altitude"]), 
			 	   			(pt["lon"]       	 , pt["lat"]+incert_pla, pt["altitude"]), 
				   			(pt["lon"]+incert_pla, pt["lat"]           , pt["altitude"]), 
				   			(pt["lon"]           , pt["lat"]-incert_pla, pt["altitude"]), 
				   			(pt["lon"]           , pt["lat"]           , pt["altitude"] + pt["incert_hig"]  )])
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
	

def csv_to_kml(
			   input_file,
			   input_type,
			   output_file="",
			   separator=",",
			   data_range=(),
			   doc_name="",
			   quiet=False,
			   mode="icon",
			   label_scale=2,
			   icon_scale=1,
			   icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png",
			   show_pt_name=False,
			   altitudemode="absolute"
			  ):
	#my data
	if input_type == "normal" :
		labels = ["time", "day", "state", "lat", "lon", "h", "incert_pla", "incert_hig", "oX", "oY", "oZ"]
	elif input_type == "special" :
		labels = ["uk1", "GNSS", "uk2", "time", "date", "hour", "state", "lat", "lon", "h", "incert_pla", "incert_hig"]
	data = pd.read_csv(input_file, sep=separator)
	data.columns = labels
	

	#clear empty coordinates
	lonlat = data[['lon', 'lat']].values
	empty = np.union1d(data[np.isnan(lonlat[:,0])].index, data[np.isnan(lonlat[:,1])].index)
	data = data.drop(empty)

	data_range = np.array(data_range[1:-1].split(",")).astype(int)
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
	if not quiet:
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

		
	# Coordinates transformation to cartesian geocentric 
	transformer = Transformer.from_crs(4326, 4964)
	coordRGF93 = transformer.transform(data['lat'], data['lon'], data['h'])
	coordRGF93 = np.array(coordRGF93)
	
	data[['coordX', 'coordY', 'coordZ']] = coordRGF93.T.round(3)

	# Altitude from ellispoidal height
	transformer = Transformer.from_crs(4326, 2154)
	coordL93 = transformer.transform(data['lat'], data['lon'], data['h'])
	coordL93 = np.array(coordL93)

	data["altitude"] = coordL93[2].round(3)

	# Calculate distance between two points
	data["dist"] = np.sqrt(data["coordX"].diff()**2 + data["coordY"].diff()**2 + data["coordZ"].diff()**2).round(3)
	data.loc[data.index[0],"dist"] = 0.

	# Calculate time between to measures
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
	
	
	#insert the elements into the kml
	points = kml.newfolder(name="Measured points")
	lines = kml.newfolder(name="Trace")
	int_conf = kml.newfolder(name="Confidence interval")

	# Calcul of a scaled version of incertainty
	y = np.log(data["incert_pla"].values)
	y = y+np.abs(np.min(y))
	y = y/(2*np.max(y))
	incert_pla_normalised = y/10000 + 0.00003

	index_color = np.zeros(len(data)).astype(int)
	    
	index_color[:]            = 4
	index_color[y<4*max(y)/5] = 3
	index_color[y<3*max(y)/5] = 2
	index_color[y<2*max(y)/5] = 1
	index_color[y<1*max(y)/5] = 0

	line = []
	index_line = 0
	for index, pt in data.iterrows():

		#insert the points into the kml
		description_pt = gen_description_pt(pt)

		custom_pt(
				  points,
				  float(pt["lon"]),
				  float(pt["lat"]),
				  float(pt["altitude"]),
				  name="Point n° " + str(index),
				  status=pt["state"],
				  mode=mode,
				  description=description_pt,
				  label_scale=label_scale,
				  icon_scale=icon_scale,
				  icon_href=icon_href,
				  show_pt_name=show_pt_name,
				  altitudemode=altitudemode
				 )
		
		#insert the confidence intervals in the kml
		#color choose
		color = csts.colors_grade[index_color[index]]
		incert_pla = incert_pla_normalised[index]
		custom_int_conf(
				int_conf,
				pt,
				mode="pyr",
				name="Point n° " + str(index),
				description="",
				altitudemode=altitudemode,
				color=color,
				incert_pla=incert_pla
				)
		
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
				description_line = gen_description_line(line)
				if len(line[0]) > 1 :
					#insert the lines into the kml
					custom_line(
								lines,
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
		if not quiet:
			print(f"Loading {100*index//len(data)} % \r",end="")
	
	#calculs of the measures boundarys	
	a = np.max(data["lon"]) + 0.001
	b = np.min(data["lon"]) - 0.001
	c = np.max(data["lat"]) + 0.001
	d = np.min(data["lat"]) - 0.001

	pol = kml.newpolygon(name='A Polygon', altitudemode='relativeToGround')
	pol.outerboundaryis = [(a,c), (a,d), (b,d), (b,c), (a,c)]
	pol.innerboundaryis = [(a,c), (a,d), (b,d), (b,c), (a,c)]
	pol.extrude = 0

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






	