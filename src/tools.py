# -*- coding: utf-8 -*-
"""
@author: mehdi daakir
"""

import csts,os,simplekml
import numpy as np
import pandas as pd
from pyproj import Transformer

# exemple line :
# python3 src/csv_to_kml.py test/EXTENVENT.LOG


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
			  icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"
			 ):

	if(mode=="icon"):
		#append a pt
		pnt = kml.newpoint()

		#edit the point
		pnt.name = name
		pnt.description = description
		pnt.coords = [(lon,lat,h)]
		pnt.style.labelstyle.color = csts.colors_dict[csts.status_dict[status]["color"]]
		pnt.style.labelstyle.scale = label_scale
		pnt.style.iconstyle.color = csts.colors_dict[csts.status_dict[status]["color"]]
		pnt.style.iconstyle.scale = icon_scale
		pnt.style.iconstyle.icon.href = icon_href

	return None

def csv_to_kml(
			   input_file,
			   output_file="",
			   separator=",",
			   doc_name="",
			   print_stats=True,
			   mode="icon",
			   label_scale=2,
			   icon_scale=1,
<<<<<<< Updated upstream
			   icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"
=======
			   icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png",
			   show_pt_name=False,
			   altitudemode="absolute",
			   show_point=True,
			   show_line=True,
			   show_confidence_interval=True,
			   show_building=True
>>>>>>> Stashed changes
			  ):
	
	#my data
	labels = ["time", "day", "state", "lat", "lon", "h", "incert_lat", "incert_lon", "oX", "oY", "oZ"]
	data = pd.read_csv(input_file)
	data.columns = labels
	
	#show some statistics
	if(print_stats):
		print("(#) samples \t = %d" % len(data))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["R"]["name"],[elem[2] for elem in data.values].count("R"),100*[elem[2] for elem in data.values].count("R")/len(data)))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["F"]["name"],[elem[2] for elem in data.values].count("F"),100*[elem[2] for elem in data.values].count("F")/len(data)))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["N"]["name"],[elem[2] for elem in data.values].count("N"),100*[elem[2] for elem in data.values].count("N")/len(data)))

	#instance class
	kml=simplekml.Kml()

	#assign a name
	if(doc_name==""): doc_name=os.path.basename(input_file)
	kml.document.name = doc_name
	
	#assign a name
	if(output_file==""): output_file="".join([os.path.splitext(input_file)[0],".kml"])

		
	# Coordinates transformation to cartesian geocentric 
	transformer = Transformer.from_crs(4326, 4964)
	coordLambert = transformer.transform(data['lat'], data['lon'], data['h'])
	coordLambert = np.array(coordLambert)
	
	data[['coordX', 'coordY', 'coordZ']] = coordLambert.T.round(3)

	# Calculate distance between two points
	data["dist"] = np.sqrt(data["coordX"].diff()**2 + data["coordY"].diff()**2 + data["coordZ"].diff()**2).round(3)
	data.loc[0,"dist"] = 0.

	# Calculate time between to measures
	data["time_laps"] = data["time"].diff().round(3)
	data.loc[0,"time_laps"] = 0.
	
	# Calculate time since start, and until end
	data["time_elapsed"] = data["time_laps"].cumsum().round(3)
	data["time_left"] = data["time_elapsed"].values[-1] - data["time_elapsed"]
	data["time_left"] = data["time_left"].round(3)

	# Calculate instantaneous velocity
	data["velocity"] = data["dist"]/data["time_laps"]
	data["velocity"] = (data["velocity"].shift(-1) + data["velocity"])/2
	data["velocity"] = data["velocity"].round(3)
	print(data["velocity"])
	
	
<<<<<<< Updated upstream
	
	#iterate over the pts	
	for index, pt in data.iterrows():
		description = gen_description(pt)
		custom_pt(
				  kml,
				  float(pt["lon"]),
				  float(pt["lat"]),
				  float(pt["h"]),
				  status=pt["state"],
				  mode=mode,
				  description = description,
				  label_scale=label_scale,
				  icon_scale=icon_scale,
				  icon_href=icon_href
				 )
=======
	#insert the elements into the kml	
	if show_point :
		points = kml.newfolder(name="Measured points")
	if show_line :
		lines = kml.newfolder(name="Trace")
	if show_confidence_interval :
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
		if show_point : 
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
		if show_confidence_interval :
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
	if show_building :
		#calculs of the measures boundarys	
		a = np.max(data["lon"]) + 0.001
		b = np.min(data["lon"]) - 0.001
		c = np.max(data["lat"]) + 0.001
		d = np.min(data["lat"]) - 0.001

		pol = kml.newpolygon(name='A Polygon', altitudemode='relativeToGround')
		pol.outerboundaryis = [(a,c), (a,d), (b,d), (b,c), (a,c)]
		pol.innerboundaryis = [(a,c), (a,d), (b,d), (b,c), (a,c)]
		pol.extrude = 0

>>>>>>> Stashed changes
	#save kml
	kml.save(output_file)

	return None

def gen_description(pt) :
	# generate a description based on the dataframes columns
	index = pt.index
	text = ""
	for i in index :
		if i == "state" :
			value = csts.status_dict[pt[i]]['name']
		else :
			value = str(pt[i])
		text += i + " : " + value + "\n"
	return text	

	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	