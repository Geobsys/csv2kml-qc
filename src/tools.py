# -*- coding: utf-8 -*-
"""
@author: mehdi daakir
"""

import csts,os #simplekml
import numpy as np
import pandas as pd
from pyproj import Transformer

#création du dataframe à partir du csv
colName = ["time", "day", "state", "lat", "lon", "h", "incert_lat", "incert_lon", "oX", "oY", "oZ"]
df = pd.read_csv("../test/EXTENVENT.LOG", delimiter=",", header=None)
df.columns = colName

#transformation des coordonnées (EPSG:432 vers EPSG:4964 (XYZ)) et stockage dans un autre dataframe
transformer = Transformer.from_crs(4326, 4964)
coordLambert = transformer.transform(df['lat'], df['lon'], df['h'])
coordLambert = np.array(coordLambert)

df2 = pd.DataFrame(coordLambert.T, columns=['coordX', 'coordY', 'coordZ'])

# #Fusion des deux dataframes
df = pd.concat([df, df2], axis=1)


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
	data=[]

	#load input file
	f = open(input_file, 'r')
	for line in f:
		data.append(line.strip().split(separator))
	f.close()

	#show some statistics
	if(print_stats):
		print("(#) samples \t = %d" % len(data))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["R"]["name"],[elem[2] for elem in data].count("R"),100*[elem[2] for elem in data].count("R")/len(data)))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["F"]["name"],[elem[2] for elem in data].count("F"),100*[elem[2] for elem in data].count("F")/len(data)))
		print("(#) %s \t = %d (%.1f%%)" % (csts.status_dict["N"]["name"],[elem[2] for elem in data].count("N"),100*[elem[2] for elem in data].count("N")/len(data)))

	#instance class
	kml=simplekml.Kml()

	#assign a name
	if(doc_name==""): doc_name=os.path.basename(input_file)
	kml.document.name = doc_name

	#assign a name
	if(output_file==""): output_file="".join([os.path.splitext(input_file)[0],".kml"])

	#iterate over the pts
	for pt in data:
		custom_pt(
                  kml,
                  float(pt[4]),
                  float(pt[3]),
                  float(pt[5]),
                  status=pt[2],
                  mode=mode,
                  label_scale=label_scale,
                  icon_scale=icon_scale,
                  icon_href=icon_href
                 )
	#save kml
	kml.save(output_file)

	return None

def get_dist_point_to_point(dataframe, index):  
    return  (dataframe.coordX[index] - dataframe.coordX[index-1])**2 + (dataframe.coordY[index] - dataframe.coordY[index-1])**2 + (dataframe.coordZ[index] - dataframe.coordZ[index-1])**2
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    