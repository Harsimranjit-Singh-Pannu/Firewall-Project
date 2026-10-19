from dataclasses import dataclass, field



@dataclass
class Operation:


    name: str


    parameters: dict = field(

        default_factory=dict

    )