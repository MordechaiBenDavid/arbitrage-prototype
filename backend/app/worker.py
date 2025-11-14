from rq import Connection, Queue, Worker
from redis import Redis

from app.core.config import settings

redis = Redis.from_url(settings.redis_url)

def run_worker():
    with Connection(redis):
        worker = Worker([Queue("ingestion")])
        worker.work()


if __name__ == "__main__":
    run_worker()
