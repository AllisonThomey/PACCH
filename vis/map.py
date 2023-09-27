# plotting
import os
import json
import rasterio
from rasterio.mask import mask
import pandas
import geopandas
import matplotlib.pyplot as plt
import seaborn as sns
import contextily as cx

filename_in = 'all_global_vul_pop.csv'
folder_in = os.path.join('data', 'processed', 'results' , 'csv')
path_in = os.path.join(folder_in, filename_in)
data = pandas.read_csv(path_in)

#import our boundaries data
filename = 'global_outline.shp'
path_in = os.path.join('data', 'processed', filename) 
boundaries = geopandas.read_file(path_in, crs="EPSG:4326")

#merge population data onto our boundaries 
boundaries = boundaries.merge(data, left_on= 'gid_id' , right_on='gid_id')

#define dummy value bins and then labels for each one
bins = [-1e6, 1000, 10000, 100000, 500000, 1000000, 5000000, 10000000, 1e12]
labels = ['<1k','1k-10k','10k-100k', '100k-500k','500k-1mil','1mil-5mil','5mil-10mil','>10mil']

#create a new variable with our dummy bin labels
boundaries['bin'] = pandas.cut(
    boundaries['pop_est'],
    bins=bins,
    labels=labels
)

#open a new seaborn figure
sns.set(font_scale=1)

dimensions = (20,10)
fig, ax = plt.subplots(1, 1, figsize=dimensions)
fig.set_facecolor('gainsboro')

#now plot our data using pandas plot

base = boundaries.plot(column='bin', ax=ax, cmap='viridis', linewidth=0, #inferno_r
    legend=True, antialiased=False)

cx.add_basemap(ax) #add the map baselayer

#allocate a plot title 
n = len(boundaries)
name = 'Population At Risk To Coastal Flooding  (n={})'.format(n)
fig.suptitle(name)

#specify where to write our .png file to
path = os.path.join('data', 'processed', 'figures', 'global_flood_risk.png')
fig.savefig(path)
plt.close(fig)
    