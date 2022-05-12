import redis

_database = None


def get_redis_connection(redis_uri, redis_port, redis_password):
    global _database

    if not _database:
        connection = redis.Redis(
            host=redis_uri,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
        )
        if not connection.ping():
            return
        _database = connection
    return _database
