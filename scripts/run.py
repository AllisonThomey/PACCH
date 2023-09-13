#this script is for running all functions
#preprocess script should be run first
import os
import json
import rasterio
from rasterio.mask import mask
import pandas
import geopandas as gpd
import configparser

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def process_regional_hazard(country, region):
    """
    This function creates a regional hazard .tif

    """
    #assigning variables
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

    #prefered GID level
    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')
    
    for region in region_dict:

        #loading in hazard .shp
        filename = 'inuncoast_rcp8p5_wtsub_2080_rp1000_0.shp' 
        path_hazard = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', 'national', filename)
        if not os.path.exists(path_hazard):
            continue
        gdf_hazard = gpd.read_file(path_hazard, crs="EPSG:4326")
        #now we write out at the regional level
        filename_out = '{}.shp'.format(gid_id)
        folder_out = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', gid_id)
        path_out = os.path.join(folder_out, filename_out)
        if not os.path.exists(path_out):
            gdf_hazard_int = gpd.overlay(gdf_hazard, gdf_region, how='intersection')
            if len(gdf_hazard_int) == 0:
                continue
            os.makedirs(path_out)
            gdf_hazard_int.to_file(path_out, crs='epsg:4326')

    return

def process_regional_population(country, region):
    """
    This function creates a regional population .shp
    
    """
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')
    
    for region in region_dict:

        filename_haz = '{}.shp'.format(gid_id) # if the region doesn't have a hazard skip it
        folder_haz = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', gid_id)
        path_haz = os.path.join(folder_haz, filename_haz)
        if not os.path.exists(path_haz):
            continue

        filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_out = os.path.join('data', 'processed', iso3 , 'population')
        path_out = os.path.join(folder_out, filename_out)

        if not os.path.exists(path_out):
            #loading in national population file
            filename = 'ppp_2020_1km_Aggregated.shp' #each regional file is named using the gid id
            folder= os.path.join('data', 'processed', iso3 , 'population', 'national')
            path_pop = os.path.join(folder, filename)
            gdf_pop =  gpd.read_file(path_pop, crs="EPSG:4326")
            
            #prefered GID level
            filename = "gadm36_{}.shp".format(gid_region)
            path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
            gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
            gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
        
            gdf_pop = gpd.overlay(gdf_pop, gdf_region, how='intersection')
            if len(gdf_pop) == 0:
                continue
            os.makedirs(path_out)
            gdf_pop.to_file(path_out, crs='epsg:4326')
    return

def process_regional_rwi(country, region):
    """
    creates relative wealth estimates .shp file by region

    """
    iso3 = country['iso3']                 
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

    #loading in gid level shape file
    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')

    for region in region_dict:

    #loading in rwi info
        filename = '{}_relative_wealth_index.shp'.format(iso3) #each regional file is named using the gid id
        folder= os.path.join(BASE_PATH, 'processed', iso3 , 'rwi', 'national')
        path_rwi= os.path.join(folder, filename)
        if not os.path.exists(path_rwi):
            continue
        gdf_rwi = gpd.read_file(path_rwi, crs="EPSG:4326")

        filename = '{}.shp'.format(gid_id)
        folder_out = os.path.join(BASE_PATH, 'processed', iso3, 'rwi', 'regions' )
        path_out = os.path.join(folder_out, filename)
        if not os.path.exists(path_out):

            gdf_rwi_int = gpd.overlay(gdf_rwi, gdf_region, how='intersection')
            if len(gdf_rwi_int) == 0:
                continue
            os.makedirs(path_out)   

            gdf_rwi_int.to_file(path_out, crs="EPSG:4326")

    return

#intersect population and hazard
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

    for region in region_dict:

        #load in population by region .shp file
        filename_pop = '{}'.format(gid_id) #each regional file is named using the gid id
        path_pop = os.path.join(BASE_PATH, 'processed', iso3 , 'population', filename_pop)
        if not os.path.exists(path_pop):
            continue
        gdf_pop =  gpd.read_file(path_pop, crs="EPSG:4326")

    #load in hazard .shp file
        filename_hazard = '{}.shp'.format(gid_id)
        path_hazard = os.path.join(BASE_PATH, 'processed', iso3 , 'hazards', 
                                'inuncoast', gid_id, filename_hazard)
        if not os.path.exists(path_hazard):
            continue
        gdf_hazard = gpd.read_file(path_hazard, crs="EPSG:4326")
    
        filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_out = os.path.join(BASE_PATH, 'processed', iso3 , 'intersect', 'hazard_pop')
        path_out = os.path.join(folder_out, filename_out)
        # if not os.path.exists(path_out):
        #     os.makedirs(path_out)
        gdf_affected = gpd.overlay(gdf_pop, gdf_hazard, how='intersection')
        if len(gdf_affected) == 0:
            continue

        gdf_affected = gdf_affected.to_crs('epsg:3857')

        # area to 1 km
        gdf_affected['area_km2'] = gdf_affected['geometry'].area / 1e6
        gdf_affected['pop_est'] = gdf_affected['value_1']* gdf_affected['area_km2']
    
        gdf_affected = gdf_affected.to_crs('epsg:4326')

        # now we write out path at the regional level
        filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_out = os.path.join(BASE_PATH, 'processed', iso3 , 'intersect', 'hazard_pop')

        path_out = os.path.join(folder_out, filename_out)
        if not os.path.exists(path_out):
            os.makedirs(path_out)
        gdf_affected.to_file(path_out, crs='epsg:4326')

    return

#intersect vulnerable population and rwi
def intersect_rwi_pop(country, region):
    """
    This function creates an intersect between the 
    relative wealth index and vulnerable population.
    
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

    for region in region_dict:
        #load in hazard .shp file
        filename = '{}.shp'.format(gid_id)
        path_rwi = os.path.join(BASE_PATH, 'processed', iso3, 'rwi', 'regions', filename )
        if not os.path.exists(path_rwi):
            continue
        gdf_rwi = gpd.read_file(path_rwi, crs="EPSG:4326")
        gdf_rwi = gdf_rwi.to_crs('epsg:3857')
        
        filename = '{}'.format(gid_id) #each regional file is named using the gid id
        path_pop= os.path.join(BASE_PATH, 'processed', iso3 , 'intersect', 'hazard_pop', filename)
        if not os.path.exists(path_pop):
            continue
        gdf_pop =  gpd.read_file(path_pop, crs="EPSG:4326")
        gdf_pop = gdf_pop.to_crs('epsg:3857')

        filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_out = os.path.join(BASE_PATH, 'processed', iso3 , 'intersect', 'rwi_pop_hazard')

        path_out = os.path.join(folder_out, filename_out)
        if not os.path.exists(path_out):
            os.makedirs(path_out)
            gdf_pop_rwi = gpd.overlay(gdf_rwi, gdf_pop, how='intersection')
            if len(gdf_pop_rwi) == 0:
                continue
            gdf_pop_rwi = gdf_pop_rwi.rename(columns = {'value_1':'population'})
            gdf_pop_rwi=gdf_pop_rwi.rename(columns = {'value_2':'flood_depth'})
            gdf_pop_rwi.to_file(path_out, crs='epsg:4326')

    return


if __name__ == "__main__":

    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')
    countries = countries.to_dict('records')

    for country in countries:

        if country['Exclude'] == 1:
            continue
        if country['income_group'] == 'HIC':
            continue
        # if not country['iso3'] == 'BGD':
        #     continue

        iso3 = country['iso3']
        gid_region = country['gid_region']
        gid_level = 'GID_{}'.format(gid_region)

        #coastal look up load in
        filename = 'coastal_lookup.csv'
        folder = os.path.join(BASE_PATH, 'processed', iso3, 'coastal')
        path_coast= os.path.join(folder, filename)
        if not os.path.exists(path_coast):
            continue
        coastal = pandas.read_csv(path_coast)
        coast_list = coastal['gid_id'].values.tolist()

        #set the filename depending our preferred regional level
        filename = "gadm36_{}.shp".format(gid_region)
        folder = os.path.join('data','processed', iso3, 'gid_region')
        
        #then load in our regions as a geodataframe
        path_regions = os.path.join(folder, filename)
        regions = gpd.read_file(path_regions, crs='epsg:4326')#[:2]
        region_dict = regions.to_dict('records')

        print("Working on {}".format(iso3))
        # process_national_population(country)
        # process_national_hazard(country)
        # process_rwi_geometry(country)

        for region in region_dict:

            if not region[gid_level] in coast_list:
                continue

            print("working on {}".format(region[gid_level]))
            process_regional_hazard(country, region)
            process_regional_population(country, region)
            process_regional_rwi(country, region)
            intersect_hazard_pop(country, region)
            intersect_rwi_pop(country, region)
