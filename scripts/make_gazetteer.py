# make_gazetteer.py
# R.A. Kinds
# 1/11/2023
# Een los script om de gazetteer voor te bereiden, zodat dit niet bij elke keer runnen gebeurt

import pandas as pd

# Load gazetteer and make it easy to query, returns dataframe
def main():
    nl = pd.read_csv('../data/gazetteer/NL.txt', engine='python', sep='\t', usecols=[0, 1, 3, 4, 5, 7, 8, 14])
    nl.columns = ['geonameid', 'name', 'alternatenames', 'latitude', 'longitude', 'feature code', 'country code', 'population']

    countries = pd.read_csv('../data/gazetteer/countries.txt', engine='python', sep='\t')
    countries.columns = ['geonameid', 'name', 'alternatenames', 'latitude', 'longitude', 'feature code', 'population']

    global_cities = pd.read_csv('../data/gazetteer/cities500.txt', engine='python', sep='\t', usecols=[0, 1, 3, 4, 5, 7, 8, 14])
    global_cities.columns = ['geonameid', 'name', 'alternatenames', 'latitude', 'longitude', 'feature code',
                             'country code', 'population']
    remove_dutch_cities = global_cities['country code'] == 'NL'
    global_cities = global_cities[~remove_dutch_cities]

    gazetteer = pd.concat([nl, countries, global_cities])
    gazetteer.loc[gazetteer['geonameid'] == 2747373, 'name'] = 'Den Haag'
    gazetteer.to_csv('../data/gazetteer.csv', sep='\t', index=False)


main()
