# -*- coding: utf-8 -*-
"""
@author: mehdi daakir, gabin bourlon, axel debock, felix mercier, clement cambours
"""

colors_dict={
             "green":"ff3c8e38",
             "orange":"ff007cf5",
             "red":"ff2f2fd3",
             "black":"ff000000"
            }

colors_list = ["ff3c8e38","ff007cf5","ff2f2fd3","ff000000"]

status_dict={
             "R":{"name":"RTK_Fix","color":"green"},
             "F":{"name":"RTK_Float","color":"orange"},
             "N":{"name":"DGNSS","color":"red"},
             "None":{"name":"Unknown","color":"black"}
             }

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
             "altitude":    {'unity' : 'm'  ,'name' : 'Altitude'},
             "dist":        {'unity' : 'm'  ,'name' : 'Distance since prev pt'},
             "time_left":   {'unity' : 's'  ,'name' : 'Time left'},
             "time_laps":   {'unity' : 's'  ,'name' : 'Time laps since prev pt'},
             "time_elapsed":{'unity' : 's'  ,'name' : 'Time last since first pt'},
             "velocity":    {'unity' : 'm/s','name' : 'Velocity'},
             "n_visible_sat":{'unity' : ''   ,'name' : 'Number of visible satellites'},
             "visible_sat": {'unity' : ''   ,'name' : 'All visible satellites'}
            }