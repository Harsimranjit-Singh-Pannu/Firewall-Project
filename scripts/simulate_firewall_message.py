
from uuid import uuid4


def create_message_envelope(
    sender,
    recipient,
    text,
    headers=None,
):
    return {
        "message_id": str(uuid4()),
        "sender": sender,
        "recipient": recipient,
        "text": text,
        "headers": dict(headers or {}),
    }