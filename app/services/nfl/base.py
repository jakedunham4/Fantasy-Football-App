from abc import ABC, abstractmethod
from typing import Iterable, Optional
from ...schemas.player import Player
from ...schemas.ranking import Ranking

class NFLProvider(ABC):
    name: str

    @abstractmethod
    def get_players(self, query: Optional[str] = None) -> Iterable[Player]:
        ...

    @abstractmethod
    def get_weekly_rankings(self, position: str, week: int) -> Iterable[Ranking]:
        ...
