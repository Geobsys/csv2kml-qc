# -*- coding: utf-8 -*-
"""
@author: mehdi daakir
"""

import csts,os,simplekml
import numpy as np
import pandas as pd
from pyproj import Transformer

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
	labels = ["time", "day", "state", "lat", "lon", "h", "incert_pla", "incert_hig", "oX", "oY", "oZ"]
	data = pd.read_csv(input_file, sep=separator)
	data.columns = labels

	#clear empty coordinates
	lonlat = data[['lon', 'lat']].values
	empty = np.union1d(data[np.isnan(lonlat[:,0])].index, data[np.isnan(lonlat[:,1])].index)
	data = data.drop(empty)


	#show some statistics
	if(print_stats):
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

	#iterate over the pts
	for index, pt in data.iterrows():
		custom_pt(
                  kml,
                  float(pt["lon"]),
				  float(pt["lat"]),
				  float(pt["h"]),
                  status=pt[2],
                  mode=mode,
                  label_scale=label_scale,
                  icon_scale=icon_scale,
                  icon_href=icon_href
                 )
	#save kml
	kml.save(output_file)

	return None
