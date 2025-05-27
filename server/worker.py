from faststream import FastStream
from faststream.redis import RedisBroker

broker = RedisBroker("redis://redis:6379")
app = FastStream(broker)

# @broker.subscriber("in-channel")
# @broker.publisher("out-channel")
# async def handle_msg(user: str, user_id: int) -> str:
#     return f"User: {user_id} - {user} registered"

class Worker():
    @broker.publisher("to-workers")
    async def add_to_domain(provider: str, provider_id: str) -> str:
        print("Отправка воркеру")
        return f"test to worker: {provider}, {provider_id}"
