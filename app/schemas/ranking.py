from pydantic import BaseModel

class Ranking(BaseModel):
    player_id: str
    player_name: str
    position: str
    week: int
    rank: int
    source: str
