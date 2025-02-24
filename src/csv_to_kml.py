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
import csts,tool
# Packages:
import argparse
import numpy as np

if __name__ == "__main__":

	# Create the parser
	parser = argparse.ArgumentParser(description=csts.desc_tool)

	# Import parameters
	parser.add_argument('input_file', type=str, help="Input file from the GEOSTIX (or any) in .csv format")
	parser.add_argument('-it', '--input_type', type=str, help="Input file type between 'extevent' and 'log' (Default=log)", default="log", choices=["extevent","log"])
	parser.add_argument('-sep', '--separator', type=str, help="Separator used in the .csv file (Default=,)", default=",")

	# Export parameters
	parser.add_argument('-o', '--output_file', type=str, help="Output file in .kml format (Default=./input_file.kml)", default="")
	parser.add_argument('-name', '--doc_name', type=str, help="KML document name (Default=input_file)", default="")
	parser.add_argument('--quiet', action="store_true", help="Do not print statistics or other information")
	
	# Apearance parameters
	parser.add_argument('-m', '--mode', type=str, help="Representation mode (Default=icon)", default="icon", choices=["icon"])
	parser.add_argument('-ls', '--label_scale', type=float, help="Label scale (Default=2)", default=2)
	parser.add_argument('-is', '--icon_scale', type=float, help="Icon scale (Default=1)", default=1)
	parser.add_argument('-ih', '--icon_href', type=str, help="Icon href (Default=http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png)", default="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png")
	parser.add_argument('--show_pt_name', action="store_true", help="Display points names in the KML viewer")
	
	# General parameters
	parser.add_argument('-dr', '--data_range', type=str, help="Range of data from start (s), to end (e), with a step (t) : (s,e,t). e and t are optionnal. If -it 'extevent' Default=(0,-1,1), -it 'log' Default=(0,-1,10))", default='default')
	parser.add_argument('-am', '--altitude_mode', type=str, help="Altitudemode (absolute, relativeToGround, clampToGround), see simplekml documentation (Default=absolute)", default="absolute", choices=["absolute","relativeToGround","clampToGround"])
	
	# Point
	parser.add_argument('--hide_pts', action="store_true", help="Don't show points")
	
	# Line
	parser.add_argument('--hide_lines', action="store_true", help="Don't show the lines between points")

	# Confidence interval
	parser.add_argument('--hide_conf_int', action="store_true", help="Don't show the confidence interval")
	parser.add_argument('-sp', '--scale_factor_pla', type=float, help="Scale factor for planimetric uncertainty (Default=1)", default=1)
	parser.add_argument('-mp', '--incert_pla_max', type=float, help="Maximum planimetric uncertainty (Default=Nan)", default=np.nan)
	parser.add_argument('-sh', '--scale_factor_hig', type=float, help="Scale factor for altimetric uncertainty (Default=1)", default=1)
	parser.add_argument('-mh', '--incert_hig_max', type=float, help="Maximum altimetric uncertainty (Default=Nan)", default=np.nan)
	
	# Buildings
	parser.add_argument('-buildings', type=str, help="Input folder where .shp buildings file is stored, or directly the .shp file path. Warning, if there are several files in the folder, the programm will choose the first one (alphabetic order) to define the schema, and then look to the others for the intersection if the both schema match.", default='')
	parser.add_argument('--hide_buildings', action="store_true", help="Don't show buildings in the .kml file")
	parser.add_argument('-margin', type=float, help="Margin (in meters) around the workfield for buildings filtering (Default=250)", default=250)
	parser.add_argument('-sb', '--save_buildings', type=str, help="Save .shp file containing filtred buildings (Default=)", default="")
	parser.add_argument('--show_extent', action="store_true", help="Add a layer representing the extent of buildings used for collision computation", default=True)
	
	# Frustum 
	parser.add_argument('--hide_frustum', action="store_true", help="Don't show frustum")
	parser.add_argument('-fr_sensor', type=float, help="Distance factor of the near face of the frustum. (Default=1)", default=1)
	parser.add_argument('-fr_focal', type=float, help="Focal distance. (Default=10)", default=1)
	parser.add_argument('-fr_distance', type = float, help="Distance between the near plane and the far plane. (Default=5)", default=5)
	parser.add_argument('-fr_alpha', type=float, help="Angle around X-axis between camera reference frame and geographical reference frame. (Default=0)", default=0)
	parser.add_argument('-fr_beta', type=float, help="Angle around Y-axis between camera reference frame and geographical reference frame. (Default=0)", default=0)
	parser.add_argument('-fr_gamma', type=float, help="Angle around Z-axis between camera reference frame and geographical reference frame. (Default=0)", default=0)
	
	# RINEX data
	parser.add_argument('-ro', '--rinex_name_obs', type=str, help="Path of the observation RINEX file", default='')
	parser.add_argument('-rn', '--rinex_name_nav', type=str, help="Path of the navigation RINEX file", default='')


	# Collision
	parser.add_argument('--detect_nlos', action="store_true", help="Perform receiver-satellite and buildings collision to detect NLOS satellites")
	parser.add_argument('-ll','--line_length', type=float, help="Line lenght in meters to reprensent receiver-satellite rays (Default=250)", default=250)

	
	args=parser.parse_args()

	print("args.hide_pts",args.hide_pts)
	
	tool.csv_to_kml(
					 args.input_file, # Input file
					 args.input_type, # Input file type: 'extevent' or 'log'
					 args.separator, # Separator used in the .csv file: ','
					 args.output_file, # Output KML file: ''
					 args.doc_name, # KML document name: ''
					 args.quiet, # Quiet mode: True
					 args.mode, # Representation mode: 'icon'
					 args.label_scale, # Label scale: 2
					 args.icon_scale, # Icon scale: 1
					 args.icon_href, # Icon href: 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
					 args.show_pt_name, # Display points names in the KML viewer: False
					 args.data_range, # Range of data: if -it 'extevent' Default=(0,-1,1), -it 'log' Default=(0,-1,10)
					 args.altitude_mode, # Altitudemode: 'absolute'
					 args.hide_pts, # Hide points: False
					 args.hide_lines, # Hide lines: False
					 args.hide_conf_int, # Hide confidence interval: False
                     args.scale_factor_pla, # Scale factor for planimetric uncertainty: 1
                     args.incert_pla_max, # Maximum planimetric uncertainty: Nan
                     args.scale_factor_hig,
                     args.incert_hig_max,
					 args.hide_buildings,
					 args.margin, # Margin around the workfield for buildings filtering: 250
					 args.buildings,
					 args.save_buildings,
					 args.hide_frustum,
					 args.fr_sensor,
					 args.fr_focal,
					 args.fr_distance,
					 args.fr_alpha,
					 args.fr_beta,
					 args.fr_gamma,
					 args.detect_nlos, # Perform receiver-satellite and buildings collision to detect NLOS satellites: False
					 args.rinex_name_obs,
					 args.rinex_name_nav,
					 args.line_length,
					 args.show_extent
                    )