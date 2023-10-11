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

    #do any required processing, e.g., simplification or remove small areas
    country_boundaries["geometry"] = country_boundaries.geometry.simplify(
        tolerance=0.01, preserve_topology=True)
    
    #remove small shapes
    country_boundaries['geometry'] = country_boundaries.apply(
        remove_small_shapes, axis=1)
    #export the national outline to a .shp
    filename = 'national_outline.shp'
    folder_out = os.path.join('data', 'processed', iso3)
    path_out = os.path.join(folder_out, filename)
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

    #saving gid region boundaries
    folder_out = os.path.join('data', 'processed', iso3, 'regions')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    filename = 'gadm36_{}.shp'.format(country['gid_region'])
    path_out = os.path.join(folder_out, filename)

    #prefered gid level
    path_in = os.path.join('data', 'raw', 'gadm36_levels_shp', filename)
    boundaries = geopandas.read_file(path_in)
    country_boundaries = boundaries[boundaries['GID_0'] == country['iso3']]

    #this is how we simplify the geometries
    country_boundaries["geometry"] = country_boundaries.geometry.simplify(
        tolerance=0.01, preserve_topology=True)
        
    #remove small shapes
    country_boundaries['geometry'] = country_boundaries.apply(
        remove_small_shapes, axis=1)
                                            
    #set the filename depending our preferred regional level
    filename = "gadm36_{}.shp".format(gid_region)

    country_boundaries.to_file(path_out, crs='epsg:4326')

    return


def process_settlement_layer(country):
    """
    Clip the settlement layer to the chosen country boundary and place in
    desired country folder.

    Parameters
    ----------
    country : string
        Three digit ISO country code.

    """
    iso3 = country['iso3']
    # regional_level = country['regional_level']

    filename = 'ppp_2020_1km_Aggregated.tif'
    path_pop = os.path.join(BASE_PATH,'raw','worldpop', filename)

    settlements = rasterio.open(path_pop, 'r+')
    settlements.nodata = 255
    settlements.crs = {"init": "epsg:4326"}

    iso3 = country['iso3']
    path_country = os.path.join(BASE_PATH,'processed', iso3, 
        'national_outline.shp')

    if os.path.exists(path_country):
        country = geopandas.read_file(path_country)
    else:
        print('Must generate national_outline.shp first' )

    folder_country = os.path.join(BASE_PATH,'processed', iso3)
    shape_path = os.path.join(folder_country, 'settlements.tif')

    if os.path.exists(shape_path):
        return print('Completed settlement layer processing')

    print('----')
    print('Working on {}'.format(iso3))

    geo = geopandas.GeoDataFrame({'geometry': country['geometry']})

    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(settlements, coords, crop=True)

    out_meta = settlements.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})

    with rasterio.open(shape_path, "w", **out_meta) as dest:
            dest.write(out_img)

    return print('Completed processing of settlement layer')


def process_regional_settlement_layer(country, region_dict):
    """
    Clip the settlement layer to the chosen country boundary and place in
    desired country folder.

    Parameters
    ----------
    country : string
        Three digit ISO country code.

    """
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)

    filename = 'settlements.tif'
    path_pop = os.path.join(BASE_PATH, 'processed', iso3, filename)
    settlements = rasterio.open(path_pop, 'r+')
    settlements.nodata = 255
    settlements.crs = {"init": "epsg:4326"}

    for region in region_dict:

        folder_country = os.path.join(BASE_PATH,'processed', iso3, 'regional_settlements')
        if not os.path.exists(folder_country):
            os.makedirs(folder_country)
        shape_path = os.path.join(folder_country, '{}.tif'.format(region[gid_level]))

        if os.path.exists(shape_path):
            return print('Completed settlement layer processing')

        print('----')
        print('Working on {}'.format(region[gid_level]))

        if region['geometry'].type == 'Polygon':
            geo = geopandas.GeoDataFrame({'geometry': region['geometry']}, index=[0], crs='epsg:4326')
        elif region['geometry'].type == 'MultiPolygon':
            geo = geopandas.GeoDataFrame({'geometry': region['geometry'].geoms}, crs='epsg:4326')

        coords = [json.loads(geo.to_json())['features'][0]['geometry']]

        out_img, out_transform = mask(settlements, coords, crop=True)

        out_meta = settlements.meta.copy()

        out_meta.update({"driver": "GTiff",
                        "height": out_img.shape[1],
                        "width": out_img.shape[2],
                        "transform": out_transform,
                        "crs": 'epsg:4326'})

        with rasterio.open(shape_path, "w", **out_meta) as dest:
                dest.write(out_img)

    return print('Completed processing of settlement layer')


def process_regional_population(country, region_dict):
    """
    This function creates a national population .shp

    """
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)

    for region in region_dict:

        folder_out = os.path.join('data', 'processed', iso3, 'population')
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)
        path_out = os.path.join(folder_out, region[gid_level] + '.shp')
        
        if os.path.exists(path_out):
            continue

        folder_country = os.path.join(BASE_PATH, 'processed', iso3, 'regional_settlements')
        path_pop = os.path.join(folder_country, '{}.tif'.format(region[gid_level]))

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

        if len(output) == 0:
            continue
        output = geopandas.GeoDataFrame.from_features(output, crs='epsg:4326')
        output.to_file(path_out, driver='ESRI Shapefile')

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


def process_national_hazard(country, haz_scene):
    """
    This function creates a national hazard.shp file

    """
    # path = os.path.join('data', 'countries.csv')
    # countries = pandas.read_csv(path, encoding='latin-1')
    # countries = countries.to_dict('records')
    iso3 = country['iso3']
    gid_region = country['gid_region']
    
    # for country in countries:
    for scene in haz_scene:

        filename = scene.format("shp")
        folder= os.path.join(BASE_PATH,'processed',iso3, 'hazards', 'inuncoast', 'national')
        path_out = os.path.join(folder, filename)
        if not os.path.exists(path_out):

            #loading in coastal flood hazard .tiff
            filename = scene.format('tif')
            path_hazard = os.path.join(BASE_PATH,'raw','flood_hazard', filename)
            # path_hazard = os.path.join(BASE_PATH,'..','..','data_raw', 'flood_hazard', filename)
            hazard = rasterio.open(path_hazard, 'r+')
            hazard.nodata = 255                       #set the no data value
            hazard.crs.from_epsg(4326)  

            #load in boundary of interest
            filename = 'national_outline.shp'
            folder = os.path.join(BASE_PATH, 'processed', iso3)
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
            filename= scene.format("tif")
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


    haz_scene = [
        "inuncoast_historical_wtsub_2080_rp0100_0.{}", 
        "inuncoast_historical_wtsub_2080_rp1000_0.{}", 
        "inuncoast_rcp4p5_wtsub_2080_rp0100_0.{}", 
        "inuncoast_rcp4p5_wtsub_2080_rp1000_0.{}", 
        "inuncoast_rcp8p5_wtsub_2080_rp0100_0.{}", 
        "inuncoast_rcp8p5_wtsub_2080_rp1000_0.{}"
        ]
    
    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')
    countries = countries.to_dict('records')

    output = []

    for country in countries:

        iso3 = country['iso3']
    
        if not iso3 == 'CHN':
            continue

        if country['Exclude'] == 1:
            continue

        if country['income_group'] == 'HIC':
            continue

        print("----Working on {}".format(iso3))

        print("Working on process_national_boundary")
        process_national_boundary(country)

        print("Working on process_regional_boundary")
        process_regional_boundary(country)

        print("Working on process_settlement_layer")
        process_settlement_layer(country)

        gid_region = country['gid_region']
        gid_level = 'GID_{}'.format(gid_region)
        filename = "gadm36_{}.shp".format(gid_region)
        path_region = os.path.join('data', 'processed', iso3, 'regions', filename)
        gdf_region = geopandas.read_file(path_region, crs="EPSG:4326")
        # gdf_region = gdf_region.to_crs('epsg:3857')
        region_dict = gdf_region.to_dict('records')

        print("Working on process_regional_settlement_layer")
        process_regional_settlement_layer(country, region_dict)

        print("Working on process_national_population")
        process_regional_population(country, region_dict)

        print("Working on process_national_hazard")
        process_national_hazard(country, haz_scene)

    #     print("Working on process_rwi_geometry")
    #     process_rwi_geometry(country)

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
    # folder_out = os.path.join('data', 'processed')
    # if not os.path.exists(folder_out):
    #     os.mkdir(folder_out)
    # path_out = os.path.join(folder_out, filename)
    # output.to_file(path_out, crs='epsg:4326')
