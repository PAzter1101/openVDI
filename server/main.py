###
import trio
from time import sleep
from worker import Worker
worker = Worker()

async def _main():
    while True:
        await worker.add_to_domain(provider="pve", provider_id="40123")
        print("sleep 5 sec")
        sleep(5)

trio.run(_main)
print("exit 5 sec")
sleep(5)
exit()
###
 
import trio
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

trio.run(main)
