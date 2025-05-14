import trio
from providers.pve import PVE
from guaca import Guaca
from open_vdi import OpenVDI

proxmox = PVE()
guaca = Guaca()

async def main():
    await proxmox._init()
    open_vdi = OpenVDI(providers=[proxmox], guaca=guaca)
    await open_vdi.start()

trio.run(main)
