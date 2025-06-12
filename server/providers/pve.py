from typing import List, Dict, Optional
from trio import sleep, move_on_after
from .provider import Provider
from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException
from config import settings as s
from functools import lru_cache
from time import time

pve = ProxmoxAPI(
    s.PVE_HOST,
    user=s.PVE_USER,
    password=s.PVE_PASS,
    verify_ssl=False
)

pve_template_id = s.PVE_TEMPLATE_ID
pve_vdi_prefix = s.PVE_VDI_PREFIX * 1000

class VMCache:
    def __init__(self, ttl: int = 60):
        self.cache: Dict[str, Dict] = {}
        self.ttl = ttl  # Time to live in seconds

    def set(self, key: str, value: Dict) -> None:
        self.cache[key] = {
            'data': value,
            'timestamp': time()
        }

    def get(self, key: str) -> Optional[Dict]:
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if time() - entry['timestamp'] > self.ttl:
            del self.cache[key]
            return None
            
        return entry['data']

    def clear(self) -> None:
        self.cache.clear()

class PVE(Provider):
    def __init__(self):
        self.pve_vdi_list = []
        self.vm_cache = VMCache()
        self.nodes_cache = None
        self.nodes_cache_time = 0
        self.nodes_cache_ttl = 60  # 60 seconds TTL for nodes cache
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

    def clear_caches(self):
        """Clear all caches when needed"""
        self.vm_cache.clear()
        self.nodes_cache = None
        self.nodes_cache_time = 0

    async def create_VDI(self, balanced: bool = False, pve_node: str = None): 
        # Use cached state if available, otherwise update
        if not self.pve_vdi_list:
            await self.update_state()
        
        # Get list of existing VDI IDs from cached state
        vdi_id_list = [vm["vmid"] for vm in self.pve_vdi_list]
        
        # Find next available VM ID
        vm_id = pve_vdi_prefix + 1
        while vm_id in vdi_id_list:
            vm_id += 1

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

    async def delete_vdi(self, vmid: int = None, force: bool = False):
        if vmid is None:
            time_creation = {}
            for vdi in self.pve_vdi_list:
                if vdi["status"] == "stopped":
                    # Use cached VM info if available
                    cache_key = f"vm_{vdi['vmid']}"
                    cached_vm = self.vm_cache.get(cache_key)
                    if cached_vm and "vm" in cached_vm and "meta" in cached_vm["vm"]:
                        time_creation[vdi["vmid"]] = cached_vm["vm"]["meta"].split(",")[1].split("=")[1]
                    else:
                        config = pve.nodes(self.get_node_by_vmid(vdi["vmid"])).qemu(vdi["vmid"]).config.get()
                        time_creation[vdi["vmid"]] = config["meta"].split(",")[1].split("=")[1]
            
            if time_creation == {} and force:
                for vdi in self.pve_vdi_list:
                    config = pve.nodes(self.get_node_by_vmid(vdi["vmid"])).qemu(vdi["vmid"]).config.get()
                    time_creation[vdi["vmid"]] = config["meta"].split(",")[1].split("=")[1]
            
            if time_creation == {}:
                raise ValueError("Unable to delete VM: No VM with status stopped")
            vmid = min(time_creation, key=time_creation.get)

        try:
            await self.stop_vdi(provider_id=str(vmid))
            node = self.get_node_by_vmid(vmid)
            pve.nodes(node).qemu(vmid).delete()
            
            # Clear cache for this VM
            cache_key = f"vm_{vmid}"
            self.vm_cache.cache.pop(cache_key, None)
            
        except ResourceException as e:
            if e.content in [f"501 Not Implemented: Method 'POST /nodes/qemu/{vmid}/status/stop' not implemented",
                            f"501 Not Implemented: Method 'DELETE /nodes/qemu/{vmid}' not implemented"]:
                return
            else:
                raise e
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
        
        # Use cached nodes
        nodes = await self.get_nodes()
        for node in nodes:
            node_name = node["node"]
            # Get VMs for this node
            vms = pve.nodes(node_name).qemu.get()
            
            # Update cache for each VM
            for vm in vms:
                if 'tags' in vm and vm['tags'] == 'openvdi' and vm["vmid"] != pve_template_id:
                    vm["node"] = node_name
                    self.pve_vdi_list.append(vm)
                    pve_vmid_list.append(vm["vmid"])
                    
                    # Update VM cache
                    cache_key = f"vm_{vm['vmid']}"
                    self.vm_cache.set(cache_key, {"node": node_name, "vm": vm})
        
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
    
    async def run_vdi(self, count: int = 1):
        await self.update_state()
        no_active_vdi = await self.get_vdi_by_status(status="stopped")
        if len(no_active_vdi) == 0:
            return
        
        for i in range(min(count, len(no_active_vdi))):
            vmid = no_active_vdi[i]["vmid"]
            node = self.get_node_by_vmid(vmid)
            
            # Start the VM
            pve.nodes(node).qemu(vmid).status.start.post()
            
            # Update cache with new status
            cache_key = f"vm_{vmid}"
            cached_vm = self.vm_cache.get(cache_key)
            if cached_vm:
                cached_vm["vm"]["status"] = "running"
                self.vm_cache.set(cache_key, cached_vm)

    async def stop_vdi(self, count: int = 1, provider_id: str = None, except_ip: list[str] = None):
        await self.update_state()
        
        if provider_id is None:
            active_vdi = await self.get_vdi_by_status(status="running")
            if except_ip is not None:
                active_vdi = [vdi for vdi in active_vdi if vdi["ip"] not in except_ip]
            
            for i in range(min(count, len(active_vdi))):
                vmid = active_vdi[i]["vmid"]
                node = self.get_node_by_vmid(vmid)
                
                # Stop the VM
                pve.nodes(node).qemu(vmid).status.stop.post()
                
                # Update cache with new status
                cache_key = f"vm_{vmid}"
                cached_vm = self.vm_cache.get(cache_key)
                if cached_vm:
                    cached_vm["vm"]["status"] = "stopped"
                    cached_vm["vm"]["ip"] = None
                    self.vm_cache.set(cache_key, cached_vm)
                return
        else:
            vmid = int(provider_id)
            node = self.get_node_by_vmid(vmid)
            
            # Stop the VM
            pve.nodes(node).qemu(vmid).status.stop.post()
            
            # Update cache with new status
            cache_key = f"vm_{vmid}"
            cached_vm = self.vm_cache.get(cache_key)
            if cached_vm:
                cached_vm["vm"]["status"] = "stopped"
                cached_vm["vm"]["ip"] = None
                self.vm_cache.set(cache_key, cached_vm)
        
    async def get_nodes(self) -> List[dict]:
        """Get nodes with caching"""
        current_time = time()
        if self.nodes_cache is not None and (current_time - self.nodes_cache_time) < self.nodes_cache_ttl:
            return self.nodes_cache
        
        nodes = pve.nodes.get()
        self.nodes_cache = nodes
        self.nodes_cache_time = current_time
        return nodes

    def get_node_by_vmid(self, vmid: int) -> str:
        """Get node name for a VM with caching"""
        cache_key = f"vm_{vmid}"
        cached_node = self.vm_cache.get(cache_key)
        if cached_node:
            return cached_node["node"]
        
        # If not in cache, search through nodes
        for node in pve.nodes.get():
            for vm in pve.nodes(node["node"]).qemu.get():
                if ('tags' in vm and vm['tags'] == 'openvdi' and 
                    vm["vmid"] != pve_template_id and vm["vmid"] == vmid):
                    # Cache the result
                    self.vm_cache.set(cache_key, {"node": node["node"], "vm": vm})
                    return node["node"]
