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


def process_gsap(country, region):
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
    gdf_region = geopandas.read_file(path_region, crs="EPSG:3857")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')

    for region in region_dict:

        filename = '{}.shp'.format(gid_id)
        folder_out = os.path.join(BASE_PATH, 'processed', iso3, 'fathom', 'gsap' )
        path_out = os.path.join(folder_out, filename)

        if os.path.exists(path_out):
            continue

        #loading in rwi info
        filename = 'GSAP2.shp'
        path_wb = os.path.join(BASE_PATH, 'raw', 'GSAP', filename )
        if not os.path.exists(path_wb):
            continue
        gdf_wb = geopandas.read_file(path_wb, crs="EPSG:4326")

        gdf_rwi_int = geopandas.overlay(gdf_wb, gdf_region, how='intersection')
        if len(gdf_rwi_int) == 0:
            continue
        os.makedirs(path_out)   
        gdf_rwi_int.to_file(path_out, crs="EPSG:4326")

    return


def process_regional_population(country, region, haz_scene):
    """
    This function creates a regional population .shp usign fathom hazard
    
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
    haz_scene = ["FU_1in1000(1).{}"]

    # for region in region_dict:
    for scene in haz_scene:

        filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_out = os.path.join('data', 'processed', iso3 , 'fathom', 'haz_pop', scene)
        path_out = os.path.join(folder_out, filename_out)

        if os.path.exists(path_out):
            continue

        filename_haz = scene.format("shp")
        folder_haz = os.path.join('data', 'processed', iso3, 'fathom', gid_id)
        path_haz = os.path.join(folder_haz, filename_haz)
        if not os.path.exists(path_haz):
            continue
        gdf_haz =  geopandas.read_file(path_haz, crs="EPSG:3857")
        gdf_haz = gdf_haz.to_crs('epsg:3857')

        #loading in national population file
        filename = 'ppp_2020_1km_Aggregated.shp' #each regional file is named using the gid id
        folder= os.path.join('data', 'processed', iso3 , 'population', 'national')
        path_pop = os.path.join(folder, filename)
        gdf_pop =  geopandas.read_file(path_pop, crs="EPSG:3857")
        gdf_pop = gdf_pop.to_crs('epsg:3857')

        gdf_pop = geopandas.overlay(gdf_pop, gdf_haz, how='intersection')
        if len(gdf_pop) == 0:
            continue

        gdf_pop['area_km2'] = gdf_pop['geometry'].area / 1e6
        gdf_pop['pop_est'] = gdf_pop['value_1']* gdf_pop['area_km2']
        gdf_pop['depth'] = gdf_pop['value_2']

        os.makedirs(path_out)
        gdf_pop.to_file(path_out, crs='epsg:3857')

    return


def intersect_haz_pop_chi(country, region, haz_scene):
    """
    This function creates an intersect between the 
    hazard area, population, and poverty data provided by
    Chi et al.
    
    """
    #assigning variables
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = geopandas.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')
    haz_scene = ["FU_1in1000(1).{}"]

    # for region in region_dict:
    for scene in haz_scene:

        # now we write out path at the regional level
        filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_out = os.path.join(BASE_PATH, 'processed', iso3 ,'fathom', 'pop_chi', scene)
        path_out = os.path.join(folder_out, filename_out)

        if os.path.exists(path_out):
            continue

        #load in poverty by region .shp file
        filename = '{}.shp'.format(gid_id)
        path_rwi = os.path.join(BASE_PATH, 'processed', iso3, 'rwi', 'regions', filename )
        if not os.path.exists(path_rwi):
            continue
        gdf_rwi = geopandas.read_file(path_rwi, crs="EPSG:3857")
        gdf_rwi = gdf_rwi.to_crs('epsg:3857')

        #load in hazard .shp file
        filename_haz = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_haz = os.path.join('data', 'processed', iso3 , 'fathom', 'haz_pop', scene)
        path_haz = os.path.join(folder_haz, filename_haz)
        # if not os.path.exists(path_haz):
        #     continue
        gdf_hazard = geopandas.read_file(path_haz, crs="EPSG:3857")
        gdf_hazard = gdf_hazard.to_crs("epsg:3857")

        gdf_affected = geopandas.overlay(gdf_rwi, gdf_hazard, how='intersection')
        if len(gdf_affected) == 0:
            continue

        gdf_affected = gdf_affected.to_crs('epsg:3857')

        if not os.path.exists(path_out):
            os.makedirs(path_out)
        gdf_affected.to_file(path_out, crs='epsg:3857')

    return


def intersect_haz_pop_gsap(country, region, haz_scene):
    """
    This function creates an intersect between the 
    hazard area, population, and poverty data provided by
    gsap.
    
    """
    #assigning variables
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = geopandas.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')
    haz_scene = ["FU_1in1000(1).{}"]

    # for region in region_dict:
    for scene in haz_scene:

        # now we write out path at the regional level
        filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_out = os.path.join(BASE_PATH, 'processed', iso3 ,'fathom', 'pop_gsap', scene)
        path_out = os.path.join(folder_out, filename_out)

        if os.path.exists(path_out):
            continue

        #load in poverty by region .shp file
        filename = '{}.shp'.format(gid_id)
        folder = os.path.join(BASE_PATH, 'processed', iso3, 'fathom', 'gsap' )
        path_gsap = os.path.join(folder, filename)
        # if not os.path.exists(path_rwi):
        #     continue
        gdf_gsap = geopandas.read_file(path_gsap, crs="EPSG:3857")
        gdf_gsap = gdf_gsap.to_crs('epsg:3857')

        #load in hazard .shp file
        filename_haz = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_haz = os.path.join('data', 'processed', iso3 , 'fathom', 'haz_pop', scene)
        path_haz = os.path.join(folder_haz, filename_haz)
        # if not os.path.exists(path_haz):
        #     continue
        gdf_hazard = geopandas.read_file(path_haz, crs="EPSG:3857")
        gdf_hazard = gdf_hazard.to_crs("epsg:3857")

        gdf_affected = geopandas.overlay(gdf_gsap, gdf_hazard, how='intersection')
        if len(gdf_affected) == 0:
            continue

        gdf_affected = gdf_affected.to_crs('epsg:3857')

        if not os.path.exists(path_out):
            os.makedirs(path_out)
        gdf_affected.to_file(path_out, crs='epsg:3857')

    return



def process_pop_csv(region):
    """
    This function creates a csv for each coastal region with the population vulnerable
    by region

    """
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    income = country['income_group']
    continent = country['continent']

    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = geopandas.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region.to_crs('epsg:3857')
    region_dict = gdf_region.to_dict('records')
    
    haz_scene = ["FU_1in1000(1).{}"]
 
    for scene in haz_scene:
        output = []
        for region in region_dict:
            
            filename = 'coastal_lookup.csv'
            folder = os.path.join('data', 'processed', iso3, 'coastal')
            path_coast= os.path.join(folder, filename)
            if not os.path.exists(path_coast):
                continue
            coastal = pandas.read_csv(path_coast)
            coast_list = coastal['gid_id'].values. tolist()

            if not region[gid_level] in coast_list:
                continue
            gid_id = region[gid_level]

            print(gid_id)

            filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
            folder_out = os.path.join('data', 'processed', iso3 , 'fathom', 'haz_pop', scene)
            path_pop = os.path.join(folder_out, filename_out)
            if not os.path.exists(path_pop):
                continue
            gdf_pop = geopandas.read_file(path_pop)
            vul_pop = gdf_pop['pop_est'].sum()

            #original vulnerable population
            filename_og = '{}'.format(gid_id) #each regional file is named using the gid id
            folder_og = os.path.join('data', 'processed', iso3 , 'intersect', 'hazard_pop', 
                                     "inuncoast_rcp8p5_wtsub_2080_rp1000_0.{}")

            path_og = os.path.join(folder_og, filename_og)
            if not os.path.exists(path_og):
                continue
            gdf_og = geopandas.read_file(path_og)
            og_pop = gdf_og['pop_est'].sum()

            filename_gsap = '{}'.format(gid_id) #each regional file is named using the gid id
            folder_gsap = os.path.join(BASE_PATH, 'processed', iso3 ,'fathom', 'pop_gsap', scene)
            path_gsap = os.path.join(folder_gsap, filename_gsap)
            if not os.path.exists(path_gsap):
                    continue
            gdf_gsap = geopandas.read_file(path_gsap)
            gdf_gsap = gdf_gsap['GSAP2_mean'].astype(float)
            gsap_mean = gdf_gsap.mean()
            gsap_min = min(gdf_gsap)
            gsap_max = max(gdf_gsap)

            filename_chi = '{}'.format(gid_id) #each regional file is named using the gid id
            folder_chi = os.path.join(BASE_PATH, 'processed', iso3 ,'fathom', 'pop_chi', scene)
            path_chi = os.path.join(folder_chi, filename_chi)
            if not os.path.exists(path_chi):
                 continue
            gdf_chi = geopandas.read_file(path_chi)
            gdf_chi = gdf_chi['rwi'].astype(float)
            rwi_mean = gdf_chi.mean()
            rwi_min = min(gdf_chi)
            rwi_max = max(gdf_chi)

            output.append({
                'iso3': iso3,
                'gid_id': gid_id,
                'fath_pop': vul_pop,
                'og_vul_pop': og_pop,
                'gsap_mean': gsap_mean,
                'gsap_min': gsap_min,
                'gsap_max': gsap_max,
                'rwi_mean': rwi_mean,
                'rwi_min': rwi_min,
                'rwi_max': rwi_max

            })
        output=pandas.DataFrame(output)
        filename_out = 'v5_vul_pop.csv'
        folder_out = os.path.join('data', 'processed', iso3 , 'fathom', 'csv', scene)
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)
        path_out = os.path.join(folder_out, filename_out)
        output.to_csv(path_out, index = False)

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

        #coastal look up load in
        filename = 'coastal_lookup.csv'
        folder = os.path.join(BASE_PATH, 'processed', iso3, 'coastal')
        path_coast= os.path.join(folder, filename)
        if not os.path.exists(path_coast):
            continue
        coastal = pandas.read_csv(path_coast)
        coast_list = coastal['gid_id'].values.tolist()

        filename = "gadm36_{}.shp".format(gid_region)

        # process_national_hazard(country)

        path_region = os.path.join('data', 'processed', iso3, 'regions', filename)
        gdf_region = geopandas.read_file(path_region, crs="EPSG:4326")
        # gdf_region = gdf_region.to_crs('epsg:3857')
        region_dict = gdf_region.to_dict('records') 

        for region in region_dict:
            gid_id = region[gid_level]
           
            if not region[gid_level] in coast_list:
                continue

            # print("working on {}".format(gid_id))
            # process_regional_hazard(country, region, haz_scene)
            # process_gsap(country, region)
            # print("working on regional_pop")
            # process_regional_population(country, region, haz_scene)
            # print("working on pop_chi")
            # intersect_haz_pop_chi(country, region, haz_scene)
            # print("working on pop_psap")
            # intersect_haz_pop_gsap(country, region, haz_scene)

        print("working on pop_csv")
        process_pop_csv(region)