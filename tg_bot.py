import logging
import re
from datetime import datetime
from textwrap import dedent

import requests
from environs import Env
from telegram import (
    Bot, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
)
from telegram.ext import (
    Updater,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    Filters,
    PicklePersistence, PreCheckoutQueryHandler
)

from logs_handler import TelegramLogsHandler
from moltin_api import (
    get_access_token,
    get_product,
    get_or_create_cart,
    add_cart_item,
    get_cart_items,
    remove_cart_item,
    create_customer, delete_cart
)
from tg_lib import (
    parse_cart,
    send_cart_description,
    send_product_description,
    send_main_menu,
    fetch_coordinates,
    get_nearest_restaurant,
    get_available_restaurants,
    send_delivery_option,
    save_delivery_address_in_moltin, send_order_reminder, send_payment_invoice,
    generate_payment_payload,
)

logger = logging.getLogger(__file__)


def handle_start(update, context):
    chat_id = context.user_data['chat_id']
    message_id = context.user_data['message_id']
    moltin_token = context.bot_data['moltin_token']
    send_main_menu(context, chat_id, message_id, moltin_token, page=1)
    context.user_data['current_page'] = 1
    return 'HANDLE_MENU'


def handle_menu(update, context):
    chat_id = context.user_data['chat_id']
    message_id = context.user_data['message_id']
    user_reply = context.user_data['user_reply']
    moltin_token = context.bot_data['moltin_token']

    if user_reply == 'cart':
        user_cart = get_cart_items(moltin_token, chat_id)
        cart_description = parse_cart(user_cart)
        send_cart_description(context, cart_description)
        return 'HANDLE_CART'
    elif user_reply.isdigit():
        page = int(user_reply)
        context.user_data['current_page'] = page
        send_main_menu(context, chat_id, message_id, moltin_token,
                       page=page)
        return 'HANDLE_MENU'

    context.user_data['product_id'] = user_reply

    product = get_product(moltin_token, user_reply)
    product_main_image = product['data']['relationships'].get('main_image')

    product_description = {
        'name': product['data']['name'],
        'description': product['data']['description'],
        'price': product['data']['meta']['display_price']['with_tax'][
            'formatted'
        ],
        'image_id': product_main_image['data']['id'] if product_main_image
        else ''
    }

    send_product_description(context, product_description)
    return 'HANDLE_DESCRIPTION'


def handle_description(update, context):
    chat_id = context.user_data['chat_id']
    message_id = context.user_data['message_id']
    moltin_token = context.bot_data['moltin_token']
    product_id = context.user_data['product_id']
    user_reply = context.user_data['user_reply']

    if user_reply == 'menu':
        current_page = context.user_data['current_page']
        send_main_menu(context, chat_id, message_id, moltin_token,
                       page=current_page)
        return 'HANDLE_MENU'
    elif user_reply == 'add':
        user_cart = get_or_create_cart(moltin_token, chat_id)
        try:
            add_cart_item(moltin_token, user_cart['data']['id'],
                          product_id, item_quantity=1)
        except requests.exceptions.HTTPError:
            context.bot.answer_callback_query(
                callback_query_id=update.callback_query.id,
                text='Не удалось добавить товар в корзину'
            )
        else:
            context.bot.answer_callback_query(
                callback_query_id=update.callback_query.id,
                text='Товар добавлен в корзину'
            )
    return 'HANDLE_DESCRIPTION'


def handle_cart(update, context):
    chat_id = context.user_data['chat_id']
    message_id = context.user_data['message_id']
    user_reply = context.user_data['user_reply']
    moltin_token = context.bot_data['moltin_token']

    if user_reply == 'menu':
        current_page = context.user_data['current_page']
        send_main_menu(context, chat_id, message_id, moltin_token,
                       page=current_page)
        return 'HANDLE_MENU'
    elif user_reply == 'pay':
        if context.bot_data['customers'].get(chat_id):
            message = 'Пришлите нам ваш адрес текстом или геолокацию.'
            context.bot.send_message(text=message,
                                     chat_id=chat_id)
            context.bot.delete_message(chat_id=chat_id,
                                       message_id=message_id)
            return 'HANDLE_LOCATION'

        message = 'Пожалуйста, напишите свою почту для связи с вами'
        context.bot.send_message(text=message,
                                 chat_id=chat_id)
        context.bot.delete_message(chat_id=chat_id,
                                   message_id=message_id)
        return 'WAITING_EMAIL'

    item_removed = remove_cart_item(moltin_token, chat_id, user_reply)
    if item_removed:
        context.bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text='Товар удален из корзины'
        )
        user_cart = get_cart_items(moltin_token, chat_id)
        cart_description = parse_cart(user_cart)
        send_cart_description(context, cart_description)
    else:
        context.bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text='Товар не может быть удален из корзины'
        )
    return 'HANDLE_CART'


def handle_email(update, context):
    chat_id = context.user_data['chat_id']
    user_email = context.user_data['user_reply']
    moltin_token = context.bot_data['moltin_token']

    email_pattern = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'
    if not re.fullmatch(email_pattern, user_email):
        message = 'Почта указана не верно. Отправьте почту еще раз.'
        update.message.reply_text(text=message)
        return 'WAITING_EMAIL'

    if not context.bot_data.get('customers'):
        context.bot_data['customers'] = {}

    if not context.bot_data['customers'].get(chat_id):
        customer = create_customer(moltin_token, user_email)
        context.bot_data['customers'][chat_id] = customer['data']['id']
    message = f'''
    Вы ввели эту почту: {user_email}
    
    Пришлите нам ваш адрес текстом или геолокацию.'''
    update.message.reply_text(text=dedent(message))
    return 'HANDLE_LOCATION'


def handle_location(update, context):
    user_location = context.user_data['user_reply']
    moltin_token = context.bot_data['moltin_token']

    try:
        coordinates = user_location.longitude, user_location.latitude
    except AttributeError:
        yandex_api_key = context.bot_data['yandex_api_key']
        coordinates = fetch_coordinates(user_location, yandex_api_key)
    if not coordinates:
        update.message.reply_text(
            text='Не могу распознать этот адрес, повторите попытку.'
        )
        return 'HANDLE_LOCATION'

    available_restaurants = get_available_restaurants(moltin_token)
    nearest_restaurant = get_nearest_restaurant(coordinates,
                                                available_restaurants)
    context.user_data.update(
        {
            'nearest_restaurant': nearest_restaurant,
            'delivery_coordinates': coordinates
        }
    )
    save_delivery_address_in_moltin(moltin_token, coordinates)
    send_delivery_option(update, nearest_restaurant)
    return 'HANDLE_DELIVERY'


def handle_delivery(update, context):
    chat_id = context.user_data['chat_id']
    user_reply = context.user_data['user_reply']
    moltin_token = context.bot_data['moltin_token']

    user_cart = get_cart_items(moltin_token, chat_id)
    cart_description = parse_cart(user_cart)
    context.user_data['cart_price'] = cart_description['total_price']
    nearest_restaurant = context.user_data['nearest_restaurant']

    if user_reply == 'pickup':
        message = '''
        Вы выбрали самовывоз.
        
        Ваш заказ:'''
        context.bot.send_message(
            chat_id=chat_id,
            text=dedent(message)
        )
        send_cart_description(context, cart_description, with_keyboard=False)
        context.bot.send_message(
            chat_id=chat_id,
            text='Адрес пиццерии:'
        )
        context.bot.send_location(chat_id,
                                  latitude=nearest_restaurant['lat'],
                                  longitude=nearest_restaurant['lon'])
    elif user_reply == 'delivery':
        lon, lat = context.user_data['delivery_coordinates']
        courier_id = nearest_restaurant['courier_id']
        message = f'''
            Новый заказ!

            Из ресторана по адресу: {nearest_restaurant['address']}
            
            Содержимое заказа:'''
        context.bot.send_message(chat_id=courier_id,
                                 text=dedent(message))
        send_cart_description(context, cart_description, with_keyboard=False,
                              chat_id=courier_id)
        context.bot.send_message(
            chat_id=courier_id,
            text='Адрес заказа:'
        )
        context.bot.send_location(chat_id=courier_id,
                                  latitude=lat,
                                  longitude=lon)

        context.bot.send_message(
            chat_id=chat_id,
            text='Спасибо за заказ! Ожидайте доставки'
        )
        context.job_queue.run_once(send_order_reminder, 3600, context=chat_id)
    else:
        return 'HANDLE_DELIVERY'

    button = [
        [InlineKeyboardButton(text='Оплатить', callback_data='pay_now')]
    ]
    context.bot.send_message(
        chat_id=chat_id,
        text='Для оплаты нажмите кнопку *Оплатить*',
        reply_markup=InlineKeyboardMarkup(button),
        parse_mode=ParseMode.MARKDOWN_V2
    )

    return 'HANDLE_PAYMENT'


def handle_payment(update, context):
    chat_id = context.user_data['chat_id']
    message_id = context.user_data['message_id']
    user_reply = context.user_data['user_reply']

    if user_reply != 'pay_now':
        return 'HANDLE_PAYMENT'

    provider_token = context.bot_data['provider_token']
    cart_price = context.user_data['cart_price']
    payload = generate_payment_payload(update)
    send_payment_invoice(context, chat_id, provider_token, cart_price,
                         payload=payload)
    context.user_data['payload'] = payload
    context.bot.delete_message(chat_id=chat_id,
                               message_id=message_id)


def precheckout_callback(update, context):
    query = update.pre_checkout_query
    payload = context.user_data['payload']
    if query.invoice_payload != payload:
        query.answer(ok=False, error_message="Что-то пошло не так...")
    else:
        query.answer(ok=True)


def successful_payment_callback(update, context):
    chat_id = update.message.chat_id
    moltin_token = context.bot_data['moltin_token']

    update.message.reply_text('Оплата прошла успешно')
    delete_cart(moltin_token, chat_id)


def handle_users_reply(update, context):
    if message := update.message:
        user_reply = message.text if message.text else message.location
        chat_id = message.chat_id
        message_id = message.message_id
    elif query := update.callback_query:
        user_reply = query.data
        chat_id = query.message.chat_id
        message_id = query.message.message_id
    else:
        return

    context.user_data.update(
        {
            'user_reply': user_reply,
            'chat_id': chat_id,
            'message_id': message_id
        }
    )

    if (not (token_expiration := context.bot_data.get('token_expiration')) or
            token_expiration <= datetime.timestamp(datetime.now())):
        moltin_access_token = get_access_token(
            context.bot_data['client_id'],
            context.bot_data['client_secret']
        )
        context.bot_data.update(
            {
                'moltin_token': moltin_access_token['access_token'],
                'token_expiration': moltin_access_token['expires'],
            }
        )

    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = context.user_data['state']

    states_functions = {
        'START': handle_start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': handle_email,
        'HANDLE_LOCATION': handle_location,
        'HANDLE_DELIVERY': handle_delivery,
        'HANDLE_PAYMENT': handle_payment
    }
    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(update, context)
        context.user_data['state'] = next_state
    except Exception as err:
        logger.error(err)


def main():
    env = Env()
    env.read_env()

    logging.basicConfig(level=logging.INFO)

    bot_token = env.str('TG_BOT_TOKEN')
    dev_bot_token = env.str('TG_DEV_BOT_TOKEN')
    tg_dev_chat_id = env.str('TG_DEV_CHAT_ID')
    client_id = env.str('CLIENT_ID')
    client_secret = env.str('CLIENT_SECRET')
    yandex_api_key = env.str('YANDEX_API_KEY')
    provider_token = env.str('PAYMENT_PROVIDER_TOKEN')

    dev_bot = Bot(token=dev_bot_token)
    tg_logger = TelegramLogsHandler(dev_bot, tg_dev_chat_id)
    logger.addHandler(tg_logger)

    persistence = PicklePersistence(filename='tg_bot.pickle')

    updater = Updater(token=bot_token, persistence=persistence)
    logger.info('Бот запущен')

    updater.dispatcher.add_handler(
        CallbackQueryHandler(handle_users_reply)
    )
    updater.dispatcher.add_handler(
        MessageHandler(Filters.text | Filters.location, handle_users_reply)
    )
    updater.dispatcher.add_handler(
        CommandHandler('start', handle_users_reply)
    )
    updater.dispatcher.add_handler(
        PreCheckoutQueryHandler(precheckout_callback)
    )
    updater.dispatcher.add_handler(
        MessageHandler(Filters.successful_payment,
                       successful_payment_callback))

    updater.dispatcher.bot_data.update(
        {
            'client_id': client_id,
            'client_secret': client_secret,
            'yandex_api_key': yandex_api_key,
            'provider_token': provider_token
        }
    )
    updater.dispatcher.bot.delete_my_commands()
    updater.dispatcher.bot.set_my_commands(
        language_code='ru',
        commands=[BotCommand('start', 'Перейти в меню')]
    )

    try:
        updater.start_polling()
        updater.idle()
    except Exception as err:
        logger.error(err)


if __name__ == '__main__':
    main()
