import json
import os

import requests
from flask import Flask, request

from moltin_api import get_products, get_access_token, \
    get_product_main_image_url

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    """
    При верификации вебхука у Facebook он отправит запрос на этот адрес. На него нужно ответить VERIFY_TOKEN.
    """
    verify_token = os.environ["VERIFY_TOKEN"]
    if (request.args.get("hub.mode") == "subscribe"
            and request.args.get("hub.challenge")):
        if not request.args.get("hub.verify_token") == verify_token:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():
    """
    Основной вебхук, на который будут приходить сообщения от Facebook.
    """
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):  # someone sent us a message
                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text
                    # send_message(sender_id, message_text)
                    send_menu(sender_id)
    return "ok", 200


def send_message(recipient_id, message_text):
    url = "https://graph.facebook.com/v2.6/me/messages"
    access_token = os.environ["PAGE_ACCESS_TOKEN"]
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


def generate_menu_elements(moltin_token, product_per_page=5):
    main_element = get_main_menu_element()
    elements = [main_element]
    products = get_products(moltin_token)['data']
    for product in products[:product_per_page]:
        price = product['meta']['display_price']['with_tax']['formatted']
        menu_element = {
            "title": f"{product['name']} ({price} р.)",
            "subtitle": product['description'],
            "buttons": [
                {
                    "type": "postback",
                    "title": "Добавить в корзину",
                    "payload": "DEVELOPER_DEFINED_PAYLOAD"
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


def send_menu(recipient_id):
    url = "https://graph.facebook.com/v2.6/me/messages"
    access_token = os.environ["PAGE_ACCESS_TOKEN"]
    client_id = os.environ["CLIENT_ID"]
    client_secret = os.environ["CLIENT_SECRET"]
    moltin_token = get_access_token(
        client_id, client_secret
    )['access_token']

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
                "elements": generate_menu_elements(moltin_token)
              }
            }
          }
    })
    response = requests.post(url, params=params, headers=headers,
                             data=request_content)
    response.raise_for_status()


if __name__ == '__main__':
    app.run(debug=True)
