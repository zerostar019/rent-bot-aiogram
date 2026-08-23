from redis.asyncio import Redis

from config import env

redis = Redis(
    host=env.REDIS_HOST,
    port=env.REDIS_PORT,
    password=(
        env.REDIS_PASSWORD.get_secret_value() if env.REDIS_PASSWORD is not None else None
    ),
    decode_responses=True,
    max_connections=50,
    health_check_interval=30,
    socket_keepalive=True,
    socket_connect_timeout=5,
    retry_on_timeout=True,
)
