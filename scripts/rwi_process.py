#preprocessing for rwi in LMICs
import os
import json
import rasterio
from rasterio.mask import mask
import pandas
import geopandas as gpd


def process_national_rwi(country):
    """

    define function

    """
    #assigning variables
    iso3 = country["iso3"]

    #path in for rwi files
    filename = '{}_relative_wealth_index.csv'.format(iso3)
    path_rwi = os.path.join('data','raw','rwi', filename)
    wealth = gpd.read_file(path_rwi, encoding='latin-1')

    #making long lat points into geometry column
    gdf = gpd.GeoDataFrame(
        wealth, geometry=gpd.points_from_xy(wealth.longitude, wealth.latitude), crs="EPSG:4326"
    )  

    #setting path out
    filename_out = '{}_relative_wealth_index.shp'.format(iso3) #each regional file is named using the gid id
    folder_out = os.path.join('data', 'processed', iso3 , 'rwi', 'national')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_out = os.path.join(folder_out, filename_out)

    #saving new .csv to location
    gdf.to_file(path_out,crs="EPSG:4326")
    
    return



def process_regional_rwi(country, region):
    """
    function

    """
    iso3 = country['iso3']                 
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

    # #loading in gid level shape file
    # filename = "gadm36_{}.shp".format(gid_region)
    # path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    # gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
    gdf_region = gpd.GeoDataFrame(gpd.GeoSeries(region.geometry), crs="EPSG:4326")


    # filename = "test.shp"
    # path = os.path.join('data', 'raw', filename)
    # gdf_region.to_file(path, crs="EPSG:4326")

    # # print(len(gdf_region))

    #loading in rwi info
    filename = '{}_relative_wealth_index.shp'.format(iso3) #each regional file is named using the gid id
    folder= os.path.join('data', 'processed', iso3 , 'rwi', 'national')
    path_rwi= os.path.join(folder, filename)
    geo = gpd.read_file(path_rwi, crs="EPSG:4326")
    gdf_rwi = gpd.GeoDataFrame(geo.geometry, crs='epsg:4326')

    # filename = "test_rwi.shp"
    # path = os.path.join('data', 'raw', filename)
    # gdf_rwi.to_file(path, crs="EPSG:4326")

    region_rwi = gpd.overlay(gdf_region, gdf_rwi, how='intersection')

    # print(len(region_rwi))
    
    filename = '{}.shp'.format(gid_id)
    folder_out = os.path.join('data', 'processed', iso3, 'rwi', 'regions' )
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_out = os.path.join(folder_out, filename)

    region_rwi.to_file(path_out, crs="EPSG:4326")


    return



if __name__ == "__main__":

    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')

    for idx, country in countries.iterrows():

        if not country["iso3"] == 'BGD':
            continue
        iso3 = country['iso3'] 
        # print("Working on process_national_rwi")
        # process_national_rwi(country)

            #define our country-specific parameters, including gid information
    
        gid_region = country['gid_region']
        gid_level = 'GID_{}'.format(gid_region)
        
        #set the filename depending our preferred regional level
        filename = "gadm36_{}.shp".format(gid_region)
        folder = os.path.join('data','processed', iso3, 'gid_region')
        
        #then load in our regions as a geodataframe
        path_regions = os.path.join(folder, filename)
        regions = gpd.read_file(path_regions, crs='epsg:4326')

        for idx, region in regions.iterrows():
            print("working on {}".format(region[gid_level]))
            process_regional_rwi(country, region)





