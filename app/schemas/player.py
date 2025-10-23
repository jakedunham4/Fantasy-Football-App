from typing import Optional
from pydantic import BaseModel

class Player(BaseModel):
    id: str
    name: str
    team: Optional[str] = None
    position: Optional[str] = None
