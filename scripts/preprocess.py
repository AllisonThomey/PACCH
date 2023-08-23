#file that makes national outline and gid region outlines
import os
import json
import pandas
import geopandas
#removing small shapes and cutting out boundray by GID region
from shapely.geometry import MultiPolygon
import rasterio
from rasterio.mask import mask
import configparser

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

def remove_small_shapes(x):
    """
    Remove small multipolygon shapes.

    Parameters
    ---------
    x : polygon
        Feature to simplify.

    Returns
    -------
    MultiPolygon : MultiPolygon
        Shapely MultiPolygon geometry without tiny shapes.

    """
    if x.geometry.type == 'Polygon':
        return x.geometry

    elif x.geometry.type == 'MultiPolygon':

        area1 = 0.003
        area2 = 50

        if x.geometry.area < area1:
            return x.geometry

        if x['GID_0'] in ['CHL','IDN', 'RUS', 'GRL','CAN','USA']:
            threshold = 0.01
        elif x.geometry.area > area2:
            threshold = 0.1
        else:
            threshold = 0.001

        new_geom = []
        for y in list(x['geometry'].geoms):
            if y.area > threshold:
                new_geom.append(y)

        return MultiPolygon(new_geom)


def process_national_boundary(country):
    """
    This function creates a national outline .shp for a 
    country with small shapes removed and simplified

    """
    #load in GID_0 gadm layer
    filename = "gadm36_0.shp"
    folder = os.path.join('data', 'raw', 'gadm36_levels_shp')
    path_in= os.path.join(folder, filename)
    boundaries = geopandas.read_file(path_in, crs="epsg:4326")

    iso3 = country['iso3']
    country_boundaries = boundaries[boundaries['GID_0'] == country['iso3']]
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)

    #extract GID_0 for the country of interest, e.g., using the iso3 code
    regions_folder_path = os.path.join('data', 'processed', iso3, 'processed_regions')
    if not os.path.exists(regions_folder_path):
        os.makedirs(regions_folder_path)
    #do any required processing, e.g., simplification or remove small areas
    country_boundaries["geometry"] = country_boundaries.geometry.simplify(
        tolerance=0.01, preserve_topology=True)
    
    #remove small shapes
    country_boundaries['geometry'] = country_boundaries.apply(
        remove_small_shapes, axis=1)
    #export the national outline to a .shp
    filename = 'national_outline.shp'
    path_out = os.path.join('data', 'processed', iso3, 'national', filename)
    if not os.path.exists(path_out):
        os.makedirs(path_out)
    country_boundaries.to_file(path_out, crs='epsg:4326')
    
    return


def process_regional_boundary(country):
    """
    This function creates a regional composite outline .shp 
    for a country with small shapes removed and simplified.

    Regional level is based on best admistrative level for 
    project analysis level.

    """
    iso3 = country["iso3"]
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)

    #prefered gid level
    filename = 'gadm36_{}.shp'.format(country['gid_region'])
    path_in = os.path.join('data', 'raw', 'gadm36_levels_shp', filename)
    boundaries = geopandas.read_file(path_in)
    country_boundaries = boundaries[boundaries['GID_0'] == country['iso3']]

    #set the filename depending our preferred regional level
    filename = "gadm36_{}.shp".format(gid_region)
    regions_folder_path = os.path.join('data', 'processed', iso3, 'processed_regions')
    if not os.path.exists(regions_folder_path):
        os.makedirs(regions_folder_path)

    #this is how we simplify the geometries
    country_boundaries["geometry"] = country_boundaries.geometry.simplify(
        tolerance=0.01, preserve_topology=True)
        
    #remove small shapes
    country_boundaries['geometry'] = country_boundaries.apply(
        remove_small_shapes, axis=1)
                                            
    #set the filename depending our preferred regional level
    filename = "gadm36_{}.shp".format(gid_region)

    #saving gid region boundaries
    path_out = os.path.join('data', 'processed', iso3,'gid_region', filename)
    if not os.path.exists(path_out):
        os.makedirs(path_out)
    country_boundaries.to_file(path_out, crs='epsg:4326')

    return


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
        country_pop = geopandas.read_file(path_in, crs='epsg:4326')

        geo = geopandas.GeoDataFrame(geopandas.GeoSeries(country_pop.geometry))
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

        output = geopandas.GeoDataFrame.from_features(output, crs='epsg:4326')
        output.to_file(path_out, driver='ESRI Shapefile')

    return  


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
            country_shp = geopandas.read_file(path_in, crs='epsg:4326')

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
            country_shp = geopandas.read_file(path_in, crs='epsg:4326')
            
            geo = geopandas.GeoDataFrame(geopandas.GeoSeries(country_shp.geometry))
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
            output = geopandas.GeoDataFrame.from_features(output, crs='epsg:4326')
            output.to_file(path_out, driver='ESRI Shapefile')

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
    gdf_region = geopandas.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')
    
    for region in region_dict:

        filename_haz = '{}.shp'.format(gid_id) # if the region doesn't have a hazard skip it
        folder_haz = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', gid_id)
        path_haz = os.path.join(folder_haz, filename_haz)
        if not os.path.exists(path_haz):
            continue

        filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_out = os.path.join('data', 'processed', iso3 , 'v2_population')
        path_out = os.path.join(folder_out, filename_out)

        if not os.path.exists(path_out):
            # os.makedirs(path_out)
            #loading in national population file
            filename = 'ppp_2020_1km_Aggregated.shp' #each regional file is named using the gid id
            folder= os.path.join('data', 'processed', iso3 , 'population', 'national')
            path_pop = os.path.join(folder, filename)
            # if not os.path.exists(path_pop):
            #     continue
            gdf_pop =  geopandas.read_file(path_pop, crs="EPSG:4326")
            
            #prefered GID level
            filename = "gadm36_{}.shp".format(gid_region)
            path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
            gdf_region = geopandas.read_file(path_region, crs="EPSG:4326")
            gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
        
            gdf_pop = geopandas.overlay(gdf_pop, gdf_region, how='intersection')
            if len(gdf_pop) == 0:
                continue
            os.makedirs(path_out)
            gdf_pop.to_file(path_out, crs='epsg:4326')
    return


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
        wealth = geopandas.read_file(path_rwi, encoding='latin-1')

        #making long lat points into geometry column
        gdf = geopandas.GeoDataFrame(
            wealth, geometry=geopandas.points_from_xy(wealth.longitude, wealth.latitude), crs="EPSG:4326"
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


if __name__ == "__main__":

    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')

    output = []

    for idx, country in countries.iterrows():

        iso3 = country['iso3']
       
        # if not country['iso3'] == 'BGD':
        #     continue
    
        if country['Exclude'] == 1:
            continue

        print("Working on {}".format(iso3))
        process_national_boundary(country)

        print("Working on process_regional_boundary")
        process_regional_boundary(country)

        print("Working on process_national_population")
        process_national_population(country)

        print("Working on process_national_hazard")
        process_national_hazard(country)

        print("Working on process_rwi_geometry")
        process_rwi_geometry(country)



    #     gid_region = country['gid_region']
    #     gid_level = 'GID_{}'.format(gid_region)
        
    #     #then load in our regions as a geodataframe
    #     filename = "gadm36_{}.shp".format(gid_region)
    #     path_region = os.path.join('data', 'processed', iso3, 'gid_region', filename)
    #     gdf_region = geopandas.read_file(path_region, crs="EPSG:4326")
    #     gdf_region = gdf_region.to_crs('epsg:3857')
    #     region_dict = gdf_region.to_dict('records')


    #     filename = 'coastal_lookup.csv'
    #     folder = os.path.join(BASE_PATH, 'processed', iso3, 'coastal')
    #     path_coast= os.path.join(folder, filename)
    #     if not os.path.exists(path_coast):
    #         continue
    #     coastal = pandas.read_csv(path_coast)
    #     coast_list = coastal['gid_id'].values. tolist()

    #     for region in region_dict:
    #         if not region[gid_level] in coast_list:
    #             continue

    #         output.append({
    #             'geometry': region['geometry'],
    #             'properties': {
    #             'gid_id': region[gid_level]
    #             }
    #         })

    # output = geopandas.GeoDataFrame.from_features(output, crs='epsg:4326') 

    # filename = 'global_outline.shp'
    # folder_out = os.path.join('data', 'processed', 'Global')
    # if not os.path.exists(folder_out):
    #     os.mkdir(folder_out)
    # path_out = os.path.join(folder_out, filename)
    # output.to_file(path_out, crs='epsg:4326')

