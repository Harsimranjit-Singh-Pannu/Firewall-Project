from dataclasses import dataclass

from conditions.enums import (
    SourceType,
    RightSourceType
)



@dataclass
class ArgumentBinding:


    argument_name: str


    source_type: object


    source_name: str = None


    value: object = None



    def validate(self):


        if self.source_type == SourceType.PARAMETER:


            if self.source_name is None:

                raise ValueError(

                    "Parameter source requires source_name"

                )


            if self.value is not None:

                raise ValueError(

                    "Parameter source cannot have value"

                )



        elif self.source_type == RightSourceType.USER_VALUE:


            if self.value is None:

                raise ValueError(

                    "User value source requires value"

                )


            if self.source_name is not None:

                raise ValueError(

                    "User value source cannot have source_name"

                )


        else:

            raise ValueError(

                f"Unsupported argument source: {self.source_type}"

            )


        return True