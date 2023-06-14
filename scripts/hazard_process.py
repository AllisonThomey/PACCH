#making user defined functions for processing hazard 
#starting with code base from 470
import os
import json
import rasterio
from rasterio.mask import mask
import pandas
import geopandas as gpd

def process_national_hazard(country):
    """
    This function creates a national hazard .tiff using 
    national boundary files created in 
    process_national_boundary function

    """
    #settign variables
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)

    #loading in coastal flood hazard .tiff
    filename = 'inuncoast_rcp8p5_wtsub_2080_rp1000_0.tif'
    path_hazard = os.path.join('data','raw','flood_hazard', filename)
    hazard = rasterio.open(path_hazard, 'r+')
    hazard.nodata = 255                       #set the no data value
    hazard.crs.from_epsg(4326)  

    #set the filename depending our preferred regional level
    filename = 'national_outline.shp'
    folder = os.path.join('data', 'processed', iso3, 'national', filename)
        
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
    filename_out = 'inuncoast_rcp8p5_wtsub_2080_rp1000_0.tif' 
    folder_out = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', 'national')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_out = os.path.join(folder_out, filename_out)

    with rasterio.open(path_out, "w", **out_meta) as dest:
        dest.write(out_img)


    return


def convert_national_hazard(country):
    """
    This function converts the national hazard .tif file into
    a .shp file
    
    """
    iso3 = country['iso3']
    gid_region = country['gid_region']

    folder_out = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', 'national')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    filename = 'inuncoast_rcp8p5_wtsub_2080_rp1000_0.shp'
    path_out = os.path.join(folder_out, filename)

    folder = os.path.join('data', 'processed', iso3, 'hazards', 'inuncoast', 'national')
    filename = 'inuncoast_rcp8p5_wtsub_2080_rp1000_0.tif'
    path_in = os.path.join(folder, filename)

    #moved if not con down with filename added in
    if not os.path.exists(path_in):
        os.makedirs(path_in)

    with rasterio.open(path_in) as src:

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



def process_regional_hazard (country, region):
    """
    This function creates a regional composite hazrd 
    .tif


    """
    #assigning variables
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]


    #loading in hazard .tif
    filename = 'inuncoast_rcp8p5_wtsub_2080_rp1000_0.tif' 
    folder = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', 'national')
    path_hazard = os.path.join(folder, filename)
    hazard = rasterio.open(path_hazard, 'r+')
    hazard.nodata = 255                       #set the no data value
    hazard.crs.from_epsg(4326)  

    geo = gpd.GeoDataFrame(gpd.GeoSeries(region.geometry))
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
    filename_out = '{}.tif'.format(gid_id)
    folder_out = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', gid_id)
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_out = os.path.join(folder_out, filename_out)

    with rasterio.open(path_out, "w", **out_meta) as dest:
        dest.write(out_img) 


    return



def convert_regional_hazard (country, region):
    """
    This function converts the national hazard .tif file into
    a .shp file
    
    """
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]


    folder_out = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', gid_id)    
    filename = '{}.shp'.format(gid_id)
    path_out = os.path.join(folder_out, filename)
    if not os.path.exists(path_out):
        os.makedirs(path_out)


    folder = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', gid_id)
    filename = '{}.tif'.format(gid_id)
    path_in = os.path.join(folder, filename)
    if not os.path.exists(path_in):
        os.makedirs(path_in)

    #moved if not con down with filename added in
    # if not os.path.exists(path_in):
    #     continue

    with rasterio.open(path_in) as src:

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
    # if len(output) ==0:
    #     continue

    output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')
    output.to_file(path_out, driver='ESRI Shapefile')


    return





if __name__ == "__main__":

    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')

    for idx, country in countries.iterrows():

        # if country['coastal_exclude'] == 1: # let's work on a single country at a time
        #     continue   
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
        
        print("Working on process_national_hazard for {}".format(iso3))
        process_national_hazard(country)
        convert_national_hazard (country)
        
        print("Working on process_regional_hazard")
        
        for idx, region in regions.iterrows():
        # #     # # if region.geometry == None:
        # #      continue 
            if not region[gid_level] == 'BGD.1.5_1':
                continue
            
       
            process_regional_hazard(country, region)
            convert_regional_hazard (country, region)
