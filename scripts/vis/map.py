# plotting
import os
import json
import rasterio
from rasterio.mask import mask
import pandas
import geopandas
import matplotlib.pyplot as plt
import seaborn as sns
import contextily as cx
# import configparser

# CONFIG = configparser.ConfigParser()
# CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
# BASE_PATH = CONFIG['file_locations']['base_path']

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
        vul_pop = gdf_pop['pop_est'].sum()

        output.append({
            'iso3': iso3,
            'gid_id': gid_id,
            'pop_est': vul_pop,
            'income_group': income,
            'continent': continent
        })

    output=pandas.DataFrame(output)
    filename_out = 'pop_at_risk.csv'
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

        if not country['iso3'] == 'AGO':
            continue
        # if country['Exclude'] == 1:
        #     continue

        iso3 = country['iso3']
        gid_region = country['gid_region']
        gid_level = 'GID_{}'.format(gid_region)

        filename = 'coastal_lookup.csv'
        folder = os.path.join('data', 'processed', iso3, 'coastal')
        path_coast= os.path.join(folder, filename)
        if not os.path.exists(path_coast):
            continue

        print('Working on {}'.format(iso3))
        process_vul_pop(country)

        filename_in = 'pop_at_risk.csv'
        folder_in = os.path.join('data', 'processed', iso3 , 'csv')
        path_in = os.path.join(folder_in, filename_in)
        if not os.path.exists(path_in):
            continue

        pop = pandas.read_csv(path_in)
        pop = pop.to_dict('records')
        output = output + pop

    output = pandas.DataFrame(output)
    filename_out = 'global_vul_pop.csv'
    folder_out = os.path.join('data', 'processed', 'results' , 'csv')
    path_out = os.path.join(folder_out, filename_out)
    if not os.path.exists(path_out):
        os.makedirs(path_out)
    output.to_csv(path_out, index = False)
    # data = pandas.read_csv(path_out)

    # print('onto the map')
    # #import our boundaries data
    # filename = 'global_outline.shp'
    # path_in = os.path.join('data', 'processed', 'Global', filename) 
    # boundaries = geopandas.read_file(path_in)

    # #merge population data onto our boundaries 
    # boundaries = boundaries.merge(data, left_on= 'gid_id' , right_on='gid_id')

    # #define dummy value bins and then labels for each one
    # bins = [-1e6, 5000, 50000, 100000, 500000, 1000000, 5000000, 1e12]
    # labels = ['<5k','5k-50k','50k-100k','100k-500k','500k-1mil','1mil-5mil', '>5mil']

    # #create a new variable with our dummy bin labels
    # boundaries['bin'] = pandas.cut(
    #     boundaries['pop_est'],
    #     bins=bins,
    #     labels=labels
    # )
    # #open a new seaborn figure
    # sns.set(font_scale=1)

    # dimensions = (20,10)
    # fig, ax = plt.subplots(1, 1, figsize=dimensions)
    # fig.set_facecolor('gainsboro')

    # #now plot our data using pandas plot

    # base = boundaries.plot(column='bin', ax=ax, cmap='viridis', linewidth=0, #inferno_r
    #     legend=True, antialiased=False)

    # cx.add_basemap(ax, crs='epsg:4326') #add the map baselayer

    # #allocate a plot title 
    # n = len(boundaries)
    # name = 'Population At Risk To Coastal Flooding (n={})'.format(n)
    # fig.suptitle(name)

    # #specify where to write our .png file to
    # path = os.path.join('data', 'processed', 'figures', 'pop_flood_risk.png')
    # fig.savefig(path)
    # plt.close(fig)
    