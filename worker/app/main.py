import asyncio
from faststream import FastStream, Logger
from faststream.redis import RedisBroker
from schemas.tasks import WorkerTask


broker = RedisBroker("redis://127.0.0.1:6379")
app = FastStream(broker)

@broker.subscriber(stream="to_worker")
async def handle(task: WorkerTask, logger: Logger):
    print(task)
    logger.info(task)
    logger.info(task.type)
    logger.info(task.data)

async def main():
    await app.run()

asyncio.run(main())
