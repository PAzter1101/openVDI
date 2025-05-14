import abc, uuid
from typing import List
from config import settings as s

class Provider(abc.ABC):
    def __init__(self):
        if s.MIN_VDI > s.MAX_VDI:
            raise "min_vdi > max_vdi"
        self.min_vdi = s.MIN_VDI
        self.max_vdi = s.MAX_VDI
        self.vdi_list = []

    async def _init(self):
        await self.upgrade_status()

    async def upgrade_status(self):
        current_count = await self.get_count_vdi()
        if current_count < self.min_vdi:
            await self.set_count_vdi(self.min_vdi)
        if current_count > self.max_vdi:
            await self.set_count_vdi(self.max_vdi)        

    @classmethod
    def create_VDI(): pass

    @classmethod
    def delete_vdi(): pass

    @classmethod
    def change_VDI(): pass

    @classmethod
    def migrate_VDI(): pass

    @classmethod
    async def set_count_vdi(count : int): pass

    @classmethod
    async def get_count_vdi() -> int: pass

    async def refresh_vdi_ip(self, provider : str, provider_id : str, ip : str):
        id = None
        for vdi in self.get_vdi_provider(provider=provider):
            if vdi["provider_id"] == provider_id:
                id = vdi["id"]
                break
        if id == None:
            return
        for vdi in self.vdi_list:
            if vdi["id"] == id:
                vdi["ip"] = ip
                return

    @classmethod
    async def update_state(): pass

    @classmethod
    async def get_vdi_by_status(status : str) -> List[dict]: pass

    @classmethod
    async def run_vdi(count : int = 1): pass

    @classmethod
    async def stop_vdi(count : int = 1, provider_id : str = None, except_ip : list[str] = None): pass

    def add_vdi(self, provider : str, provider_id : str):
        vdi = {"id": uuid.uuid4(),
               "provider": provider,
               "provider_id": provider_id,
               }
        self.vdi_list.append(vdi)

    def get_vdi_provider(self, provider : str) -> List:
        vdi_provider_list = []
        for vdi in self.vdi_list:
            if vdi["provider"] == provider:
                vdi_provider_list.append(vdi)
        return vdi_provider_list

    def del_vdi(self, id : uuid):
        for i in range(len(self.vdi_list)):
            if self.vdi_list[i]["id"] == id:
                del self.vdi_list[i]
                break
