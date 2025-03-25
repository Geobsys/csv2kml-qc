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

import math,os
d2r = math.pi/180

# Description of the main tool
desc_tool = "\n***********************\nGNSS data Quality Check\n***********************\n"

# Labels for the different columns: extevent
extevent_labels = ["time", "day", "state", "lat", "lon", "h", "incert_pla", "incert_hig", "oX", "oY", "oZ"]

# Labels for the different columns: log
log_labels = ["uk1", "GNSS", "uk2", "time", "date", "hour", "state", "lat", "lon", "h", "incert_pla", "incert_hig"]

# Default data range: extevent
default_data_range_extevent = "(0,-1,1)"

# Default data range: log
default_data_range_log = "(0,-1,10)"

# Line of # for print purpose
sep_line = "#########################################################################"

location_file = os.path.abspath(__file__)
grid_path = "/".join(location_file.split('/')[:-2]) + "/params/fr_ign_RAF20.tif"

colors_dict={
             "green":"ff3c8e38",
             "orange":"ff007cf5",
             "red":"ff2f2fd3",
             "black":"ff000000"
            }

colors_list = ["ff3c8e38","ff007cf5","ff2f2fd3","ff000000"]

# Define the status of the GNSS position real-time computation
status_dict={
             "R":{"name":"RTK_Fix","color":"green"},
             "F":{"name":"RTK_Float","color":"orange"},
             "N":{"name":"DGNSS","color":"red"},
             "None":{"name":"Unknown","color":"black"}
             }

# Define the styles for the lines
line_styles={
             'LOS': {'id': 'lineStyleLos', 'color': 'ff00ff00'},  # Green
             'NLOS': {'id': 'lineStyleNotLos', 'color': 'ff0000ff'}  # Red
           }
    
# 
param_dict={
             "index":       {'unity' : ''   ,'name' : 'Index'},
             "time":        {'unity' : 's'  ,'name' : 'Time'}, 
             "day":         {'unity' : ''   ,'name' : 'Day'}, 
             "state":       {'unity' : ''   ,'name' : 'State'}, 
             "lat":         {'unity' : '°'  ,'name' : 'Latitude  (WGS84)'}, 
             "lon":         {'unity' : '°'  ,'name' : 'Longitude (WGS84)'}, 
             "h":           {'unity' : 'm'  ,'name' : 'Height'}, 
             "incert_pla":  {'unity' : 'm'  ,'name' : 'Uncertainties Lat-Lon'}, 
             "incert_hig":  {'unity' : 'm'  ,'name' : 'Uncertainty High'}, 
             "oX":          {'unity' : 'rad','name' : 'Orientation X'}, 
             "oY":          {'unity' : 'rad','name' : 'Orientation Y'}, 
             "oZ":          {'unity' : 'rad','name' : 'Orientation Z'},
             "uk1":         {'unity' : ''   ,'name' : 'Unknown'}, 
             "GNSS":        {'unity' : ''   ,'name' : 'GNSS'}, 
             "uk2":         {'unity' : ''   ,'name' : 'Unknown'}, 
             "date":        {'unity' : ''   ,'name' : 'Date'},
             "hour":        {'unity' : ''   ,'name' : 'Hour'},

             "coordX":      {'unity' : 'm'  ,'name' : 'X (RGF93)'}, 
             "coordY":      {'unity' : 'm'  ,'name' : 'Y (RGF93)'}, 
             "coordZ":      {'unity' : 'm'  ,'name' : 'Z (RGF93)'},
             "coordE":      {'unity' : 'm'  ,'name' : 'E (RGF93/L93)'}, 
             "coordN":      {'unity' : 'm'  ,'name' : 'N (RGF93/L93)'}, 
             "coordh":      {'unity' : 'm'  ,'name' : 'h (RGF93/L93)'},
             "H":    {'unity' : 'm'  ,'name' : 'Altitude'},
             "dist":        {'unity' : 'm'  ,'name' : 'Distance since prev pt'},
             "time_left":   {'unity' : 's'  ,'name' : 'Time left'},
             "time_laps":   {'unity' : 's'  ,'name' : 'Time laps since prev pt'},
             "time_elapsed":{'unity' : 's'  ,'name' : 'Time last since first pt'},
             "velocity":    {'unity' : 'm/s','name' : 'Velocity'},
             "n_visible_sat":{'unity' : ''   ,'name' : 'Number of visible satellites'},
             "visible_sat": {'unity' : ''   ,'name' : 'All visible satellites'}
            }