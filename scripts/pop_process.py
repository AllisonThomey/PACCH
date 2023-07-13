#starting code base from 470 for populaiton processing
import os
import json
import rasterio
from rasterio.mask import mask
import pandas
import geopandas as gpd
import configparser
from tqdm import tqdm


CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def process_national_population(country):
    """
    This function creates a national population .shp

    """
    
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)

    #let's load in our pop layer
    filename = 'ppp_2020_1km_Aggregated.tif'
    path_pop = os.path.join('data','raw','worldpop', filename)
    hazard = rasterio.open(path_pop, 'r+')
    hazard.nodata = 255                       #set the no data value
    hazard.crs.from_epsg(4326)                #set the crs
        
    #load in boundary of interest
    filename = 'national_outline.shp'
    folder = os.path.join('data', 'processed', iso3, 'national', filename)
        
    #then load in our country as a geodataframe
    path_in = os.path.join(folder, filename)
    country_pop = gpd.read_file(path_in, crs='epsg:4326')

    geo = gpd.GeoDataFrame(gpd.GeoSeries(country_pop.geometry))
    #this line sets geometry for resulting geodataframe
    geo = geo.rename(columns={0:'geometry'}).set_geometry('geometry')
    #convert to json
    coords = [json.loads(geo.to_json())['features'][0]['geometry']] 
        
    #carry out the clip using our mask
    out_img, out_transform = mask(hazard, coords, crop=True)
    out_img, out_transform

    #update our metadata
    out_meta = hazard.meta.copy()
    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})

    #now we write out at the regional level
    filename_out = 'ppp_2020_1km_Aggregated.tif' #each regional file is named using the gid id
    folder_out = os.path.join('data', 'processed', iso3 , 'population', 'national')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_pop = os.path.join(folder_out, filename_out)

    with rasterio.open(path_pop, "w", **out_meta) as dest:
        dest.write(out_img)
    #done cutting out .tif to boundary file

    #set up file system for .shp
    filename = 'ppp_2020_1km_Aggregated.shp'
    folder= os.path.join('data','processed',iso3, 'population', 'national')
    path_out = os.path.join(folder, filename)
    if not os.path.exists(path_out):
        os.makedirs(path_out)

    with rasterio.open(path_pop) as src:

        affine = src.transform
        array = src.read(1)

        output = []

        for vec in rasterio.features.shapes(array):

            if vec[1] > 0 and not vec[1] == 255:

                coordinates = [i for i in vec[0]['coordinates'][0]]

                coords = []

                for i in coordinates:

                    x = i[0]
                    y = i[1]

                    x2, y2 = src.transform * (x, y)

                    coords.append((x2, y2))

                output.append({
                    'type': vec[0]['type'],
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [coords],
                    },
                    'properties': {
                        'value': vec[1],
                    }
                })

    output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')
    output.to_file(path_out, driver='ESRI Shapefile')
    
    return  


def process_regional_population(country, region):
    """
    This function creates a regional population .shp
    
    """
    #assigning variables
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

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

    #now we write out at the regional level
    filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
    folder_out = os.path.join('data', 'processed', iso3 , 'population')

    path_out = os.path.join(folder_out, filename_out)
    if not os.path.exists(path_out):
        os.makedirs(path_out)
    gdf_pop.to_file(path_out, crs='epsg:4326')

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
        
        print("Working on process_national_population")
        process_national_population(country)

        print("Working on process_regional_population")                
        for idx, region in regions.iterrows():
            if not region[gid_level] in coast_list:
                continue
            process_regional_population(country, region)
