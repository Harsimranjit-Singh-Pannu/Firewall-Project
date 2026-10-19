
def load_message_parameters(envelope, context):
    """Load received message fields into the execution context."""

    if not isinstance(envelope, dict):
        raise ValueError("Message envelope must be a dictionary")

    if context is None:
        raise ValueError("Message parameter loading requires an execution context")

    required_fields = (
        "message_id",
        "sender",
        "recipient",
        "text",
        "headers",
    )

    missing = [
        field for field in required_fields
        if field not in envelope
    ]

    if missing:
        raise ValueError(
            "Message envelope requires: " + ", ".join(missing)
        )

    parameter_mapping = {
        "Message-Id": ("message_id", "String"),
        "Message-Sender": ("sender", "String"),
        "Message-Recipient": ("recipient", "String"),
        "Message-Text": ("text", "String"),
        "Message-Headers": ("headers", "Object"),
    }

    for parameter_name, (field_name, datatype) in parameter_mapping.items():
        context.set_parameter(
            name=parameter_name,
            value=envelope[field_name],
            datatype=datatype,
        )

    return True
