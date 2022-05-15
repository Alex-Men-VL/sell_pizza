import requests

from facebook_lib import (
    send_menu,
    send_cart_description,
    send_message
)
from moltin_api import (
    get_cart_items,
    get_or_create_cart,
    add_cart_item,
    remove_cart_item
)
from moltin_cart_parser import parse_cart


def handle_users_reply(sender_id, messaging_event, redis_data):
    states_functions = {
        'START': handle_start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_CART': handle_cart,
    }
    user = f'fb_id_{sender_id}'

    if not redis_data.exists(user):
        user_state = 'START'
        mapping = {
            'state': user_state,
            'reply': ''
        }
        redis_data.hset(user, mapping=mapping)
    elif not (user_state := redis_data.hget(user, 'state')):
        user_state = 'START'

    if message := messaging_event.get("message"):
        user_reply = message['text']
    elif postback := messaging_event.get("postback"):
        user_reply = postback['payload']
    else:
        return

    redis_data.hset(user, 'reply', user_reply)

    state_handler = states_functions[user_state]
    next_state = state_handler(sender_id, redis_data)
    redis_data.hset(user, 'state', next_state)


def handle_start(sender_id, redis_data):
    send_menu(sender_id, redis_data)
    return 'HANDLE_MENU'


def handle_menu(sender_id, redis_data):
    user = f'fb_id_{sender_id}'
    moltin_token = redis_data.hget('bot', 'moltin_token')
    user_reply = redis_data.hget(user, 'reply')

    if user_reply.startswith('slug_'):
        category = user_reply.replace('slug_', '')
        send_menu(sender_id, redis_data, category)
    elif user_reply == 'cart':
        user_cart = get_cart_items(moltin_token, sender_id)
        cart_description = parse_cart(user_cart)
        send_cart_description(sender_id, redis_data, cart_description)
        return 'HANDLE_CART'
    elif user_reply.startswith('product_'):
        product_id = user_reply.replace('product_', '')
        user_cart = get_or_create_cart(moltin_token, sender_id)
        try:
            add_cart_item(moltin_token, user_cart['data']['id'],
                          product_id, item_quantity=1)
        except requests.exceptions.HTTPError:
            message = 'К сожалению, не удалось добавить товар :c'
        else:
            message = 'Пицца добавлена в корзину!'
        send_message(sender_id, redis_data, message)
    elif user_reply == 'promo' or user_reply == 'pay':
        message = 'Данная функция еще не доступна :c'
        send_message(sender_id, redis_data, message)
    else:
        message = 'Я вас не понимаю :c'
        send_message(sender_id, redis_data, message)
    return 'HANDLE_MENU'


def handle_cart(sender_id, redis_data):
    user = f'fb_id_{sender_id}'
    moltin_token = redis_data.hget('bot', 'moltin_token')
    user_reply = redis_data.hget(user, 'reply')

    if user_reply.startswith('add_'):
        product_id = user_reply.replace('add_', '')
        try:
            add_cart_item(moltin_token, sender_id,
                          product_id, item_quantity=1)
        except requests.exceptions.HTTPError:
            message = 'К сожалению, не удалось добавить товар :c'
            send_message(sender_id, redis_data, message)
        else:
            user_cart = get_cart_items(moltin_token, sender_id)
            cart_description = parse_cart(user_cart)
            send_cart_description(sender_id, redis_data, cart_description)
    elif user_reply.startswith('delete_'):
        product_id = user_reply.replace('delete_', '')
        item_removed = remove_cart_item(moltin_token, sender_id, product_id)
        if not item_removed:
            message = 'К сожалению, товар не был удален :c'
            send_message(sender_id, redis_data, message)
            return 'HANDLE_CART'
        user_cart = get_cart_items(moltin_token, sender_id)
        cart_description = parse_cart(user_cart)
        send_cart_description(sender_id, redis_data, cart_description)
    elif user_reply == 'menu':
        send_menu(sender_id, redis_data)
        return 'HANDLE_MENU'
    elif user_reply == 'pickup' or user_reply == 'delivery':
        message = 'Данная функция еще не доступна :c'
        send_message(sender_id, redis_data, message)
    else:
        message = 'Я вас не понимаю :c'
        send_message(sender_id, redis_data, message)

    return 'HANDLE_CART'
