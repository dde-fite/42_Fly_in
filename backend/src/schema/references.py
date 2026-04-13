from typing import NewType
from uuid import UUID

HubRef = NewType("HubRef", UUID)
ConnectionRef = NewType("ConnectionRef", UUID)
DroneRef = NewType("DroneRef", UUID)
