import redis


def get_redis_connection(redis_uri, redis_port, redis_password):
    connection = redis.Redis(
        host=redis_uri,
        port=redis_port,
        password=redis_password,
        decode_responses=True,
    )
    if connection.ping():
        return connection


def handle_new_bot_connection(redis_data, access_token, moltin_token,
                              token_expiration):
    mapping = {
        'access_token': access_token,
        'moltin_token': moltin_token,
        'token_expiration': token_expiration,
    }
    redis_data.hset('bot', mapping=mapping)


def handle_new_user(user, redis_data):
    mapping = {
        'state': 'START',
        'reply': ''
    }
    redis_data.hset(user, mapping=mapping)
