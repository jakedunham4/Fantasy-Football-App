import os
from typing import Iterable, List
from .nfl.sleeper import SleeperProvider
from .nfl.base import NFLProvider
from ..schemas.player import Player
from ..schemas.ranking import Ranking

class CompositeRankings:
    def __init__(self):
        self.providers: List[NFLProvider] = [
            SleeperProvider(os.getenv("SLEEPER_BASE", "https://api.sleeper.app/v1"))
        ]

    def search_players(self, query: str = None) -> List[Player]:
        seen = {}  # type: dict[str, Player]
        for provider in self.providers:
            for p in provider.get_players(query=query):
                if p.id not in seen:
                    seen[p.id] = p
        return list(seen.values())

    def weekly_rankings(self, position: str, week: int) -> List[Ranking]:
        ranks: List[Ranking] = []
        for provider in self.providers:
            ranks.extend(list(provider.get_weekly_rankings(position, week)))
        return sorted(ranks, key=lambda r: r.rank)
