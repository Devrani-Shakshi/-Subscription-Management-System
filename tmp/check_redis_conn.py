import redis
import os
from dotenv import load_dotenv

load_dotenv()

def check_redis():
    url = os.getenv("REDIS_URL")
    if not url:
        print("REDIS_URL not found in .env")
        return
    print(f"Connecting to {url}...")
    try:
        r = redis.from_url(url)
        r.ping()
        print("Successfully connected to Redis.")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")

if __name__ == "__main__":
    check_redis()
