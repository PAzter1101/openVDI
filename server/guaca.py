from typing import List
from guacapy import Guacamole, RDP_CONNECTION, ORG_CONNECTION_GROUP
from config import settings as s

guacamole = Guacamole(
              hostname=s.GUACA_HOST,
              url_path='/guacamole/',
              username=s.GUACA_USER,
              password=s.GUACA_PASS,
              method='http'
            )

class Guaca():
    def __init__(self):
        group = guacamole.get_connection_group_by_name('openVDI')
        if group is None:
            group = ORG_CONNECTION_GROUP
            group["name"] = "openVDI"
            group["type"] = "BALANCING"
            group["attributes"] = {
                'max-connections-per-user': '1',
                'enable-session-affinity': 'true'
            }
            group = guacamole.add_connection_group(group)
        self.group_id = group["identifier"]

    def add_connection(self, ip : str) -> dict:
        connection = RDP_CONNECTION
        connection['name'] = ip
        connection['parentIdentifier'] = self.group_id
        connection['protocol'] = "rdp"
        connection['parameters']['security'] = "nla"
        connection['parameters']['port'] = "3389"
        connection['parameters']['ignore-cert'] = "true"
        connection['parameters']['hostname'] = ip

        return guacamole.add_connection(connection)

    def get_connections(self) -> List[dict]:
        connections = []
        for root_connection in guacamole.get_connections()["childConnectionGroups"]:
            if "childConnections" in root_connection and root_connection["identifier"] == self.group_id:
                for connection in root_connection["childConnections"]:
                    connections.append(connection)
        return connections
    
    def del_connection(self, id : int):
        guacamole.delete_connection(id)

    async def get_count_not_connected_vdi(self) -> int:
        active_connection_identifier_list = []
        for connection in guacamole.get_active_connections().values():
            active_connection_identifier_list.append(connection["connectionIdentifier"])

        connection_identifier_list = []
        for connection_identifier in self.get_connections():
            connection_identifier_list.append(connection_identifier["identifier"])

        return len(set(connection_identifier_list) - set(active_connection_identifier_list))
    
    async def get_active_connection_ip_list(self) -> List[str]:
        ip_list = []
        for connection in guacamole.get_active_connections().values():
            ip = guacamole.get_connection(connection["connectionIdentifier"])["name"]
            ip_list.append(ip)
        return ip_list

# Uncomment the next lines to match guacamole credentials with windows credentials
# Leave commented to prompt for credentials upon connection
#RDP_CONNECTION['parameters']['username'] = '${GUAC_USERNAME}' # Windows Username
#RDP_CONNECTION['parameters']['password'] = '${GUAC_PASSWORD}' # Windows Password
#RDP_CONNECTION['parameters']['domain'] = "DOMAIN" # Windows Domain
