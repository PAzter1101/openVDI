###
# # import trio
# import asyncio
# from faststream.redis import RedisBroker

# broker = RedisBroker("redis://127.0.0.1:6379")

# # @broker.publisher(stream="to_workers")
# async def add_to_domain(provider: str, provider_id: str) -> str:

#     print("Sending message to worker...")
#     msg = f"test to worker: {provider}, {provider_id}"
#     print(msg)
    
#     await broker.publish(msg, stream="to_worker")
#     # return msg

# async def _main():
#     await broker.connect()
#     while True:
#         await add_to_domain(provider="pve", provider_id="40123")
#         print("sleep 5 sec")
#         await asyncio.sleep(5)

# asyncio.run(_main())
# # trio.run(_main)
# exit()
###
 
import asyncio
from providers.pve import PVE
from guaca import Guaca
from open_vdi import OpenVDI

proxmox = PVE()
guaca = Guaca()

async def main():
    print("Initializing OpenVDI...")
    await proxmox._init()
    open_vdi = OpenVDI(providers=[proxmox], guaca=guaca)
    await open_vdi.start()

asyncio.run(main())
