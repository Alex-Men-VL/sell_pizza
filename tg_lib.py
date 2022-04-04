from textwrap import dedent

from more_itertools import chunked
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.utils.helpers import escape_markdown

from moltin_api import get_product_main_image_url, get_products


def get_products_menu(products, page):
    parsed_products = {
        product['name']: product['id'] for product in products[page - 1]
    }
    keyboard = []
    for button_name, button_id in parsed_products.items():
        keyboard.append(
            [InlineKeyboardButton(text=button_name, callback_data=button_id)]
        )
    max_page_number = len(products)
    previous_page_number = page - 1
    previous_page_alias = 'Предыдущая страница'
    next_page_number = page + 1
    next_page_alias = 'Следующая страница'
    if page == 1:
        previous_page_number = max_page_number
        previous_page_alias = 'На последнюю страницу'
    elif page == max_page_number:
        next_page_number = 1
        next_page_alias = 'На первую страницу'

    keyboard.append(
        [
            InlineKeyboardButton(text=previous_page_alias,
                                 callback_data=previous_page_number),
            InlineKeyboardButton(text='Корзина', callback_data='cart'),
            InlineKeyboardButton(text=next_page_alias,
                                 callback_data=next_page_number)
        ]
    )
    return InlineKeyboardMarkup(keyboard)


def get_paginated_products(products):
    products_count_per_page = 8
    products_per_page = list(chunked(products, products_count_per_page))
    return products_per_page


def parse_cart(cart):
    total_price = cart['meta']['display_price']['with_tax']['formatted']
    cart_description = []

    for cart_item in cart['data']:
        item_id = cart_item['id']
        item_name = cart_item['name']
        item_description = cart_item['description']
        item_quantity = cart_item['quantity']
        item_price = cart_item['meta']['display_price']['with_tax']
        item_unit_price = item_price['unit']['formatted']
        item_value_price = item_price['value']['formatted']

        cart_item_description = {
            'id': item_id,
            'name': item_name,
            'description': item_description,
            'quantity': item_quantity,
            'unit_price': item_unit_price,
            'value_price': item_value_price
        }
        cart_description.append(cart_item_description)
    return {
        'total_price': total_price,
        'cart_description': cart_description
    }


def send_cart_description(context, cart_description):
    cart_items = cart_description['cart_description']
    if not cart_items:
        message = 'Корзина пуста'
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text='Назад', callback_data='menu')]]
        )
    else:
        message = ''
        buttons = []
        for item in cart_items:
            name = escape_markdown(item['name'], version=2)
            description = escape_markdown(item['description'], version=2)
            value_price = escape_markdown(item['value_price'], version=2)

            message += f'''
            *{name}*
            _{description}_
            {item['quantity']} пицц в корзине на сумму {value_price}

            '''
            buttons.append([
                InlineKeyboardButton(
                    text=f'Убрать из корзины {item["name"]}',
                    callback_data=item['id']
                )
            ])
        total_price = escape_markdown(cart_description["total_price"],
                                      version=2)
        message += f'*К оплате: {total_price}*'
        buttons.append(
            [InlineKeyboardButton(text='Оплатить', callback_data='pay')]
        )
        buttons.append(
            [InlineKeyboardButton(text='В меню', callback_data='menu')]
        )
        reply_markup = InlineKeyboardMarkup(buttons)

    chat_id = context.user_data['chat_id']
    message_id = context.user_data['message_id']
    context.bot.edit_message_text(text=dedent(message),
                                  chat_id=chat_id,
                                  message_id=message_id,
                                  reply_markup=reply_markup,
                                  parse_mode=ParseMode.MARKDOWN_V2)


def send_product_description(context, product_description):
    message = f'''\
    {product_description['name']}

    Стоимость: {product_description['price']} руб.

    {product_description['description']}
    '''
    chat_id = context.user_data['chat_id']
    message_id = context.user_data['message_id']

    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text='Положить в корзину',
                                  callback_data='add')],

            [InlineKeyboardButton(text='В меню', callback_data='menu')]
        ]
    )

    if image_id := product_description['image_id']:
        context.bot.send_chat_action(chat_id=chat_id,
                                     action='typing')

        moltin_token = context.bot_data['moltin_token']
        img_url = get_product_main_image_url(moltin_token, image_id)

        context.bot.send_photo(chat_id=chat_id,
                               photo=img_url,
                               caption=dedent(message),
                               reply_markup=reply_markup)
        context.bot.delete_message(chat_id=chat_id,
                                   message_id=message_id)
    else:
        context.bot.edit_message_text(text=dedent(message),
                                      chat_id=chat_id,
                                      message_id=message_id,
                                      reply_markup=reply_markup)


def send_main_menu(context, chat_id, message_id, moltin_token, page):
    products = get_products(moltin_token)['data']
    paginated_products = get_paginated_products(products)

    reply_markup = get_products_menu(paginated_products, page)
    context.bot.send_message(text='Please choose:',
                             chat_id=chat_id,
                             reply_markup=reply_markup)
    context.bot.delete_message(chat_id=chat_id,
                               message_id=message_id)
