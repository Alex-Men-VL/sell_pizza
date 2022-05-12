import logging
import os
from datetime import datetime

from flask import Flask, request
from environs import Env

from facebook_bot import handle_users_reply
from moltin_api import (
    get_access_token
)
from redis_db import get_redis_connection

logger = logging.getLogger(__file__)
app = Flask(__name__)
env = Env()
env.read_env()


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
    redis_uri = env.str('REDIS_URL')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')
    redis_connection = get_redis_connection(redis_uri, redis_port,
                                            redis_password)

    current_time = datetime.timestamp(datetime.now())
    if redis_connection.hget('bot', 'token_expiration') < str(current_time):
        client_id = env.str('CLIENT_ID')
        client_secret = env.str('CLIENT_SECRET')
        moltin_token = get_access_token(client_id, client_secret)
        redis_connection.hset(
            'bot',
            mapping={'moltin_token': moltin_token['access_token'],
                     'token_expiration': moltin_token['expires']}
        )

    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                sender_id = messaging_event["sender"]["id"]  # the facebook ID of the person sending you the message
                recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                handle_users_reply(sender_id, messaging_event,
                                   redis_connection)
    return "ok", 200


def main():
    logging.basicConfig(level=logging.INFO)

    client_id = env.str('CLIENT_ID')
    client_secret = env.str('CLIENT_SECRET')
    redis_uri = env.str('REDIS_URL')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')
    access_token = env.str('PAGE_ACCESS_TOKEN')

    redis_connection = get_redis_connection(redis_uri, redis_port,
                                            redis_password)

    moltin_token = get_access_token(client_id, client_secret)
    mapping = {
        'access_token': access_token,
        'moltin_token': moltin_token['access_token'],
        'token_expiration': moltin_token['expires'],
    }
    redis_connection.hset('bot', mapping=mapping)

    logger.info('Facebook бот запущен.')
    app.run(debug=True)


if __name__ == '__main__':
    main()
