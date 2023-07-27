#file that makes national outline and gid region outlines
import os
import pandas
import geopandas
#removing small shapes and cutting out boundray by GID region
from shapely.geometry import MultiPolygon
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


if __name__ == "__main__":

    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')
    output = []
    for idx, country in countries.iterrows():
        iso3 = country['iso3']
       
        if country['Exclude'] == 1:
            continue

    #     print("Working on {}".format(iso3))
    #     process_national_boundary(country)

    #     print("Working on process_regional_boundary")
    #     process_regional_boundary(country)

        gid_region = country['gid_region']
        gid_level = 'GID_{}'.format(gid_region)
        
        #then load in our regions as a geodataframe
        filename = "gadm36_{}.shp".format(gid_region)
        path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
        gdf_region = geopandas.read_file(path_region, crs="EPSG:4326")
        gdf_region = gdf_region.to_crs('epsg:3857')
        region_dict = gdf_region.to_dict('records')
            
        filename = 'coastal_lookup.csv'
        folder = os.path.join(BASE_PATH, 'processed', iso3, 'coastal')
        path_coast= os.path.join(folder, filename)
        if not os.path.exists(path_coast):
            continue
        coastal = pandas.read_csv(path_coast)
        coast_list = coastal['gid_id'].values. tolist()

        for region in region_dict:
            if not region[gid_level] in coast_list:
                continue

            output.append({
                'geometry': region['geometry'],
                'properties': {
                'gid_id': region[gid_level]
                }
            })

    output = geopandas.GeoDataFrame.from_features(output, crs='epsg:4326') 

    filename = 'global_outline.shp'
    path_out = os.path.join('data', 'processed', 'Global', filename)
    output.to_file(path_out, crs='epsg:4326')

