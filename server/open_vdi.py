from typing import List
from providers.provider import Provider
from guaca import Guaca
from trio import sleep
from config import settings as s

# count_active_session
        #     count_connected_vdi
        #         count_runned_vdi
        #             count_stopped_vdi

class OpenVDI():
    def __init__(self, providers : List[Provider], guaca : Guaca):
        self.providers = providers
        self.guaca = guaca
        
    async def start(self):
        await self.state_update()

        for provider in self.providers:
            if len(await provider.get_vdi_by_status(status="running")) == 0:
                await provider.run_vdi(1)

        while True:
            await self.state_update()
            await self.status_upgrade()
            await self.buffers_upgrade()

            await sleep(s.UPDATE_PERIOD)

    async def state_update(self):
        vdi_ip_list = []
        for provider in self.providers:
            await provider.update_state()

            for vdi in provider.vdi_list:
                if "ip" in vdi and vdi["ip"] != None:
                    vdi_ip_list.append(vdi["ip"])
        
        self.connections = self.guaca.get_connections()
        ip_connections = []
        for connection in self.connections:
            ip_connections.append(connection['name'])

        ip_connection_for_remove_list = set(ip_connections) - set(vdi_ip_list)
        if len(ip_connection_for_remove_list) > 0:
            for ip in ip_connection_for_remove_list:
                for connection in self.connections:
                    if ip == connection['name']:
                        self.guaca.del_connection(id=connection["identifier"])

        ip_connection_for_adding_list = set(vdi_ip_list) - set(ip_connections)
        if len(ip_connection_for_adding_list) > 0:
            for ip in ip_connection_for_adding_list:
                self.guaca.add_connection(ip)
            
    async def status_upgrade(self):
        for provider in self.providers:
            await provider.upgrade_status()
            
            provider_runned_vdi_count = len(await provider.get_vdi_by_status(status="running"))
            if provider_runned_vdi_count < s.MIN_RUNNED_VDI:
                await provider.run_vdi(s.MIN_RUNNED_VDI - provider_runned_vdi_count)

    async def buffers_upgrade(self):
        # count_active_session
        #     count_connected_vdi
        #         count_runned_vdi
        #             count_stopped_vdi
        not_connected_vdi_count = await self.guaca.get_count_not_connected_vdi()
        runned_vdi_count = 0
        for provider in self.providers:
            runned_vdi_count += len(await provider.get_vdi_by_status(status="running"))
        if not_connected_vdi_count < s.BUFFER_RV:
            if runned_vdi_count < s.MAX_VDI:
                for provider in self.providers:
                    await provider.run_vdi(s.BUFFER_RV - not_connected_vdi_count)
        elif not_connected_vdi_count > s.BUFFER_RV:
            if runned_vdi_count > s.MIN_RUNNED_VDI:
                for provider in self.providers:
                    await provider.stop_vdi(count=(not_connected_vdi_count - s.BUFFER_RV),
                                            except_ip=await self.guaca.get_active_connection_ip_list())

        vdi_count = await provider.get_count_vdi()
        stopped_vdi_count = vdi_count - len(await provider.get_vdi_by_status(status="running"))
        if stopped_vdi_count < s.BUFFER_SV:
            if vdi_count < s.MAX_VDI:
                new_count_vdi = vdi_count + (s.BUFFER_SV - stopped_vdi_count)
                for provider in self.providers:
                    await provider.set_count_vdi(new_count_vdi)
        elif stopped_vdi_count > s.BUFFER_SV:
            new_count_vdi = vdi_count - (stopped_vdi_count - s.BUFFER_SV)
            if new_count_vdi >= s.MIN_VDI:
                for provider in self.providers:
                    await provider.set_count_vdi(new_count_vdi)

