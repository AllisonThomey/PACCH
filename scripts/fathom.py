import os
import json
import rasterio
from rasterio.mask import mask
import pandas
import geopandas 
import configparser

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

def process_national_hazard(country):
    """
This function creates a national hazard.shp file
    """
    # path = os.path.join('data', 'countries.csv')
    # countries = pandas.read_csv(path, encoding='latin-1')
    # countries = countries.to_dict('records')
    iso3 = country['iso3']
    gid_region = country['gid_region']

    # haz_scene = ["FU_1in5.{}", "FU_1in10.{}", "FU_1in20.{}", 
    #              "FU_1in50.{}", "FU_1in75.{}", "FU_1in100.{}", 
    #              "FU_1in200.{}", "FU_1in250.{}", "FU_1in500.{}", 
    #              "FU_1in1000.{}"]
    haz_scene = ["FU_1in1000(1).{}"]
    # for country in countries:
    for scene in haz_scene:

        filename = scene.format("shp")
        folder= os.path.join(BASE_PATH,'processed',iso3, 'fathom', 'BGD')
        path_out = os.path.join(folder, filename)
        if not os.path.exists(path_out):

            #loading in coastal flood hazard .tiff
            filename = scene.format('tif')
            # path_hazard = os.path.join(BASE_PATH,'raw','fathom', "Bangladesh", "fluvial_undefended", filename)
            path_hazard = os.path.join(BASE_PATH,'raw','fathom', filename)
            # print("{}".format(filename))
            hazard = rasterio.open(path_hazard, 'r+')
            hazard.nodata = 255                       #set the no data value
            hazard.crs.from_epsg(4326)
            #load in boundary of interest
            filename = 'national_outline.shp'
            folder = os.path.join(BASE_PATH, 'processed', iso3, 'national', filename)
            #then load in our country as a geodataframe
            path_in = os.path.join(folder, filename)
            country_shp = geopandas.read_file(path_in, crs='epsg:4326')
            (print("here1"))
            geo = geopandas.GeoDataFrame(geopandas.GeoSeries(country_shp.geometry))
            #this line sets geometry for resulting geodataframe
            geo = geo.rename(columns={0:'geometry'}).set_geometry('geometry')
            #convert to json
            coords = [json.loads(geo.to_json())['features'][0]['geometry']] 
            (print("here2"))    
            #carry out the clip using our mask
            out_img, out_transform = mask(hazard, coords, crop=True)
            out_img, out_transform
            (print("here2.5"))
            #update our metadata
            out_meta = hazard.meta.copy()
            out_meta.update({"driver": "GTiff",
                            "height": out_img.shape[1],
                            "width": out_img.shape[2],
                            "transform": out_transform,
                            "crs": 'epsg:4326'})
            (print("here3"))
            #now we write out at the national level
            filename= scene.format("tif")
            folder= os.path.join('data', 'processed', iso3, 'fathom', 'BGD')
            if not os.path.exists(folder):
                os.makedirs(folder)
            path_hazard = os.path.join(folder, filename)

            with rasterio.open(path_hazard, "w", **out_meta) as dest:
                dest.write(out_img)
            #done cutting out .tif to boundary file
            (print("here4"))
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
            (print("here5"))
            if len(output) == 0:
                continue
            output = geopandas.GeoDataFrame.from_features(output, crs='epsg:4326')
            output.to_file(path_out, driver='ESRI Shapefile')
    return

def process_regional_hazard(country, region, haz_scene):
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
    gdf_region = geopandas.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')
    haz_scene = ["FU_1in1000(1).{}"]
    
    # for region in region_dict:
    for scene in haz_scene:

        #now we write out at the regional level
        filename_out = scene.format("shp")
        folder_out = os.path.join('data', 'processed', iso3, 'fathom', gid_id)
        path_out = os.path.join(folder_out, filename_out)

        if os.path.exists(path_out):
            continue

        #loading in hazard .shp
        filename = scene.format("shp")
        folder= os.path.join(BASE_PATH,'processed',iso3, 'fathom', 'BGD')
        path_hazard = os.path.join(folder, filename)
        if not os.path.exists(path_hazard):
            continue
        gdf_hazard = geopandas.read_file(path_hazard, crs="EPSG:4326")
        gdf_hazard_int = geopandas.overlay(gdf_hazard, gdf_region, how='intersection')
        if len(gdf_hazard_int) == 0:
            continue
        os.makedirs(path_out)
        gdf_hazard_int.to_file(path_out, crs='epsg:4326')

    return



if __name__ == "__main__":
    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')
    countries = countries.to_dict('records')
    haz_scene = ["FU_1in1000(1).{}"]
    for country in countries:
        if not country['iso3'] == 'BGD':
            continue

        iso3 = country['iso3']
        gid_region = country['gid_region']
        gid_level = 'GID_{}'.format(gid_region)
        filename = "gadm36_{}.shp".format(gid_region)
        path_region = os.path.join('data', 'processed', iso3, 'regions', filename)
        gdf_region = geopandas.read_file(path_region, crs="EPSG:4326")
        # gdf_region = gdf_region.to_crs('epsg:3857')
        region_dict = gdf_region.to_dict('records') 

        for region in region_dict:
            gid_id = region[gid_level]
            print("working on {}".format(gid_id))
            process_regional_hazard(country, region, haz_scene)
