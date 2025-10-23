import os
from typing import List, Dict
from .nfl.base import NFLProvider
from .nfl.sleeper import SleeperProvider
from ..schemas.player import Player
from ..schemas.ranking import Ranking

def _build_providers() -> List[NFLProvider]:
    names = [x.strip().lower() for x in os.getenv("PROVIDERS", "sleeper").split(",") if x.strip()]
    providers: List[NFLProvider] = []
    for name in names:
        if name == "sleeper":
            providers.append(SleeperProvider(os.getenv("SLEEPER_BASE", "https://api.sleeper.app/v1")))
        elif name == "sportsdataio":
            from .nfl.sportsdataio import SportsDataIOProvider
            providers.append(SportsDataIOProvider())
    return providers

class CompositeRankings:
    def __init__(self):
        self.providers: List[NFLProvider] = _build_providers()

    def search_players(self, query: str = None) -> List[Player]:
        seen: Dict[str, Player] = {}
        for provider in self.providers:
            for p in provider.get_players(query=query):
                if p.id not in seen:
                    seen[p.id] = p
        return list(seen.values())

    def weekly_rankings(self, position: str, week: int) -> List[Ranking]:
        ranks: List[Ranking] = []
        for provider in self.providers:
            ranks.extend(list(provider.get_weekly_rankings(position, week)))
        return sorted(ranks, key=lambda r: (r.rank, r.player_name))
