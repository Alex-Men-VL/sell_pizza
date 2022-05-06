from moltin_api import (
    get_product_main_image_url,
    get_products_by_category_slug,
    get_categories
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
                "payload": slug
            }
        )
    return element


def generate_front_menu_elements(moltin_token, product_per_page=5,
                                 front_page_category_slug='main'):
    main_element = get_main_menu_element()
    elements = [main_element]
    products = get_products_by_category_slug(moltin_token,
                                             front_page_category_slug)['data']
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

    last_element = get_last_menu_element(moltin_token,
                                         front_page_category_slug)
    elements.append(last_element)
    return elements
