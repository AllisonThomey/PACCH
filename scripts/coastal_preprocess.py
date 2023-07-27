#making function to process coastal regions
import os
from rasterio.mask import mask
import pandas
import geopandas as gpd
import configparser
from tqdm import tqdm

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

path = os.path.join('data', 'countries.csv')
countries = pandas.read_csv(path, encoding='latin-1')
countries = countries.to_dict('records')

filename = 'coastal_buffer.shp'
folder_out = os.path.join(BASE_PATH, 'processed')
path_coastal = os.path.join(folder_out, filename)
if not os.path.exists(path_coastal):
    
    #loading in coastline file
    filename = 'GSHHS_c_L1.shp'
    path = os.path.join(BASE_PATH, 'raw', 'GSHHS_shp', 'c', filename)
    gdf_coastal = gpd.read_file(path, crs = "EPSG: 4326")
    gdf_coastal = gdf_coastal.to_crs('epsg:3857')

    gdf_coastal['geometry'] = gdf_coastal['geometry'].boundary

    gdf_coastal['geometry'] = gdf_coastal['geometry'].buffer(1e5)

    gdf_coastal.to_file(path_coastal)
else: 
    gdf_coastal = gpd.read_file(path_coastal, crs = 'epsg:3857')

coast_dict = gdf_coastal.to_dict("records")

for country in tqdm(countries):

    if country['Exclude'] == 1:
        continue
    
    iso3 = country["iso3"]
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)

    #loading in regions by GID level
    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region.to_crs('epsg:3857')
    region_dict = gdf_region.to_dict('records')
    
    my_shp = []
    my_csv = []
    # my_set = set()

    for region in region_dict:
        if region['geometry'] == None:
            continue
        for coast in coast_dict:

            if region['geometry'].intersects(coast['geometry']):

                    my_shp.append({
                        'geometry': region['geometry'],
                        'properties': {
                        'gid_id': region[gid_level],
                        'iso3': iso3
                        }
                    })
                    my_csv.append({
                        'gid_id': region[gid_level],
                        'iso3': iso3
                    })

    if len(my_shp) == 0:
        continue  

    ##shp files
    output = gpd.GeoDataFrame.from_features(my_shp)
    
    filename = 'coastal_regions.shp'
    folder_out = os.path.join(BASE_PATH, 'processed', iso3, 'coastal')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_out = os.path.join(folder_out, filename)
    output.to_file(path_out)
    
    # #csv files
    output = pandas.DataFrame(my_csv)
    
    filename = 'coastal_lookup.csv'
    folder_out = os.path.join(BASE_PATH, 'processed', iso3, 'coastal')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_out = os.path.join(folder_out, filename)
    output.to_csv(path_out, index= False) 
