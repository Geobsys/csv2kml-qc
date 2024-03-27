# -*- coding: utf-8 -*-
"""
@author: mehdi daakir
"""

#todo:
#do shared KML styles
#force 2D mode ?
#polygone mode using sigma


import tools,argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="*************** csv_to_kml ***************")
    # data input/output
    parser.add_argument('input_file',type=str,help="input file from the Geostix in .csv format")
    parser.add_argument('-it', '--input_type', type=str, help="input file type between 'normal' and 'special'", default="normal",choices=["normal", "special"])
    parser.add_argument('-o' ,'--output_file',type=str,help="output file in .kml format (Default=./input_file.kml)",default="")
    parser.add_argument('-sep','--separator',type=str,help="separator used in the .csv file (Default=,)",default=",")
    parser.add_argument('-dr','--data_range',type=str, help="Range of data from start (s), to end (e), with a step (t) : (s,e,t). e and t are optionnal",default='(0,-1,100)')
    parser.add_argument('-name','--doc_name',type=str,help="kml document name",default="")
    parser.add_argument('--quiet',action="store_true",help="print some statistics")
    # style parameters
    parser.add_argument('-m' ,'--mode',type=str,help="representation mode",default="icon",choices=["icon"])
    parser.add_argument('-ls','--label_scale',type=float,help="label scale (Default=2)",default=2)
    parser.add_argument('-is','--icon_scale',type=float,help="icon scale (Default=1)",default=1)
    parser.add_argument('-ih','--icon_href',type=str,help="icon href (Default=http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png)",default="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png")
    parser.add_argument('-sn','--show_pt_name',type=bool,help="True : showing the label, False : Hiding it", default=False)
    parser.add_argument('-am','--altitudemode',type=str,help="See simplekml .Altitudemode (absolute, relativeToGround, clampToGround)", default="absolute",choices=["absolute", "relativeToGround", "clampToGround"])
    # processing options
    parser.add_argument('--show_point',action="store_false",help="Don't show points")
    parser.add_argument('--show_line',action="store_false",help="Don't show the lines between points")
    parser.add_argument('--show_confidence_interval',action="store_false",help="Don't show the confidences intervals of points")
    parser.add_argument('--show_building',action="store_false",help="Don't show the buildings around thes points")

    args=parser.parse_args()

    
    tools.csv_to_kml(
                     args.input_file,
                     args.input_type,
                     args.output_file,
                     args.separator,
                     args.data_range,
                     args.doc_name,
                     args.quiet,
                     args.mode,
                     args.label_scale,
                     args.icon_scale,
                     args.icon_href,
                     args.show_pt_name,
                     args.altitudemode,
                     args.show_point,
                     args.show_line,
                     args.show_confidence_interval,
                     args.show_building
                    )
