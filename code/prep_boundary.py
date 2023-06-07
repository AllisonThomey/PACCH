#file that makes national outline and gid region outlines
import os
import pandas
import geopandas
#removing small shapes and cutting out boundray by GID region
from shapely.geometry import MultiPolygon

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



#making file paths
path = os.path.join('data', 'countries.csv')
countries = pandas.read_csv(path, encoding='latin-1')



for idx, country in countries.iterrows():

    # if country['Exclude'] == 1: # if the current country iso3 does not match  
    #     continue                     # continue in the loop to the next country
    if not country['iso3']=='BGD':
        continue
        print(country['iso3'])
    
    #GID0
    filename = "gadm36_0.shp"
    folder = os.path.join('data', 'raw', 'gadm36_levels_shp')
    path_in= os.path.join(folder, filename)
    boundaries = geopandas.read_file(path_in, crs="epsg:4326")

    iso3 = country["iso3"]
    country_boundaries = boundaries[boundaries['GID_0'] == country['iso3']]
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)

    regions_folder_path = os.path.join('data', 'processed', iso3, 'processed_regions')
    if not os.path.exists(regions_folder_path):
        os.makedirs(regions_folder_path)
   
    #this is how we simplify the geometries
    country_boundaries["geometry"] = country_boundaries.geometry.simplify(
        tolerance=0.01, preserve_topology=True)
   
     #remove small shapes
    country_boundaries['geometry'] = country_boundaries.apply(
         remove_small_shapes, axis=1)
    
    #saving national outline
    filename = 'national_outline.shp'
    path_out = os.path.join('data', 'processed', iso3, 'national', filename)
    if not os.path.exists(path_out):
        os.makedirs(path_out)
    country_boundaries.to_file(path_out, crs='epsg:4326')

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
   
    print("Processed country boundary for {}".format(country['iso3']))