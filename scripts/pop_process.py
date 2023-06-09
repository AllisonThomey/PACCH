#starting code base from 470 for populaiton processing
import os
import json
import rasterio
from rasterio.mask import mask
import pandas
import geopandas as gpd

def process_population(region):
    """
        Define what function does

    """
    # if region.geometry == None:
    #     continue

    #let's load in our hazard layer
    filename = 'ppp_2020_1km_Aggregated.tif'
    path_hazard = os.path.join('data','raw','worldpop', filename)
    hazard = rasterio.open(path_hazard, 'r+')
    hazard.nodata = 255                       #set the no data value
    hazard.crs.from_epsg(4326)                #set the crs

    #create a new gpd dataframe from our single region geometry
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

    #now we write out at the regional level
    filename_out = 'ppp_2020_1km_Aggregated.tif' #each regional file is named using the gid id
    folder_out = os.path.join('data', 'processed', iso3 , 'population', gid_id)
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_out = os.path.join(folder_out, filename_out)

    with rasterio.open(path_out, "w", **out_meta) as dest:
        dest.write(out_img)
    
    return  


if __name__ == "__main__":

    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')

    for idx, country in countries.iterrows():

        # if country['coastal_exclude'] == 1: # let's work on a single country at a time
        #     continue   
        if not country['iso3'] =='BGD':
            continue
        
        #define our country-specific parameters, including gid information
        iso3 = country['iso3']
        gid_region = country['gid_region']
        gid_level = 'GID_{}'.format(gid_region)
        
        #set the filename depending our preferred regional level
        filename = "gadm36_{}.shp".format(gid_region)
        folder = os.path.join('data','processed', iso3, 'gid_region')
        
        #then load in our regions as a geodataframe
        path_regions = os.path.join(folder, filename)
        regions = gpd.read_file(path_regions, crs='epsg:4326')#[:2]
        
        for idx, region in regions.iterrows():
            gid_id = region[gid_level]
            # if region.geometry == None:
            #     continue
            if not region[gid_level] == 'BGD.1.5_1':
                continue
            
            print("Working on process_population")
            process_population(region)

        
