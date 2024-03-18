# Get the development version from GitHub
# git clone https://github.com/InseeFrLab/pynsee.git
# cd pynsee
# pip install .[full]

# Subscribe to api.insee.fr and get your credentials!
# Save your credentials with init_conn function :      
from pynsee.utils.init_conn import init_conn
init_conn(insee_key="DxdKUkuOcXaem5zGTD9KWwC6Ev8a", insee_secret="a3IsSAujh2WPtZtvDdSUHqhp0xga")

# Beware : any change to the keys should be tested after having cleared the cache
# Please do : from pynsee.utils import clear_all_cache; clear_all_cache()

from pynsee.geodata import get_geodata_list, get_geodata, GeoFrDataFrame

import math
import geopandas as gpd
import pandas as pd
from pandas.api.types import CategoricalDtype
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import descartes

import warnings
from shapely.errors import ShapelyDeprecationWarning
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

# get geographical data list
geodata_list = get_geodata_list()
# get departments geographical limits
com = get_geodata('ADMINEXPRESS-COG-CARTO.LATEST:commune')

mapcom = gpd.GeoDataFrame(com).set_crs("EPSG:3857")

# area calculations depend on crs which fits metropolitan france but not overseas departements
# figures should not be considered as official statistics
mapcom = mapcom.to_crs(epsg=3035)
mapcom["area"] = mapcom['geometry'].area / 10**6
mapcom = mapcom.to_crs(epsg=3857)

mapcom['REF_AREA'] = 'D' + mapcom['insee_dep']
mapcom['density'] = mapcom['population'] / mapcom['area']

mapcom = GeoFrDataFrame(mapcom)
mapcom = mapcom.translate(departement = ['971', '972', '974', '973', '976'],
                          factor = [1.5, 1.5, 1.5, 0.35, 1.5])

mapcom = mapcom.zoom(departement = ["75","92", "93", "91", "77", "78", "95", "94"],
                 factor=1.5, startAngle = math.pi * (1 - 3 * 1/9))
mapcom

mapplot = gpd.GeoDataFrame(mapcom)
mapplot.loc[mapplot.density < 40, 'range'] = "< 40"
mapplot.loc[mapplot.density >= 20000, 'range'] = "> 20 000"

density_ranges = [40, 80, 100, 120, 150, 200, 250, 400, 600, 1000, 2000, 5000, 10000, 20000]
list_ranges = []
list_ranges.append( "< 40")

for i in range(len(density_ranges)-1):
    min_range = density_ranges[i]
    max_range = density_ranges[i+1]
    range_string = "[{}, {}[".format(min_range, max_range)
    mapplot.loc[(mapplot.density >= min_range) & (mapplot.density < max_range), 'range'] = range_string
    list_ranges.append(range_string)

list_ranges.append("> 20 000")

mapplot['range'] = mapplot['range'].astype(CategoricalDtype(categories=list_ranges, ordered=True))

fig, ax = plt.subplots(1,1,figsize=[15,15])
mapplot.plot(column='range', cmap=cm.viridis,
legend=True, ax=ax,
legend_kwds={'bbox_to_anchor': (1.1, 0.8),
             'title':'density per km2'})
ax.set_axis_off()
ax.set(title='Distribution of population in France')
plt.show()

fig.savefig('pop_france.svg',
            format='svg', dpi=1200,
            bbox_inches = 'tight',
            pad_inches = 0)