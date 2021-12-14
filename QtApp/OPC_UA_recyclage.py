from datetime import datetime
import logging
import asyncio
from asyncua import Client, ua
from asyncua.common import node
from asyncua.ua.uatypes import Boolean, DataValue
import time

futures = []

_logger = logging.getLogger('asyncua')


class OPCUACommunication():
    url_OPCUA_boudineuse = "opc.tcp://192.168.250.1:4840"
    def __init__(self):
        print("Init...")
    
    async def recyclage(self):
        async with Client(url=self.url_OPCUA_boudineuse) as client:
            dv_true = ua.DataValue(ua.Variant(True, ua.VariantType.Boolean))
            print("Attempting to recycle")
            node_ejection = await client.nodes.root.get_child(["0:Objects", "4:NX1021020_Boudineuse","3:GlobalVars","4:entree_OPCUA_ejection_bondon"]) #,"4:GlobalVars","4:OPCUA_entree_pause_convoyeur_presse"]
            await node_ejection.set_value(dv_true)
            print("TERMINATOR POWER")

    async def conservation(self):
        async with Client(url=self.url_OPCUA_boudineuse) as client:
            dv_true = ua.DataValue(ua.Variant(True, ua.VariantType.Boolean))
            node_conservation = await client.nodes.root.get_child(["0:Objects", "4:NX1021020_Boudineuse","3:GlobalVars","4:entree_OPCUA_conservation_bondon"]) #,"4:GlobalVars","4:OPCUA_entree_pause_convoyeur_presse"]
            await node_conservation.set_value(dv_true)
            print("I'LL BE BACK")
            
    async def appel_recyclage(self, delay):
        asyncio.run(self.recyclage())
        time.sleep(delay)
        asyncio.run(self.conservation())
            


# loop = asyncio.get_event_loop()
if __name__ == "__main__":
    OPCUA =  OPCUACommunication()
    asyncio.run(OPCUA.recyclage())
    time.sleep(1)
    asyncio.run(OPCUA.conservation())
    
    













