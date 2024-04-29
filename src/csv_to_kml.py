# -*- coding: utf-8 -*-
"""
@author: mehdi daakir, gabin bourlon, axel debock, felix mercier, clement cambours
"""

#todo:
#do shared KML styles
#force 2D mode ?
#polygone mode using sigma


import tools,argparse
import numpy as np

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description="*************** csv_to_kml ***************")
	# Import parameters
	parser.add_argument('input_file',type=str,help="input file from the Geostix in .csv format")
	parser.add_argument('-it', '--input_type', type=str, help="input file type between 'extevent' and 'log' (Default=extevent)", default="extevent",choices=["extevent", "log"])
	parser.add_argument('-sep','--separator',type=str,help="separator used in the .csv file (Default=,)",default=",")
	# Export parameters
	parser.add_argument('-o','--output_file',type=str,help="output file in .kml format (Default=./input_file.kml)",default="")
	parser.add_argument('-name','--doc_name',type=str,help="kml document name",default="")
	parser.add_argument('--quiet',action="store_true",help="print some statistics")
	# Apearance parameters
	parser.add_argument('-m','--mode',type=str,help="representation mode (Default=icon)",default="icon",choices=["icon"])
	parser.add_argument('-ls','--label_scale',type=float,help="label scale (Default=2)",default=2)
	parser.add_argument('-is','--icon_scale',type=float,help="icon scale (Default=1)",default=1)
	parser.add_argument('-ih','--icon_href',type=str,help="icon href (Default=http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png)",default="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png")
	parser.add_argument('--show_pt_name',action="store_true",help="Hide the points names")
	# General parameters
	parser.add_argument('-dr','--data_range',type=str, help="Range of data from start (s), to end (e), with a step (t) : (s,e,t). e and t are optionnal. (Default=(0,-1,100))",default='(0,-1,100)')
	parser.add_argument('-am','--altitudemode',type=str,help="See simplekml .Altitudemode (absolute, relativeToGround, clampToGround). (Default=absolute)", default="absolute",choices=["absolute", "relativeToGround", "clampToGround"])
	# Point
	parser.add_argument('--show_point',action="store_false",help="Don't show points")
	# Line
	parser.add_argument('--show_line',action="store_false",help="Don't show the lines between points")
	# Confidence interval
	parser.add_argument('--show_conf_int',action="store_false",help="Don't show the confidence interval")
	parser.add_argument('-sp','--scale_factor_pla',type=float,help="Scale factor for planimetric uncertainty. (Default=1)", default=1)
	parser.add_argument('-mp','--incert_pla_max',type=float,help="Maximum planimetric uncertainty. (Default=Nan)", default=np.nan)
	parser.add_argument('-sh','--scale_factor_hig',type=float,help="Scale factor for altimetric uncertainty. (Default=1)", default=1)
	parser.add_argument('-mh','--incert_hig_max',type=float,help="Maximum altimetric uncertainty. (Default=Nan)", default=np.nan)
	# Buildings
	parser.add_argument('--show_buildings',action="store_false",help="Don't show the show_buildings")
	parser.add_argument('-margin',type=float,help="margin (in geographical degres) around the workfield for building modelisation (Default=0.001)",default=0.001)
	parser.add_argument('-departments',type=str,help="input shp buildings file path",default='')
	parser.add_argument('--save_buildings',action="store_true",help="If you want to save the shp file of your buildings")
	# Ephemerids
	parser.add_argument('--calc_ephemerids',action="store_false",help="Don't calculate the ephemerids")
	parser.add_argument('-rn','--rinex_name',type=str,help="name of the observation and rinex file (without the extension)",default='')

	# Frustum 
	parser.add_argument('--show_orientation', action="store_false",help="Don't show frustum")
	parser.add_argument('-fr_captor', type=float,help="distance factor of the near face of the frustum. (Default=1)", default=1)
	parser.add_argument('-fr_focal', type=float,help="focal distance. (Default=10)", default=10)
	parser.add_argument('-fr_distance',type = float, help=" distance between the near plane et the far plane. (Default=5)", default=5)
	parser.add_argument('-fr_alpha',type=float, help="angle between camera reference frame and geographical reference frame. (Default=0)", default=0)
	parser.add_argument('-fr_beta',type=float, help="angle between camera reference frame and geographical reference frame. (Default=0)",default=0)
	parser.add_argument('-fr_gamma',type=float, help="angle between camera reference frame and geographical reference frame. (Default=0)",default=0)

	args=parser.parse_args()
	
	tools.csv_to_kml(
					 args.input_file,
					 args.input_type,
					 args.separator,
					 args.output_file,
					 args.doc_name,
					 args.quiet,
					 args.mode,
					 args.label_scale,
					 args.icon_scale,
					 args.icon_href,
					 args.show_pt_name,
					 args.data_range,
					 args.altitudemode,
					 args.show_point,
					 args.show_line,
					 args.show_conf_int,
                     args.scale_factor_pla,
                     args.incert_pla_max,
                     args.scale_factor_hig,
                     args.incert_hig_max,
					 args.show_buildings,
					 args.margin,
					 args.departments,
					 args.save_buildings,
					 args.calc_ephemerids,
					 args.rinex_name,
					 args.show_orientation,
					 args.fr_captor,
					 args.fr_focal,
					 args.fr_distance,
					 args.fr_alpha,
					 args.fr_beta,
					 args.fr_gamma
                    )
