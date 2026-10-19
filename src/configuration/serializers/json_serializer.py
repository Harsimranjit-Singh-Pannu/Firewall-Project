import json
from dataclasses import asdict, is_dataclass


class JsonSerializer:


    def serialize(
        self,
        obj
    ):

        if is_dataclass(obj):

            obj = asdict(
                obj
            )


        return json.dumps(

            obj,

            indent=4,

            default=str

        )