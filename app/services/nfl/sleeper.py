import requests
from typing import Optional, Iterable, List

from .base import NFLProvider
from ...schemas.player import Player
from ...schemas.ranking import Ranking
from ...extensions.cache import cache


# Cache the large players map for 15 minutes.
# Key includes the base_url so different environments don't collide.
@cache.memoize(timeout=900)
def _fetch_all_players_map(base_url: str) -> dict:
    resp = requests.get(f"{base_url}/players/nfl", timeout=30)
    resp.raise_for_status()
    return resp.json()


class SleeperProvider(NFLProvider):
    """
    Lightweight adapter for Sleeper's public NFL endpoints.
    Docs: https://api.sleeper.app/
    """
    name = "sleeper"

    def __init__(self, base_url: str = "https://api.sleeper.app/v1"):
        self.base_url = base_url

    def get_players(self, query: Optional[str] = None) -> Iterable[Player]:
        """
        Returns Player models from Sleeper's players map.
        Applies an optional case-insensitive name filter.
        Cached for 15 minutes to stay polite and fast.
        """
        data = _fetch_all_players_map(self.base_url)

        # Iterate the big player map {player_id: {...}}
        for pid, p in data.items():
            full_name = p.get("full_name") or p.get("last_name") or "?"
            if query and query.lower() not in full_name.lower():
                continue

            yield Player(
                id=str(pid),
                name=full_name,
                team=p.get("team"),
                position=p.get("position"),
            )

    def get_weekly_rankings(self, position: str, week: int) -> Iterable[Ranking]:
        """
        Dummy weekly rankings using Sleeper player list:
        - Filters by position
        - Sorts alphabetically (team, then name)
        - Takes top 25 as placeholder ranks

        Replace this with real projections/consensus ranks when you add
        a provider that exposes weekly scoring or projections.
        """
        players: List[Player] = [
            p for p in self.get_players() if (p.position or "").upper() == position.upper()
        ]
        players.sort(key=lambda x: ((x.team or ""), x.name))

        for i, p in enumerate(players[:25], start=1):
            yield Ranking(
                player_id=p.id,
                player_name=p.name,
                position=position,
                week=week,
                rank=i,
                source=self.name,
            )
