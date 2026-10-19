import uuid
import socket

from datetime import datetime, timezone

from parameters import ParameterScope



class SystemMetadataLoader:


    ENGINE_VERSION = "PXP-Engine-1.0"



    def load(

        self,

        context

    ):


        timestamp = datetime.now(

            timezone.utc

        ).isoformat()



        context.set_parameter(

            "Message_UUID",

            str(uuid.uuid4()),

            datatype="String",

            scope=ParameterScope.SYSTEM

        )


        context.set_parameter(

            "Received_Timestamp",

            timestamp,

            datatype="Timestamp",

            scope=ParameterScope.SYSTEM

        )


        context.set_parameter(

            "Processing_Timestamp",

            timestamp,

            datatype="Timestamp",

            scope=ParameterScope.SYSTEM

        )


        context.set_parameter(

            "Engine_Version",

            self.ENGINE_VERSION,

            datatype="String",

            scope=ParameterScope.SYSTEM

        )


        context.set_parameter(

            "Processing_Node",

            socket.gethostname(),

            datatype="String",

            scope=ParameterScope.SYSTEM

        )