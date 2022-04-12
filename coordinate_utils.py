import requests
from geopy import distance


def fetch_coordinates(address, yandex_api_key):
    url = 'https://geocode-maps.yandex.ru/1.x'
    apikey = yandex_api_key
    params = {
        'geocode': address,
        'apikey': apikey,
        'format': 'json',
    }
    response = requests.get(url, params=params)
    response.raise_for_status()

    found_places = response.json()['response'][
        'GeoObjectCollection'
    ]['featureMember']

    if not found_places:
        return None

    most_relevant_place = found_places[0]
    lon, lat = most_relevant_place['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def get_nearest_restaurant(order_coordinates, restaurants):
    distances = []
    order_lon, order_lat = order_coordinates
    for restaurant in restaurants:
        order_distance = distance.distance(
            (order_lat, order_lon),
            (restaurant['Latitude'], restaurant['Longitude'])
        )
        distances.append(
            {
                'address': restaurant['Address'],
                'lon': restaurant['Longitude'],
                'lat': restaurant['Latitude'],
                'id': restaurant['id'],
                'distance_km': order_distance.kilometers,
                'distance_m': order_distance.meters,
                'courier_id': restaurant['Tg-id']
            }
        )
    nearest_restaurant = min(distances,
                             key=lambda rest: rest['distance_km'])
    return nearest_restaurant
