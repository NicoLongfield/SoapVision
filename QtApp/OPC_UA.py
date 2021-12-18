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
    
    async def pause_convoyeur_coupe(self):
        async with Client(url=self.url_OPCUA_boudineuse) as client:
            dv = ua.DataValue(ua.Variant(True, ua.VariantType.Boolean))
            _logger.info("Attempting to pause the conveyor belt")
            node_pause_convoyeur = await client.nodes.root.get_child(["0:Objects", "4:NX1021020_Boudineuse","3:GlobalVars","4:entree_OPCUA_pauseConvoyeur"]) #,"4:GlobalVars","4:OPCUA_entree_pause_convoyeur_presse"]
            await node_pause_convoyeur.set_value(dv)
            _logger.info("The conveyor belt was paused")
    
    async def recyclage(self):
        async with Client(url=self.url_OPCUA_boudineuse) as client:
            dv_true = ua.DataValue(ua.Variant(True, ua.VariantType.Boolean))
            print("Attempting to recycle")
            node_ejection = await client.nodes.root.get_child(["0:Objects", "4:NX1021020_Boudineuse","3:GlobalVars","4:entree_OPCUA_ejection_bondon"]) #,"4:GlobalVars","4:OPCUA_entree_pause_convoyeur_presse"]
            # asyncio.wait()
            await node_ejection.set_value(dv_true)
            print("TERMINATOR POWER")

    async def conservation(self):
        async with Client(url=self.url_OPCUA_boudineuse) as client:
            dv_true = ua.DataValue(ua.Variant(True, ua.VariantType.Boolean))
            node_conservation = await client.nodes.root.get_child(["0:Objects", "4:NX1021020_Boudineuse","3:GlobalVars","4:entree_OPCUA_conservation_bondon"]) #,"4:GlobalVars","4:OPCUA_entree_pause_convoyeur_presse"]
            await asyncio.sleep(0.10)
            await node_conservation.set_value(dv_true)
            
            
    async def appel_recyclage(self, delay_entre, delay_avant):
        await self.recyclage()
        await self.conservation()
    
    async def read_acquisition_arret(self):
        async with Client(url=self.url_OPCUA_boudineuse) as client:
            _logger.info("Attempting to read the conveyor's state")
            node_pause_convoyeur = await client.nodes.root.get_child(["0:Objects", "4:NX1021020_Boudineuse","3:GlobalVars","4:acquisition_arret"])
            state_arret = await node_pause_convoyeur.read_value()
            print("Arret = " + str(state_arret))


if __name__ == "__main__":
    OPCUA =  OPCUACommunication()
    asyncio.run(OPCUA.appel_recyclage(0.15, 0.5))
    













