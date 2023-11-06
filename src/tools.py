# -*- coding: utf-8 -*-
"""
@author: mehdi daakir
"""

import csts,os,simplekml

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
