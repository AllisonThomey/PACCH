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

#population
def process_national_population(country):
    """
    This function creates a national population .shp

    """
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)

    filename = 'ppp_2020_1km_Aggregated.shp'
    folder= os.path.join('data','processed',iso3, 'population', 'national')
    path_out = os.path.join(folder, filename)
    if not os.path.exists(path_out):

        #let's load in our pop layer
        filename = 'ppp_2020_1km_Aggregated.tif'
        path_pop = os.path.join(BASE_PATH,'raw','worldpop', filename)
        hazard = rasterio.open(path_pop, 'r+')
        hazard.nodata = 255                       #set the no data value
        hazard.crs.from_epsg(4326)                #set the crs
            
        #load in boundary of interest
        filename = 'national_outline.shp'
        folder = os.path.join(BASE_PATH, 'processed', iso3, 'national', filename)
            
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
        folder_out = os.path.join(BASE_PATH, 'processed', iso3 , 'population', 'national')
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)
        path_pop = os.path.join(folder_out, filename_out)

        with rasterio.open(path_pop, "w", **out_meta) as dest:
            dest.write(out_img)
        #done cutting out .tif to boundary file

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

    filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
    folder_out = os.path.join('data', 'processed', iso3 , 'v2_population')
    path_out = os.path.join(folder_out, filename_out)

    if not os.path.exists(path_out):
        os.makedirs(path_out)
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
        gdf_pop.to_file(path_out, crs='epsg:4326')

    return

#hazards
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

def process_regional_hazard (country, region):
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


#rwi
def process_rwi_geometry(country):
    """
    Adds geometry column into .csv data to make use of latitude and longitude easier
    """
    #assigning variables
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)

    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')
    countries = countries.to_dict('records')

    for country in countries:

        #path in for rwi files
        filename = '{}_relative_wealth_index.csv'.format(iso3)
        path_rwi = os.path.join(BASE_PATH,'raw','rwi', filename)
        if not os.path.exists(path_rwi):
            continue 
        wealth = gpd.read_file(path_rwi, encoding='latin-1')

        #making long lat points into geometry column
        gdf = gpd.GeoDataFrame(
            wealth, geometry=gpd.points_from_xy(wealth.longitude, wealth.latitude), crs="EPSG:4326"
        )  

        #setting path out
        filename_out = '{}_relative_wealth_index.shp'.format(iso3) #each regional file is named using the gid id
        folder_out = os.path.join(BASE_PATH, 'processed', iso3 , 'rwi', 'national')
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)
        path_out = os.path.join(folder_out, filename_out)

        #saving new .csv to location
        gdf.to_file(path_out,crs="EPSG:4326")
    
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
            # filename = '{}.shp'.format(gid_id)
            # folder_out = os.path.join(BASE_PATH, 'processed', iso3, 'rwi', 'regions' )
            # if not os.path.exists(folder_out):
                # os.makedirs(folder_out)
            # path_out = os.path.join(folder_out, filename)
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

    #load in population by region .shp file
    filename_pop = '{}'.format(gid_id) #each regional file is named using the gid id
    path_pop = os.path.join(BASE_PATH, 'processed', iso3 , 'v2_population', filename_pop)
    gdf_pop =  gpd.read_file(path_pop, crs="EPSG:4326")

    for region in region_dict:

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
        if not os.path.exists(path_out):
            os.makedirs(path_out)
            gdf_affected = gpd.overlay(gdf_pop, gdf_hazard, how='intersection')
            if len(gdf_affected) == 0:
                continue

            # area to 1 km
            gdf_affected['area_km2'] = gdf_affected['geometry'].area/ 1e6
            gdf_affected['pop_est'] = gdf_affected['value_1']* gdf_affected['area_km2']
        
            gdf_affected = gdf_affected.to_crs('epsg:4326')

            #now we write out path at the regional level
            # filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
            # folder_out = os.path.join(BASE_PATH, 'processed', iso3 , 'intersect', 'hazard_pop')

            # path_out = os.path.join(folder_out, filename_out)
            # if not os.path.exists(path_out):
            #     os.makedirs(path_out)
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
            #now we write out path at the regional level
            # filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
            # folder_out = os.path.join(BASE_PATH, 'processed', iso3 , 'intersect', 'rwi_pop_hazard')

            # path_out = os.path.join(folder_out, filename_out)
            # if not os.path.exists(path_out):
            # os.makedirs(path_out)
            gdf_pop_rwi.to_file(path_out, crs='epsg:4326')

    return


if __name__ == "__main__":
    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')
    countries = countries.to_dict('records')

    for country in countries:
        if country['Exclude'] == 1:
            continue
       
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
        coast_list = coastal['gid_id'].values. tolist()

        #set the filename depending our preferred regional level
        filename = "gadm36_{}.shp".format(gid_region)
        folder = os.path.join('data','processed', iso3, 'gid_region')
        
        #then load in our regions as a geodataframe
        path_regions = os.path.join(folder, filename)
        regions = gpd.read_file(path_regions, crs='epsg:4326')#[:2]
        region_dict = regions.to_dict('records')

        print("Working on {}".format(iso3))
        process_national_population(country)
        print('finished population')
        process_national_hazard(country)
        print('finished hazard')
        # process_rwi_geometry(country)
        print('finished rwi')

        for region in region_dict:
            if not region[gid_level] in coast_list:
                continue
            print("working on {}".format(region[gid_level]))
            process_regional_population(country, region)
            print('finished population')
            process_regional_hazard (country, region)
            print('finished hazard')
            # process_regional_rwi(country, region)
            print('finished rwi')
            intersect_hazard_pop(country, region)
            # intersect_rwi_pop(country, region)
