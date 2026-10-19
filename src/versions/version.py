from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime, timezone

from configuration.models.firewall_config import (
    FirewallConfiguration
)


@dataclass
class Version:

    number: int

    configuration: FirewallConfiguration

    name: str

    description: str | None = None

    parent_version_id: UUID | None = None

    id: UUID = field(
        default_factory=uuid4
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    status: str = "AVAILABLE"