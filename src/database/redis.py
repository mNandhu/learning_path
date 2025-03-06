from redis import Redis, StrictRedis
import os

from dotenv import load_dotenv

load_dotenv()


def get_redis_client() -> Redis:
    """Direct Redis connection for workers"""
    return StrictRedis(
        host=os.getenv("REDIS_HOST"),
        port=os.getenv("REDIS_PORT"),
        db=os.getenv("REDIS_DB"),
        decode_responses=False,
    )
