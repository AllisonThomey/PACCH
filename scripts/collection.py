#this script creates then collects all pop data 
#for individual countries
import os
import json
import rasterio
from rasterio.mask import mask
import pandas
import geopandas

#function to turn data into csv
def process_vul_pop(region):
    """
    This function creates a csv for each country with the population vulnerable
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

        filename_pop = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_pop = os.path.join('data', 'processed', iso3 , 'intersect', 'hazard_pop', filename_pop)
        if not os.path.exists(folder_pop):
            continue
        gdf_pop = geopandas.read_file(folder_pop)
        area = gdf_pop['area_km2'].sum()
        vul_pop = gdf_pop['pop_est'].sum()

        #adding total original population from worldpop for each region
        filename_pop = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_pop = os.path.join('data', 'processed', iso3 , 'population', filename_pop)
        if not os.path.exists(folder_pop):
            continue
        og_pop = geopandas.read_file(folder_pop)
        total_pop = og_pop['value'].sum()

        output.append({
            'iso3': iso3,
            'gid_id': gid_id,
            'pop_est': vul_pop,
            'income_group': income,
            'continent': continent,
            'area_km2': area,
            'total_pop':total_pop
        })
    output=pandas.DataFrame(output)
    filename_out = 'varifying_pop.csv'
    folder_out = os.path.join('data', 'processed', iso3 , 'csv')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_out = os.path.join(folder_out, filename_out)
    output.to_csv(path_out, index = False)

    return


if __name__ == "__main__":

    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')
    countries = countries.to_dict('records')

    output = []
    for country in countries:

        if country['Exclude'] == 1:
            continue

        if country['income_group'] == 'HIC':
            continue

        iso3 = country['iso3']
        gid_region = country['gid_region']
        gid_level = 'GID_{}'.format(gid_region)
    
        filename = 'coastal_lookup.csv'
        folder = os.path.join('data', 'processed', iso3, 'coastal')
        path_coast= os.path.join(folder, filename)
        if not os.path.exists(path_coast):
            continue

        # filename = '{}_relative_wealth_index.csv'.format(iso3)
        # path_rwi = os.path.join('data','raw','rwi', filename)
        # if not os.path.exists(path_rwi):
        #     continue 

        folder_pop = os.path.join('data', 'processed', iso3 , 'intersect', 'hazard_pop')
        if not os.path.exists(folder_pop):
            continue

        print('Working on {}'.format(iso3))
        process_vul_pop(country)

        filename_in = 'varifying_pop.csv'
        folder_in = os.path.join('data', 'processed', iso3 , 'csv')
        path_in = os.path.join(folder_in, filename_in)
        if not os.path.exists(path_in):
            continue
        
        pop = pandas.read_csv(path_in)
        pop = pop.to_dict('records')
        output = output + pop

    output = pandas.DataFrame(output)
    filename_out = 'all_global_vul_pop.csv'
    folder_out = os.path.join('data', 'processed', 'results' , 'csv')
    path_out = os.path.join(folder_out, filename_out)
    if not os.path.exists(path_out):
        os.makedirs(path_out)
    output.to_csv(path_out, index = False)