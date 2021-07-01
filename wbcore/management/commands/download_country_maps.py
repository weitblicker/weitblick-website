from django.core.management.base import BaseCommand, no_translations
import urllib.request
from django.conf import settings
from os import path, makedirs
from pathlib import Path
import json



class Command(BaseCommand):
    """
    Creates slugs based on the name for each partner without slug.
    """
    @no_translations
    def handle(self, *args, **options):
        env_path = Path(settings.ENV_PATH)
        local_static_path = env_path.parent / 'wbcore' / 'static'
        static_location = local_static_path if settings.DEBUG else Path(settings.SERVER_STATIC_ROOT)

        path_highmaps_countries = static_location / 'highmaps' / 'countries'
        print('Save files in ' + str(path_highmaps_countries))
        if not path.exists(path_highmaps_countries):
            makedirs(path_highmaps_countries)

        with open(str(path_highmaps_countries.parent) + '/world-robinson-highres.geo.json') as f:
            world_data = json.load(f)

        print('Beginning file downloads with urllib2...')
        # Iterating through the json list
        count = 0
        for country in world_data['features']:
            country_code = country['properties']['hc-key']
            print('download country: ' + country['properties']['name'])
            url = 'https://code.highcharts.com/mapdata/countries/{}/{}-all.js'.format(country_code, country_code)
            try:
                urllib.request.urlretrieve(url, str(path_highmaps_countries / country_code) + '.js')
                count += 1
            except urllib.error.HTTPError:
                print('country {} with code {} cannot be downloaded'.format(country['properties']['name'], country_code))

        print("created {} country files".format(count))
