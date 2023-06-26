#making rwi points into voronoi polygons
import os
from rasterio.mask import mask
import pandas
import geopandas as gpd
import numpy as np
import configparser
from shapely.ops import cascaded_union
from geovoronoi import voronoi_regions_from_coords, points_to_coords
from shapely.geometry import Point, LineString, Polygon

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']



def create_rwi_voronoi(country, region):
    """
    creates rwi voronoi polygons by region

    """
    iso3 = country['iso3']                 
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]   
    
    #load in rwi as gdf
    filename = '{}.shp'.format(gid_id)
    path_rwi = os.path.join(BASE_PATH, 'processed', iso3, 'rwi', 'regions', filename )
    gdf_rwi = gpd.read_file(path_rwi, crs="EPSG:4326")

    #loading in gid level shape file
    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]

    boundary_shape = cascaded_union(gdf_region.geometry)
    coords = points_to_coords(gdf_rwi.geometry)

    region_polys, region_pts = voronoi_regions_from_coords(coords, boundary_shape)


    interim = []
    for key, value in region_polys.items():
        for idx, rwi in gdf_rwi.iterrows():
            if value.intersects(rwi['geometry']):
                interim.append({ 
                    'type': 'Polygon',
                    'geometry': value,
                    'properties': {
                        "rwi": rwi['rwi'],
                        'error': rwi['error']
                    }
                })
    output = gpd.GeoDataFrame.from_features(interim, crs="EPSG:4326")


    filename = 'voronoi_{}.shp'.format(gid_id)
    folder_out = os.path.join(BASE_PATH, 'processed', iso3, 'rwi', 'regions' )
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_out = os.path.join(folder_out, filename)

    output.to_file(path_out, crs="EPSG:4326")


    return





if __name__ == "__main__":

    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')

    for idx, country in countries.iterrows():

        if not country["iso3"] == 'BGD':
            continue

        iso3 = country['iso3'] 

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
            create_rwi_voronoi(country, region)