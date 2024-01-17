import requests
import pandas as pd
from io import StringIO
import math
import token_file

API_TOKEN = token_file.API_TOKEN
BASE_URL = 'https://api.atmo-aura.fr/api/v1/'

def fetch_data(dataset_number, params_list):
    """
    Fetch from the API pi.atmo-aura.fr, the different datasets awailable
    """
    endpoints = {
        '1': 'sites',
        '2': 'mesures',
        '4': 'valeurs/horaire',
        '5': 'valeurs/journaliere',
        '6': 'valeurs/mensuelle',
        '7': 'valeurs/annuelle',
        '8': 'valeurs/prelevement',
    }

    params = {param.split('=')[0]: param.split('=')[1] for param in params_list}
    params['api_token'] = API_TOKEN

    endpoint = endpoints.get(dataset_number)
    if endpoint:
        response = requests.get(f'{BASE_URL}{endpoint}', params=params)
        if response.status_code == 200:
            if 'format' in params and params['format'] == 'csv':
                csv_data = StringIO(response.text)
                df = pd.read_csv(csv_data, delimiter=';', decimal=',')
                return df
            else:
                return response.json()  # Parse and return JSON
        else:
            return response.text  # Return error message as text
    else:
        return "Invalid dataset number."


def haversine(lat1, lon1, lat2, lon2):
    """
    Compute Euclidean distance from latitude, longitude
    """
    R = 6371.0  # Earth radius in kilometers
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def find_site_coordinates(reference_station_id):
    """
    Get lat and lon of a station from its station_id
    """
    params_list_sites = ['format=geojson', f'sites={reference_station_id}']
    sites_data = fetch_data('1', params_list_sites)
    if len(sites_data) == 0:
        raise ValueError("Reference station ID not found")
    feature = sites_data['features'][0]
    return feature['geometry']['coordinates'][1], feature['geometry']['coordinates'][0]  # lat, lon

def retrieve_nearby_station(reference_station_id, radius, param_lists=None):
    """
    Retrieve all measuring station within a certain radius of a reference station
    """
    if not param_lists:
        param_lists = ['format=geojson']
    data = fetch_data('1', param_lists)

    station_ids = set() 
    center_lat, center_lon = find_site_coordinates(reference_station_id=reference_station_id)
    for feature in data['features']:
        feature_lat = feature['geometry']['coordinates'][1]
        feature_lon = feature['geometry']['coordinates'][0]
        distance = haversine(center_lat, center_lon, feature_lat, feature_lon)
        
        # Check if the feature falls within the specified radius
        if distance > radius:
            continue
        station_ids.add(feature['properties']['id'])
    
    return station_ids