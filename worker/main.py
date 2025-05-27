from faststream import FastStream
from faststream.redis import RedisBroker

broker = RedisBroker("redis://redis:6379")
app = FastStream(broker)

print("start")
@broker.subscriber("to-workers")
async def handle_msg(task: str):
    print(task)

print("stop")
