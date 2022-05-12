import json

import requests


def send_menu(recipient_id, redis_data, category_slug='main'):
    access_token = redis_data.hget('bot', 'access_token')
    menu_category = f'menu_{category_slug}'
    menu = json.loads(redis_data.get('menu'))[menu_category]
    send_ring_gallery(recipient_id, access_token, menu)


def get_cart_main_element(total_price):
    logo_url = 'https://postium.ru/wp-content/uploads/2018/08/idealnaya-korzina-internet-magazina-1068x713.jpg'

    element = {
        "title": f"Ваш заказ на сумму {total_price}",
        "image_url": logo_url,
        "buttons": []
    }
    buttons = (
        ('Самовывоз', 'pickup'),
        ('Доставка', 'delivery'),
        ('К меню', 'menu')
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


def get_empty_cart_main_element():
    logo_url = 'https://postium.ru/wp-content/uploads/2018/08/idealnaya-korzina-internet-magazina-1068x713.jpg'

    element = {
        "title": f"Ваша корзина пуста :c",
        "image_url": logo_url,
        "buttons": [
            {
                "type": "postback",
                "title": "К меню",
                "payload": "menu"
            }
        ]
    }
    return element


def generate_cart_menu_elements(cart_items):
    elements = []
    for item in cart_items:
        cart_element = {
            "title": f"{item['name']} ({item['quantity']} шт.)",
            "subtitle": item['description'],
            "buttons": [
                {
                    "type": "postback",
                    "title": "Добавить еще одну",
                    "payload": f"add_{item['product_id']}"
                },
                {
                    "type": "postback",
                    "title": "Убрать из корзины",
                    "payload": f"delete_{item['id']}"
                }
            ]
        }
        if main_image_url := item.get('image_url'):
            cart_element.update({
                "image_url": main_image_url
            })
        elements.append(cart_element)
    return elements


def send_cart_description(recipient_id, redis_data, cart):
    access_token = redis_data.hget('bot', 'access_token')
    cart_items = cart['cart_description']
    if not cart_items:
        main_element = get_empty_cart_main_element()
    else:
        main_element = get_cart_main_element(cart['total_price'])
    products_elements = generate_cart_menu_elements(cart_items)
    cart_description = [main_element, *products_elements]

    send_ring_gallery(recipient_id, access_token, cart_description)


def send_ring_gallery(recipient_id, access_token, elements):
    url = "https://graph.facebook.com/v2.6/me/messages"
    params = {"access_token": access_token}
    headers = {"Content-Type": "application/json"}
    request_content = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements
                }
            }
        }
    })
    response = requests.post(url, params=params, headers=headers,
                             data=request_content)
    response.raise_for_status()


def send_message(recipient_id, redis_data, message_text):
    url = "https://graph.facebook.com/v2.6/me/messages"
    access_token = redis_data.hget('bot', 'access_token')

    params = {"access_token": access_token}
    headers = {"Content-Type": "application/json"}
    request_content = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    response = requests.post(url, params=params, headers=headers,
                             data=request_content)
    response.raise_for_status()
