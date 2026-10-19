
from parameters import ParameterScope


class ExtractMetadataOperation:
    name = "extract-message-metadata"

    def execute(self, context, parameters):
        if context is None:
            raise ValueError(
                "extract-message-metadata requires a context"
            )

        metadata = context.get_metadata("Message-Metadata")

        if not isinstance(metadata, dict):
            raise ValueError(
                "Message-Metadata must be a dictionary"
            )

        if not parameters.get("require_metadata", True):
            pass

        fields = parameters.get("fields", {
            "sender": "Sender_MSISDN",
            "recipient": "Recipient_MSISDN",
            "text": "Text-Content",
            "message_id": "Message-ID",
        })

        for source_name, parameter_name in fields.items():
            if source_name not in metadata:
                continue

            value = metadata[source_name]

            if not isinstance(value, str):
                raise ValueError(
                    f"Metadata field {source_name} must be a string"
                )

            context.set_parameter(
                name=parameter_name,
                value=value,
                datatype="String",
                scope=ParameterScope.GLOBAL,
            )

        headers = metadata.get("headers", {})
        if not isinstance(headers, dict):
            raise ValueError("Message headers must be a dictionary")

        prefix = parameters.get("header_prefix", "Header:")

        for header_name, value in headers.items():
            if not isinstance(header_name, str):
                raise ValueError("Header names must be strings")

            if not isinstance(value, str):
                raise ValueError(
                    f"Header {header_name} must have a string value"
                )

            context.set_parameter(
                name=f"{prefix}{header_name}",
                value=value,
                datatype="String",
                scope=ParameterScope.GLOBAL,
            )

        return True