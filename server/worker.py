from faststream.redis import RedisBroker
from schemas.tasks import WorkerTask

broker = RedisBroker("redis://127.0.0.1:6379")
prepared_publisher = broker.publisher("to_worker")

class Worker():
    async def _init(self):
        await broker.connect()

    async def add_to_domain(self, provider: str, provider_id: str):

        print("Sending message to worker...")

        task = WorkerTask(
            type="add_to_domain",
            data={
                "provider": provider,
                "provider_id": provider_id,
            },
        )

        print(task.type)
        print(task.data)
        await prepared_publisher.publish("task")
