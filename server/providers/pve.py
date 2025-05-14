from typing import List
from trio import sleep, move_on_after
from .provider import Provider
from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException
from config import settings as s

pve = ProxmoxAPI(
    s.PVE_HOST,
    user=s.PVE_USER,
    password=s.PVE_PASS,
    verify_ssl=False
)

pve_template_id = s.PVE_TEMPLATE_ID
pve_vdi_prefix = s.PVE_VDI_PREFIX * 1000

class PVE(Provider):
    def __init__(self):
        self.pve_vdi_list = []
        super().__init__()
        

    async def set_count_vdi(self, count : int):
        await super().set_count_vdi()

        current_count = await self.get_count_vdi()

        if current_count == count:
            return
        
        if current_count < count:
            for i in range(count - current_count):
                await self.create_VDI(balanced=False, pve_node="pve4")
            return
        
        if current_count > count:
            for i in range(current_count - count):
                await self.delete_vdi(force=True)
            return

    async def get_count_vdi(self) -> int:
        await self.update_state()
        return len(self.pve_vdi_list)

    async def create_VDI(self, balanced : bool = False, pve_node : str = None): 
        vdi_id_list = []
        for node in pve.nodes.get():
            for vm in pve.nodes(node["node"]).qemu.get():
                if 'tags' in vm and vm['tags'] == 'openvdi' and vm["vmid"] != pve_template_id:
                    vdi_id_list.append(vm["vmid"])
        
        vm_id = pve_vdi_prefix + 1
        while True:
            if vm_id in vdi_id_list:
                vm_id += 1
            else: 
                break

        if not balanced:
            pve.nodes(pve_node).qemu(pve_template_id).clone().post(
                newid=vm_id,
                name="test-" + str(vm_id),
            )

        else:
            #todo
            raise
            nodes = []
            for node in pve.nodes.get():
                nodes.append(node["node"])
        
        self.add_vdi(provider="pve", provider_id=str(vm_id))

    async def delete_vdi(self, vmid : int = None, force : bool = False):
        if vmid is None:
            time_creation = {}
            for vdi in self.pve_vdi_list:
                if vdi["status"] == "stopped":
                    config = pve.nodes(self.get_node_by_vmid(vdi["vmid"])).qemu(vdi["vmid"]).config.get()
                    time_creation[vdi["vmid"]] = config["meta"].split(",")[1].split("=")[1]
            if time_creation == {} and force:
                for vdi in self.pve_vdi_list:
                    config = pve.nodes(self.get_node_by_vmid(vdi["vmid"])).qemu(vdi["vmid"]).config.get()
                    time_creation[vdi["vmid"]] = config["meta"].split(",")[1].split("=")[1]
            if time_creation == {}:
                raise "Unable to delete VM: No VM with status stopped"
            vmid = min(time_creation, key=time_creation.get)

        await self.stop_vdi(provider_id=str(vmid))
        await sleep(1)
        pve.nodes(self.get_node_by_vmid(vmid)).qemu(vmid).delete()
        await self.update_state()

    async def pve_refresh_vdi_ip(self):
        for vdi in self.pve_vdi_list:
            if vdi["status"] == "running":
                with move_on_after(120):
                    ip = await self.get_ip(vdi["node"], vdi["vmid"])
                if ip is None:
                    # raise TimeoutError(f'Can not get IP address of {vdi["vmid"]}')
                    await self.delete_vdi(vdi["vmid"])
                vdi["ip"] = ip
            elif vdi["status"] == "stopped":
                vdi["ip"] = None
            await self.refresh_vdi_ip(provider="pve", provider_id=vdi["vmid"], ip=vdi["ip"])


    async def get_ip(self, node : str, vmid : int) -> str:
        attempt = 0
        while True:
            try:
                r = pve.nodes(node).qemu(vmid).agent("network-get-interfaces").get()
                if len(r["result"]) > 0:
                    break
            except ResourceException as e:
                if attempt >= 5:
                    return None
                attempt +=1
                if e.content == "QEMU guest agent is not running":
                    await sleep(5)
                    continue
                if e.content == f"VM {vmid} is not running":
                    await sleep(5)
                    continue
                raise e                
    
        for i in range(len(r["result"])):
            if "ip-addresses" not in r["result"][i]:
                return None
            for ip in r["result"][i]["ip-addresses"]:
                if ip["ip-address-type"] == "ipv4" and ip["ip-address"] != "127.0.0.1":
                    return ip["ip-address"]
    
    async def update_state(self):
        self.pve_vdi_list.clear()

        vdi_provider = self.get_vdi_provider("pve")
        pve_vmid_list = []
        for node in pve.nodes.get():
            for vm in pve.nodes(node["node"]).qemu.get():
                if 'tags' in vm and vm['tags'] == 'openvdi' and vm["vmid"] != pve_template_id:
                    vm["node"] = node["node"]
                    self.pve_vdi_list.append(vm)
                    pve_vmid_list.append(vm["vmid"])
        
        vmid_list = []
        for vdi in vdi_provider:
            vmid_list.append(vdi["provider_id"])

        vmid_for_remove_list = set(vmid_list) - set(pve_vmid_list)
        for vmid in vmid_for_remove_list:
            for vdi in vdi_provider:
                if vdi["provider_id"] == vmid:
                    self.del_vdi(vdi["id"])
                    del vdi

        vmid_for_adding_list = set(pve_vmid_list) - set(vmid_list)
        for vmid in vmid_for_adding_list:
            self.add_vdi(provider="pve", provider_id=vmid)

        await self.pve_refresh_vdi_ip()

    async def get_vdi_by_status(self, status : str) -> List[dict]:
        await self.update_state()
        active_vdi = []
        for vm in self.pve_vdi_list:
            if vm["status"] == status:
                active_vdi.append(vm)
        return active_vdi
    
    async def run_vdi(self, count : int = 1):
        await self.update_state()
        no_active_vdi = await self.get_vdi_by_status(status="stopped")
        if len(no_active_vdi) == 0:
            return
        for i in range(count):
            pve.nodes(self.get_node_by_vmid(no_active_vdi[i]["vmid"])).qemu(no_active_vdi[i]["vmid"]).status.start.post()

    async def stop_vdi(self, count : int = 1, provider_id : str = None, except_ip : list[str] = None):
        await self.update_state()
        if provider_id is None:
            active_vdi = await self.get_vdi_by_status(status="running")
            if except_ip != None:
                active_vdi = [vdi for vdi in active_vdi if vdi["ip"] not in except_ip]
            for i in range(count):
                pve.nodes(self.get_node_by_vmid(active_vdi[i]["vmid"])).qemu(active_vdi[i]["vmid"]).status.stop.post()
                return
        else:
            try:
                pve.nodes(self.get_node_by_vmid(int(provider_id))).qemu(int(provider_id)).status.stop.post()
            except ResourceException as e:
                if e.content == f"501 Not Implemented: Method 'POST /nodes/qemu/{provider_id}/status/stop' not implemented":
                    return
    def get_node_by_vmid(self, vmid : int) -> str:
        # todo:
        # caching
        for node in pve.nodes.get():
            for vm in pve.nodes(node["node"]).qemu.get():
                if 'tags' in vm and vm['tags'] == 'openvdi' and vm["vmid"] != pve_template_id and vm["vmid"] == vmid:
                    return node["node"]
