from pydantic import BaseModel
from typing import Optional

class TaskMetadata(BaseModel):
    created_at: float
    client_ip: str
    owner_id: Optional[str] = None
