from textwrap import dedent

from more_itertools import chunked
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    LabeledPrice
)
from telegram.utils.helpers import escape_markdown

from moltin_api import (
    get_product_main_image_url,
    get_products
)


def send_main_menu(context, chat_id, message_id, moltin_token, page,
                   quantity_per_page=8):
    products = get_products(moltin_token)['data']
    products_per_page = list(chunked(products, quantity_per_page))

    reply_markup = get_products_menu(products_per_page, page)
    context.bot.send_message(text='Пожалуйста, выберите товар:',
                             chat_id=chat_id,
                             reply_markup=reply_markup)
    context.bot.delete_message(chat_id=chat_id,
                               message_id=message_id)


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
    next_page_number = page + 1
    if page == 1:
        previous_page_number = max_page_number
    elif page == max_page_number:
        next_page_number = 1

    keyboard.append(
        [
            InlineKeyboardButton(text='◀',
                                 callback_data=previous_page_number),
            InlineKeyboardButton(text='Корзина', callback_data='cart'),
            InlineKeyboardButton(text='▶',
                                 callback_data=next_page_number)
        ]
    )
    return InlineKeyboardMarkup(keyboard)


def send_cart_description(context, cart_description, with_keyboard=True,
                          chat_id=None):
    cart_items = cart_description['cart_description']
    if not cart_items:
        message = 'К сожалению, ваша корзина пуста :c'
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

    chat_id = chat_id if chat_id else context.user_data['chat_id']
    message_id = context.user_data['message_id']
    reply_markup = reply_markup if with_keyboard else None
    context.bot.send_message(chat_id=chat_id,
                             text=dedent(message),
                             reply_markup=reply_markup,
                             parse_mode=ParseMode.MARKDOWN_V2)
    context.bot.delete_message(chat_id=chat_id,
                               message_id=message_id)


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


def send_delivery_option(update, restaurant):
    distance = restaurant["distance_km"]
    if distance < 0.5:
        delivery = True
        message = f'''
        Может, заберете пиццу из нашей пиццерии неподалеку?
        Она всего в {'{:.0f}'.format(restaurant['distance_m'])} метрах от вас!
        Вот ее адрес: {restaurant['address']}.
        
        А можем и бесплатно доставить, нам не сложно c:'''
    elif distance < 5:
        delivery = True
        message = '''
        Похоже, придется ехать  к вам на самокате.
        Доставка будет стоить 100 руб.
        Доставляем или самовывоз?'''
    elif distance < 20:
        delivery = True
        message = '''
        Ближайшая пиццерия довольно далеко от вас.
        Доставка будет стоить 200 руб.
        Доставляем или самовывоз?'''
    else:
        delivery = False
        message = f'''
        Простите, но так далеко мы пиццу не доставим.
        Ближайшая пиццерия аж в {'{:.1f}'.format(distance)} километрах от вас!
        Будете заказывать самовывоз?'''

    buttons = [
        [InlineKeyboardButton(text='Самовывоз', callback_data='pickup')]
    ]

    if delivery:
        buttons.append(
            [InlineKeyboardButton(text='Доставка', callback_data='delivery')]
        )

    update.message.reply_text(text=dedent(message),
                              reply_markup=InlineKeyboardMarkup(buttons))


def send_order_reminder(context):
    message = '''
    *место для рекламы*
    *сообщение что делать если пицца не пришла*'''
    context.bot.send_message(chat_id=context.job.context,
                             text=dedent(message))


def generate_payment_payload(update):
    query = update.callback_query.message
    first_name = query.chat.first_name
    last_name = query.chat.last_name
    message_id = query.message_id
    return f'{first_name}-{last_name}-{message_id}'


def send_payment_invoice(context, chat_id, provider_token, price,
                         currency='RUB', payload='Custom-Payload',
                         description=None):
    title = 'Оплата пиццы'
    description = description if description else \
        'Здесь должно быть описание заказа'
    prices = [LabeledPrice('Pizza', int(float(price)) * 100)]

    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )
