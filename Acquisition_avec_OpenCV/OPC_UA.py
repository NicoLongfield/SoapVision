from datetime import datetime
import logging
import asyncio
from asyncua import Client, ua
from asyncua.common import node
from asyncua.ua.uatypes import Boolean, DataValue

futures = []

_logger = logging.getLogger('asyncua')


class OPCUACommunication():
    url_OPCUA_boudineuse = "opc.tcp://192.168.250.1:4840"
    def __init__(self):
        print("Init...")
    
    async def pause_convoyeur_coupe(self):
        async with Client(url=self.url_OPCUA_boudineuse) as client:
            dv = ua.DataValue(ua.Variant(True, ua.VariantType.Boolean))
            _logger.info("Attempting to pause the conveyor belt")
            node_pause_convoyeur = await client.nodes.root.get_child(["0:Objects", "4:NX1021020_Boudineuse","3:GlobalVars","4:OPCUA_entree_pause_convoyeur_presse"]) #,"4:GlobalVars","4:OPCUA_entree_pause_convoyeur_presse"]
            await node_pause_convoyeur.set_value(dv)
            _logger.info("The conveyor belt was paused")


# loop = asyncio.get_event_loop()
if __name__ == "__main__":
    OPCUA =  OPCUACommunication()
    asyncio.run(OPCUA.pause_convoyeur_coupe())
    













