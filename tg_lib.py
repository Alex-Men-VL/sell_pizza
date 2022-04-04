from textwrap import dedent

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from moltin_api import get_products, get_product_main_image_url


def get_products_menu(moltin_token):
    products = get_products(moltin_token)
    parsed_products = {
        product['name']: product['id'] for product in products['data']
    }
    extra_buttons = {
        'Корзина': 'cart',
    }
    current_buttons = {**parsed_products, **extra_buttons}
    keyboard = []
    for button_name, button_id in current_buttons.items():
        keyboard.append(
            [InlineKeyboardButton(text=button_name, callback_data=button_id)]
        )

    return InlineKeyboardMarkup(keyboard)


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
            message += f'''
            {item['name']}
            {item['description']}
            {item['quantity']} пицц в корзине на сумму {item['value_price']}

            '''
            buttons.append([
                InlineKeyboardButton(
                    text=f'Убрать из корзины {item["name"]}',
                    callback_data=item['id']
                )
            ])
        message += f'К оплате: {cart_description["total_price"]}'
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
                                  reply_markup=reply_markup)


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


def send_main_menu(context, chat_id, message_id):
    reply_markup = context.user_data['reply_markup']
    context.bot.send_message(text='Please choose:',
                             chat_id=chat_id,
                             reply_markup=reply_markup)
    context.bot.delete_message(chat_id=chat_id,
                               message_id=message_id)
