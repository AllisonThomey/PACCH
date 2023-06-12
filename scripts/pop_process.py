#starting code base from 470 for populaiton processing
import os
import json
import rasterio
from rasterio.mask import mask
import pandas
import geopandas as gpd

def process_national_population(country):
    """
    This function creates a national population .tiff
    using national boundary files created in 
    process_national_boundary function

    """
    # if region.geometry == None:
    #     continue

    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)

    #let's load in our pop layer
    filename = 'ppp_2020_1km_Aggregated.tif'
    path_pop = os.path.join('data','raw','worldpop', filename)
    hazard = rasterio.open(path_pop, 'r+')
    hazard.nodata = 255                       #set the no data value
    hazard.crs.from_epsg(4326)                #set the crs
        
    #set the filename depending our preferred regional level
    filename = 'national_outline.shp'
    folder = os.path.join('data', 'processed', iso3, 'national', filename)
        
    #then load in our country as a geodataframe
    path_in = os.path.join(folder, filename)
    country_pop = gpd.read_file(path_in, crs='epsg:4326')

    #create a new gpd dataframe from our single country geometry
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
    path_out = os.path.join(folder_out, filename_out)

    with rasterio.open(path_out, "w", **out_meta) as dest:
        dest.write(out_img)
    
    return  


def process_regional_population(country, region):
    """
    This function creates a regional composite population 
    .tiff using regional boundary files created in 
    process_regional_boundary function and national
    population files created in process_national_population
    function.
    
    """
    #assigning variables
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

    #loading in national population file
    filename = 'ppp_2020_1km_Aggregated.tif' #each regional file is named using the gid id
    folder= os.path.join('data', 'processed', iso3 , 'population', 'national')
    path_pop = os.path.join(folder, filename)
    hazard = rasterio.open(path_pop, 'r+')
    hazard.nodata = 255                       #set the no data value
    hazard.crs.from_epsg(4326)
    
    # #load in regional .shp file
    # filename = "gadm36_{}.shp".format(gid_region)
    # path= os.path.join('data', 'processed', iso3,'gid_region', filename)
    # country_pop= gpd.read_file(path, crs='epsg:4326')
    # gid_id = country_pop[gid_level]

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


    # print(gid_id)
    #now we write out at the regional level
    filename_out = '{}.tif'.format(gid_id) #each regional file is named using the gid id
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
        
        # print("Working on process_national_population")
        # process_national_population(country)
        print("Working on process_regional_population")
        
        for idx, region in regions.iterrows():
        # #     # # if region.geometry == None:
        # #      continue 
        #     if not region[gid_level] == 'BGD.1.5_1':
        #         continue
            
       
            process_regional_population(country, region)

        
