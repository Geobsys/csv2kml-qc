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
			   icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"
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

	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	