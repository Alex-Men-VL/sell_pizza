import json
import logging

from environs import Env

from moltin_api import (
    get_access_token,
    get_categories,
    get_products_by_category_slug,
    get_product_main_image_url
)
from redis_db import get_redis_connection

logger = logging.getLogger(__file__)


def get_main_menu_element():
    logo_url = 'https://image.similarpng.com/very-thumbnail/2020/05/Pizza-logo-design-template-Vector-PNG.png'
    element = {
        "title": "Меню",
        "subtitle": "Здесь вы можете выбрать один из вариантов.",
        "image_url": logo_url,
        "buttons": []
    }
    buttons = (
        ('Корзина', 'cart'),
        ('Акции', 'promo'),
        ('Сделать заказ', 'pay')
    )
    for title, payload in buttons:
        element['buttons'].append(
            {
                "type": "postback",
                "title": title,
                "payload": payload
            }
        )
    return element


def get_last_menu_element(moltin_token, total_category_slug):
    image_url = 'https://primepizza.ru/uploads/position/large_0c07c6fd5c4dcadddaf4a2f1a2c218760b20c396.jpg'
    element = {
        "title": "Не нашли нужную пиццу?",
        "subtitle": "Остальные пиццы можно посмотреть в одной из категорий.",
        "image_url": image_url,
        "buttons": []
    }
    categories = get_categories(moltin_token)['data']
    buttons = (
        (category['name'], category['slug']) for category in categories
        if category['slug'] != total_category_slug
    )
    for name, slug in buttons:
        element['buttons'].append(
            {
                "type": "postback",
                "title": name,
                "payload": f"slug_{slug}"
            }
        )
    return element


def get_products_menu_elements(moltin_token, category_slug,
                               product_per_page=5):
    elements = []
    products = get_products_by_category_slug(moltin_token,
                                             category_slug)['data']
    for product in products[:product_per_page]:
        price = product['meta']['display_price']['with_tax']['formatted']
        menu_element = {
            "title": f"{product['name']} ({price} р.)",
            "subtitle": product['description'],
            "buttons": [
                {
                    "type": "postback",
                    "title": "Добавить в корзину",
                    "payload": f"product_{product['id']}"
                }
            ]
        }
        if main_image := product['relationships'].get('main_image'):
            image_id = main_image['data']['id']
            image_url = get_product_main_image_url(moltin_token, image_id)
            menu_element.update({
                "image_url": image_url
            })
        elements.append(menu_element)
    return elements


def create_menu(moltin_token):
    categories = get_categories(moltin_token)['data']
    menu = {}
    main_element = get_main_menu_element()
    for category in categories:
        category_slug = category['slug']
        menu_category = f'menu_{category_slug}'
        products_elements = get_products_menu_elements(moltin_token,
                                                       category_slug)
        last_element = get_last_menu_element(moltin_token, category_slug)
        total_menu = [main_element, *products_elements, last_element]

        menu.update({
            menu_category: total_menu
        })
    return menu


def cache_menu(moltin_token, database):
    menu = create_menu(moltin_token)
    menu_updated = database.set('menu', json.dumps(menu))
    if menu_updated:
        logger.info('Меню успешно обновлено')


def main():
    env = Env()
    env.read_env()
    logging.basicConfig(level=logging.INFO)

    redis_uri = env.str('REDIS_URL')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')
    client_id = env.str('CLIENT_ID')
    client_secret = env.str('CLIENT_SECRET')

    moltin_token = get_access_token(client_id, client_secret)['access_token']
    redis_connection = get_redis_connection(redis_uri, redis_port,
                                            redis_password)
    cache_menu(moltin_token, redis_connection)


if __name__ == '__main__':
    main()
