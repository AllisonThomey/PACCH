#making user defined functions for processing hazard 
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

def process_national_hazard(country):
    """
    This function creates a national hazard.shp file

    """
    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')
    countries = countries.to_dict('records')

    for country in countries:
        filename = 'inuncoast_rcp8p5_wtsub_2080_rp1000_0.shp'
        folder= os.path.join(BASE_PATH,'processed',iso3, 'hazards', 'inuncoast', 'national')
        path_out = os.path.join(folder, filename)
        if not os.path.exists(path_out):

            #load in boundary of interest
            filename = 'national_outline.shp'
            folder = os.path.join(BASE_PATH, 'processed', iso3, 'national', filename)
                
            #then load in our country as a geodataframe
            path_in = os.path.join(folder, filename)
            country_shp = gpd.read_file(path_in, crs='epsg:4326')

            #loading in coastal flood hazard .tiff
            filename = 'inuncoast_rcp8p5_wtsub_2080_rp1000_0.tif'
            path_hazard = os.path.join(BASE_PATH,'raw','flood_hazard', filename)
            hazard = rasterio.open(path_hazard, 'r+')
            hazard.nodata = 255                       #set the no data value
            hazard.crs.from_epsg(4326)  

            #load in boundary of interest
            filename = 'national_outline.shp'
            folder = os.path.join(BASE_PATH, 'processed', iso3, 'national', filename)
                
            #then load in our country as a geodataframe
            path_in = os.path.join(folder, filename)
            country_shp = gpd.read_file(path_in, crs='epsg:4326')
            
            geo = gpd.GeoDataFrame(gpd.GeoSeries(country_shp.geometry))
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
            
            #now we write out at the national level
            filename= 'inuncoast_rcp8p5_wtsub_2080_rp1000_0.tif' 
            folder= os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', 'national')
            if not os.path.exists(folder):
                os.makedirs(folder)
            path_hazard = os.path.join(folder, filename)

            with rasterio.open(path_hazard, "w", **out_meta) as dest:
                dest.write(out_img)
            #done cutting out .tif to boundary file
        
            with rasterio.open(path_hazard) as src:

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
            if len(output) == 0:
                continue
            output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')
            output.to_file(path_out, driver='ESRI Shapefile')

    return


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


if __name__ == "__main__":

    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')
    countries = countries.to_dict('records')

    for country in countries:
        if not country['iso3'] == "BGD":
            continue

        # #define our country-specific parameters, including gid information
        iso3 = country['iso3']
        gid_region = country['gid_region']
        gid_level = 'GID_{}'.format(gid_region)
        
        #loading in coastal lookup list
        filename = 'coastal_lookup.csv'
        folder = os.path.join(BASE_PATH, 'processed', iso3, 'coastal')
        path_coast= os.path.join(folder, filename)
        if not os.path.exists(path_coast):
            continue
        coastal = pandas.read_csv(path_coast)
        coast_list = coastal['gid_id'].values. tolist()

        #set the filename depending our preferred regional level
        filename = "gadm36_{}.shp".format(gid_region)
        folder = os.path.join('data','processed', iso3, 'gid_region')
        
        #then load in our regions as a geodataframe
        path_regions = os.path.join(folder, filename)
        regions = gpd.read_file(path_regions, crs='epsg:4326')#[:2]

        region_dict = regions.to_dict('records')

        print("Working on process_national_hazard for {}".format(iso3))
        process_national_hazard(country)
        
        print("Working on process_regional_hazard")
        
        for region in region_dict:
            if not region[gid_level] in coast_list:
                continue
            process_regional_hazard(country, region)

