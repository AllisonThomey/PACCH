#working on intersecting the coastal flood hazard 
#with the population layer
import os
from rasterio.mask import mask
import pandas
import geopandas as gpd
import configparser

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#create user defined function for coastal flood and population intersection

def intersect_rwi_pop(country, region):
    """
    This function creates an intersect between the 
    relative wealth index and population.
    
    """
    #assigning variables
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]


    #load in population by region .shp file
    filename_pop = '{}'.format(gid_id) #each regional file is named using the gid id
    path_pop = os.path.join(BASE_PATH, 'processed', iso3 , 'population', filename_pop)
    gdf_pop =  gpd.read_file(path_pop, crs="EPSG:4326")


    #load in hazard .shp file
    filename = '{}.shp'.format(gid_id)
    path_rwi = os.path.join(BASE_PATH, 'processed', iso3, 'rwi', 'regions', filename )
    gdf_rwi = gpd.read_file(path_rwi, crs="EPSG:4326")


    gdf_pop_rwi = gpd.overlay(gdf_rwi, gdf_pop, how='intersection')

    #now we write out path at the regional level
    filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
    folder_out = os.path.join(BASE_PATH, 'processed', iso3 , 'intersect', 'rwi_pop')

    path_out = os.path.join(folder_out, filename_out)
    if not os.path.exists(path_out):
        os.makedirs(path_out)
    gdf_pop_rwi.to_file(path_out, crs='epsg:4326')



    return



if __name__ == "__main__":

    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')

    for idx, country in countries.iterrows():

 
        if not country['iso3'] =='BGD':
            continue
        
        # #define our country-specific parameters, including gid information
        iso3 = country['iso3']
        gid_region = country['gid_region']
        gid_level = 'GID_{}'.format(gid_region)
        

        #set the filename depending our preferred regional level
        filename = "gadm36_{}.shp".format(gid_region)
        folder = os.path.join('data','processed', iso3, 'gid_region')
        
        #then load in our regions as a geodataframe
        path_regions = os.path.join(folder, filename)
        regions = gpd.read_file(path_regions, crs='epsg:4326')#[:2]
        
        
        for idx, region in regions.iterrows():

            if not region[gid_level] == 'BGD.1.5_1':
                continue
            
            print("working on {}".format(region[gid_level]))
            intersect_rwi_pop(country, region)