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

def intersect_hazard_pop(country, region):
    """
    This function creates an intersect between the 
    coastal flood hazard area and population.
    
    """
    #assigning variables
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')

    #load in population by region .shp file
    filename_pop = '{}'.format(gid_id) #each regional file is named using the gid id
    path_pop = os.path.join(BASE_PATH, 'processed', iso3 , 'population', filename_pop)
    gdf_pop =  gpd.read_file(path_pop, crs="EPSG:4326")
    gdf_pop = gdf_pop.to_crs('epsg:3857')
    
    for region in region_dict:

    #load in hazard .shp file
        filename_hazard = '{}.shp'.format(gid_id)
        path_hazard = os.path.join(BASE_PATH, 'processed', iso3 , 'hazards', 
                                'inuncoast', gid_id, filename_hazard)
        if not os.path.exists(path_hazard):
            continue
        gdf_hazard = gpd.read_file(path_hazard, crs="EPSG:4326")
        gdf_hazard = gdf_hazard.to_crs('epsg:3857')
        
        gdf_affected = gpd.overlay(gdf_pop, gdf_hazard, how='intersection')
        if len(gdf_affected) == 0:
            continue
       
        # area to 1 km
        gdf_affected['area_km2'] = gdf_affected['geometry'].area/ 1e6
        gdf_affected['pop_est'] = gdf_affected['value_1']* gdf_affected['area_km2']

        #now we write out path at the regional level
        filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_out = os.path.join(BASE_PATH, 'processed', iso3 , 'intersect', 'hazard_pop')

        path_out = os.path.join(folder_out, filename_out)
        if not os.path.exists(path_out):
            os.makedirs(path_out)
        gdf_affected.to_file(path_out, crs='epsg:4326')

    return


if __name__ == "__main__":

    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')
    countries = countries.to_dict('records')

    for country in countries:

        if not country['iso3'] =='BGD':
            continue
        
        # #define our country-specific parameters, including gid information
        iso3 = country['iso3']
        gid_region = country['gid_region']
        gid_level = 'GID_{}'.format(gid_region)
        
        #loading in coastal lookup list
        filename = 'coastal_lookup.csv'
        folder = os.path.join(BASE_PATH, 'processed', iso3, 'coastal')
        path_coast= os.path.join(folder, filename)
        coastal = pandas.read_csv(path_coast)
        coast_list = coastal['gid_id'].values. tolist()

        #set the filename depending our preferred regional level
        filename = "gadm36_{}.shp".format(gid_region)
        folder = os.path.join('data','processed', iso3, 'gid_region')
        
        #then load in our regions as a geodataframe
        path_regions = os.path.join(folder, filename)
        regions = gpd.read_file(path_regions, crs='epsg:4326')#[:2]
        region_dict = regions.to_dict('records')
        
        for region in region_dict:
            if not region[gid_level] in coast_list:
                continue

            intersect_hazard_pop(country, region)
