from moltin_api import (
    get_product_main_image_url,
    get_products_by_category_name
)


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


def generate_front_menu_elements(moltin_token, product_per_page=5,
                                 front_page_category='Main'):
    main_element = get_main_menu_element()
    elements = [main_element]
    products = get_products_by_category_name(moltin_token,
                                             front_page_category)['data']
    for product in products[:product_per_page]:
        price = product['meta']['display_price']['with_tax']['formatted']
        menu_element = {
            "title": f"{product['name']} ({price} р.)",
            "subtitle": product['description'],
            "buttons": [
                {
                    "type": "postback",
                    "title": "Добавить в корзину",
                    "payload": product['id']
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
