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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

################################
# Imports :
################################
# Python files:
import csts
import functions

# Packages:
import os
import simplekml
import pyproj
import fiona
import numpy as np
import pandas as pd

"""
 Main Function, transform the input data into a KML file (with many options)

 This code has been updated to handle three input types: 'extevent', 'log', and 'kmltraj'.
 In particular, when 'kmltraj' is selected, we parse a KML file describing a single polyline
 and discretize it in time/space according to parameters:
   start_time_kml, end_time_kml, dist_step_kml, velocity_kml, and now a date (date_str).
   
 The function then optionally:
   - performs coordinate transformations,
   - adds buildings,
   - computes collisions (NLOS),
   - draws lines, confidence intervals, frustums, etc.
"""
def csv_to_kml(
    input_file,            # string
    input_type,            # string: 'extevent', 'log', or 'kmltraj'
    separator=",",         # string
    output_file="",        # string
    doc_name="",           # string
    quiet=True,            # boolean
    mode="icon",           # string
    label_scale=2,         # integer
    icon_scale=1,          # integer
    icon_href="http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png", # string
    show_pt_name=False,    # boolean
    data_range='default',  # string
    altitude_mode="absolute", # string
    hide_pts=False,        # boolean
    hide_lines=False,      # boolean
    hide_conf_int=False,   # boolean
    scale_factor_pla=1,    # float
    incert_pla_max=np.nan, # float
    scale_factor_hig=1,    # float
    incert_hig_max=np.nan, # float
    hide_buildings=True,   # boolean
    margin=250,            # float
    buildings='',          # string
    save_buildings='intersection',  # string
    hide_frustum=False,    # boolean
    fr_sensor=1,           # float
    fr_focal=10,           # float
    fr_distance=5,         # float
    fr_alpha=0,            # float
    fr_beta=0,             # float
    fr_gamma=0,            # float
    detect_nlos=False,     # boolean
    rinex_obs="",
    rinex_nav="",
    line_length=250,
    show_extent=True
):
    """Main function generating a KML file from an input dataset."""
    if not quiet:
        print(csts.desc_tool)
        print("==> Input File : %s\n" % input_file)
    else:
        if input_type == "extevent":
            labels = csts.extevent_labels
        elif input_type == "log":
            labels = csts.log_labels
        else:
            print("Unsupported input_type. Must be in ['extevent','log','kmltraj'].")
            return None
        try:
            data = pd.read_csv(input_file, sep=separator, header=None)
        except Exception as e:
            print(f"Error reading CSV file '{input_file}' with sep='{separator}': {e}")
            return None
        try:
            data.columns = labels
        except:
            print("The input type isn't the right one, or isn't supported. \nYou can change the input type by using the command -it.")
            return None
    
    # 2. Some stats on the data
    nb_elem = len(data)
    if data_range == 'default':
        if input_type == 'extevent':
            data_range = csts.default_data_range_extevent
        elif input_type == 'log':
            data_range = csts.default_data_range_log
        else:
            data_range = "(0,-1,1)"
    try:
        dr_vals = data_range.strip()[1:-1]
        data_range_array = np.array(dr_vals.split(",")).astype(int)
    except:
        print("The data_range parameter (-dr) isn't in the right format.")
        return None
    if "lon" in data.columns and "lat" in data.columns:
        lon_lat = data[['lon','lat']].values
        empt1 = np.where(np.isnan(lon_lat[:,0]))[0]
        empt2 = np.where(np.isnan(lon_lat[:,1]))[0]
        empty_indexes = np.union1d(empt1, empt2)
        data = data.drop(empty_indexes)
    nb_elem_rm_empty = len(data)
    if len(data) > 1:
        if len(data_range_array) == 3:
            s, e, t = data_range_array
            data = data[s:e:t]
        elif len(data_range_array) == 2:
            s, e = data_range_array
            data = data[s:e:1]
        elif len(data_range_array) == 1:
            s = data_range_array[0]
            data = data[s:-1:1]
    nb_elem_decim = len(data)
    if not quiet:
        print(csts.sep_line)
        print("(#) original samples = %d" % nb_elem)
        print("(#) samples after removing empty coordinates = %d" % nb_elem_rm_empty)
        print("(#) samples after decimation = %d" % nb_elem_decim)
        print(csts.sep_line)
    data = data.reset_index(drop=True)
    if not quiet and "state" in data.columns:
        print(csts.sep_line)
        print("(#) samples = %d" % len(data))
        count_R = (data["state"]=="R").sum()
        count_F = (data["state"]=="F").sum()
        count_N = (data["state"]=="N").sum()
        total = len(data)
        print("(#) %s = %d (%.1f%%)" % (csts.status_dict["R"]["name"], count_R, 100*count_R/total))
        print("(#) %s = %d (%.1f%%)" % (csts.status_dict["F"]["name"], count_F, 100*count_F/total))
        print("(#) %s = %d (%.1f%%)" % (csts.status_dict["N"]["name"], count_N, 100*count_N/total))
        print(csts.sep_line)
    
    # 3. KML creation
    kml = simplekml.Kml()
    if doc_name == "":
        doc_name = os.path.basename(input_file)
    kml.document.name = doc_name
    if output_file == "":
        output_file = "".join([os.path.splitext(input_file)[0], ".kml"])
    
    if all(col in data.columns for col in ["lon", "lat", "h"]):
        coord_XYZ = functions.llh_2_XYZ(data["lon"], data["lat"], data["height"] if "height" in data.columns else data["h"])
        data[["coordX","coordY","coordZ"]] = np.array(coord_XYZ).T.round(3)
        coord_ENh = functions.XYZ_2_ENh(data["coordX"], data["coordY"], data["coordZ"])
        data[["coordE","coordN","coordh"]] = np.array(coord_ENh).T.round(3)
        coord_LLH = functions.llh_2_llH(data["lon"], data["lat"], data["height"] if "height" in data.columns else data["h"])
        data["H"] = coord_LLH[2].round(3)
    
    if "coordX" in data.columns and "coordY" in data.columns and "coordZ" in data.columns:
        data["dist"] = np.sqrt(data["coordX"].diff()**2 + data["coordY"].diff()**2 + data["coordZ"].diff()**2).round(3)
        data.loc[data.index[0], "dist"] = 0.
    if "time" in data.columns:
        data["time_laps"] = data["time"].diff().round(3)
        data.loc[data.index[0], "time_laps"] = 0.
        data["time_elapsed"] = data["time_laps"].cumsum().round(3)
        data["time_left"] = data["time_elapsed"].values[-1] - data["time_elapsed"]
        data["time_left"] = data["time_left"].round(3)
        data["velocity"] = data["dist"] / data["time_laps"]
        data["velocity"] = (data["velocity"].shift(-1) + data["velocity"]) / 2
        data["velocity"] = data["velocity"].round(3)
    
    size = 1000
    incert_pla_factor_E, incert_pla_factor_N = functions.calcul_incert_pla_factor(data, size)
    
    # Use the function arguments for rotation angles (passed as parameters)
    rotation_matrixX2 = np.array([
        [1, 0, 0],
        [0, np.cos(fr_alpha), -np.sin(fr_alpha)],
        [0, np.sin(fr_alpha), np.cos(fr_alpha)]
    ])
    rotation_matrixY2 = np.array([
        [np.cos(fr_beta), 0, np.sin(fr_beta)],
        [0, 1, 0],
        [-np.sin(fr_beta), 0, np.cos(fr_beta)]
    ])
    rotation_matrixZ2 = np.array([
        [np.cos(fr_gamma), -np.sin(fr_gamma), 0],
        [np.sin(fr_gamma), np.cos(fr_gamma), 0],
        [0, 0, 1]
    ])
    product_rotation_matrix = rotation_matrixX2 @ rotation_matrixY2 @ rotation_matrixZ2
    
    # 4. Buildings
    buildings_infos = {}
    shp_out_file = ""
    if buildings != "":
        kml_buildings_layer = kml.newfolder(name='Buildings')
        if "coordE" in data.columns and "coordN" in data.columns:
            E_min, E_max = np.min(data["coordE"]), np.max(data["coordE"])
            N_min, N_max = np.min(data["coordN"]), np.max(data["coordN"])
            bbox = (E_min - margin, N_min - margin, E_max + margin, N_max + margin)
        else:
            bbox = (0,0,0,0)
            if not quiet:
                print("Warning: No coordE/coordN found => cannot compute bounding box properly.")
        layers = []
        if buildings.endswith(".shp"):
            base_path = os.path.dirname(buildings)
            shp_name = os.path.basename(buildings)
            layers = [shp_name[:-4]]
            buildings = base_path if base_path else "./"
        if "/" not in save_buildings:
            shp_out_file = os.path.join(buildings, "")
        if save_buildings.endswith(".shp"):
            shp_out_file += save_buildings
        else:
            shp_out_file += (save_buildings + ".shp")
        if len(layers) == 0:
            layers = fiona.listlayers(buildings)
        with fiona.open(buildings, 'r', layer=layers[0]) as src:
            schema = src.schema
        with fiona.open(shp_out_file, 'w', driver='ESRI Shapefile', schema=schema) as sink:
            if not quiet:
                print("Selecting buildings on the workfield ...\r", end="")
            for lay in layers:
                with fiona.open(buildings, 'r', layer=lay) as src2:
                    if src2.schema == schema:
                        filtered_bat = src2.filter(bbox=bbox)
                        sink.writerecords(filtered_bat)
                    else:
                        print(f"The shapefile '{lay}' schema is different from '{layers[0]}' => skipping.")
            if not quiet:
                print("Selecting buildings on the workfield done.")
        buildings_infos = functions.shp2kml(shp_out_file, kml_buildings_layer, quiet)
        if save_buildings == 'intersection':
            if not quiet:
                print("Deleting temporary files ...")
            for ext in [".shp", ".dbf", ".cpg", ".shx"]:
                try:
                    os.remove(shp_out_file[:-4] + ext)
                except:
                    pass
    
    # 5. Create subfolders for points, lines, etc.
    if not hide_pts:
        kml_points_layer = kml.newfolder(name="Measured points")
    if not hide_lines:
        kml_lines_layer = kml.newfolder(name="Trace")
    if not hide_conf_int:
        kml_int_conf_layer = kml.newfolder(name="Confidence intervals")
    if not hide_frustum and input_type == "extevent":
        kml_frustum_layer = kml.newfolder(name="Frustums")
    if detect_nlos:
        kml_collisions_layer = kml.newfolder(name="Collisions")
    
    if show_extent and buildings != "" and len(buildings_infos) > 0:
        kml_bbox_layer = kml.newfolder(name="Extent")
        if "coordh" in data.columns:
            h_min = np.min(data["coordh"])
        else:
            h_min = 0.0
        coordMinLLh = functions.ENh_2_llh(bbox[0], bbox[1], h_min)
        coordMaxLLh = functions.ENh_2_llh(bbox[2], bbox[3], h_min)
        lat_min, lat_max = coordMinLLh[0], coordMaxLLh[0]
        lon_min, lon_max = coordMinLLh[1], coordMaxLLh[1]
        bbox_llh = [
            (lon_min, lat_min, h_min),
            (lon_max, lat_min, h_min),
            (lon_max, lat_max, h_min),
            (lon_min, lat_max, h_min),
            (lon_min, lat_min, h_min)
        ]
        polygon_extent = kml_bbox_layer.newpolygon(name="Bounding Box")
        polygon_extent.outerboundaryis = bbox_llh
        polygon_extent.style.polystyle.color = simplekml.Color.changealpha("7f", simplekml.Color.red)
    
    # 6. NLOS detection if requested
    sat_infos = {}
    if detect_nlos and buildings != "" and len(buildings_infos) > 0 and (rinex_obs or rinex_nav):
        if rinex_obs and rinex_nav:
            sat_infos = functions.get_sat_infos(data, rinex_obs, rinex_nav)
        sat_infos = functions.compute_collisions(sat_dict=sat_infos, building_dict=buildings_infos, dist_building=300, show=False)
    
    # 7. Generate KML objects
    line = []
    index_line = 0
    for idx, pt in data.iterrows():
        # Points
        if not hide_pts:
            descr_point = functions.gen_description_pt(pt, data["index"].max() if "index" in data.columns else len(data)-1)
            functions.custom_pt(
                kml_points_layer,
                pt,
                mode=mode,
                name="Point n° " + str(idx),
                desc=descr_point,
                label_scale=label_scale,
                icon_scale=icon_scale,
                icon_href=icon_href,
                show_pt_name=show_pt_name,
                altitude_mode=altitude_mode
            )
        # Confidence intervals
        if not hide_conf_int:
            color_ci = csts.colors_dict[csts.status_dict[pt["state"]]["color"]] if "state" in pt else csts.colors_dict["green"]
            functions.custom_int_conf(
                kml_int_conf_layer,
                pt,
                mode="pyr",
                name="Point n° " + str(idx),
                altitudemode=altitude_mode,
                color=color_ci,
                incert_pla_factor_E=incert_pla_factor_E,
                incert_pla_factor_N=incert_pla_factor_N,
                scale_factor_pla=scale_factor_pla,
                incert_pla_max=incert_pla_max,
                scale_factor_hig=scale_factor_hig,
                incert_hig_max=incert_hig_max
            )
        # Frustum (only for extevent)
        if not hide_frustum and input_type == "extevent":
            functions.custom_frustum(
                kml_frustum_layer,
                pt,
                product_rotation_matrix,
                mode="fur",
                name="",
                description="",
                altitudemode=altitude_mode,
                incert_pla_factor_E=incert_pla_factor_E,
                incert_pla_factor_N=incert_pla_factor_N,
                fr_sensor=fr_sensor,
                fr_focal=fr_focal,
                fr_distance=fr_distance
            )
        # Lines
        if not hide_lines and "state" in data.columns:
            if idx + 1 < len(data):
                if len(line) == 0:
                    line = [
                        [pt["state"]],
                        [pt["index"]],
                        [(pt["lon"], pt["lat"], pt["H"])]
                    ]
                elif line[0][0] == pt["state"]:
                    line[0].append(pt["state"])
                    line[1].append(pt["index"])
                    line[2].append((pt["lon"], pt["lat"], pt["H"]))
                else:
                    if len(line[0]) > 1:
                        descr_line = functions.gen_description_line(line)
                        functions.custom_line(
                            kml_lines_layer,
                            line[2],
                            status=line[0][0],
                            mode="line",
                            name="Segment n° " + str(index_line),
                            description=descr_line,
                            width=5,
                            altitudemode=altitude_mode
                        )
                        index_line += 1
                    line = [
                        [pt["state"]],
                        [pt["index"]],
                        [(pt["lon"], pt["lat"], pt["H"])]
                    ]
        if not quiet:
            print(f"Generating kml objects {100*idx//len(data)} % \r", end="")
    
    if detect_nlos and buildings_infos and sat_infos:
        functions.draw_collision_rays(sat_dict=sat_infos, kml_layer=kml_collisions_layer)
    
    if not quiet:
        print("Generating kml objects done.")
        print("Saving kml file ...\r", end="")
    
    kml.save(output_file)
    
    if not quiet:
        print(csts.sep_line)
        print("\n==> Job done")
        print("==> KML output saved as", output_file)
        if (buildings != "") and (save_buildings != "intersection"):
            print("==> SHP output saved as", shp_out_file if shp_out_file else "No shapefile saved.")
        print(csts.sep_line)
    return None
