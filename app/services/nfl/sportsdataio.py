import os
from typing import Optional, Iterable, List, Dict, Any, Tuple
import requests

from .base import NFLProvider
from ...schemas.player import Player
from ...schemas.ranking import Ranking
from ...extensions.cache import cache


# ---------------------------------------------------------------------------
# Helpers for base URL, API key, and season type
# ---------------------------------------------------------------------------

def _base_url() -> str:
    return (os.getenv("SPORTSDATAIO_BASE", "https://api.sportsdata.io/v3/nfl")).rstrip("/")


def _api_key() -> str:
    key = os.getenv("SPORTSDATAIO_API_KEY", "")
    if not key:
        raise ValueError("SPORTSDATAIO_API_KEY is required")
    return key


def _season_type() -> str:
    # PRE | REG | POST
    return os.getenv("NFL_SEASON_TYPE", "REG").upper()


# ---------------------------------------------------------------------------
# Generic GET wrapper with correct API key header
# ---------------------------------------------------------------------------

def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    url = f"{_base_url()}{path}"
    headers = {"Ocp-Apim-Subscription-Key": _api_key()}
    r = requests.get(url, headers=headers, params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Robust season & week resolution
# ---------------------------------------------------------------------------

@cache.memoize(timeout=300)  # 5 minutes
def _resolve_season_and_week() -> Tuple[str, int]:
    """
    Resolve the *current* NFL season + week using a robust, tier-safe approach:
        1) Try Timeframes API ("current")
        2) Fallback: CurrentSeason + CurrentWeek
        3) Last resort: env overrides
    """
    # --- Try Timeframes (if available on your plan) ---
    try:
        data = _get("/scores/json/Timeframes/current")
        if isinstance(data, list):
            current = next((t for t in data if t.get("IsCurrent")), None) or \
                      next((t for t in data if t.get("IsUpcoming")), None)
            if current:
                season_num = int(current.get("Season"))
                week = int(current.get("Week"))
                return f"{season_num}{_season_type()}", week
    except Exception:
        pass

    # --- Try CurrentSeason & CurrentWeek ---
    try:
        season_num = _get("/scores/json/CurrentSeason")
        week = _get("/scores/json/CurrentWeek")
        if not isinstance(season_num, int):
            season_num = int(season_num)
        if not isinstance(week, int):
            week = int(week) if str(week).isdigit() else 1
        if week <= 0:
            week = 1
        return f"{season_num}{_season_type()}", week
    except Exception:
        pass

    # --- Last resort: environment overrides ---
    season_env = os.getenv("NFL_SEASON_NUM")
    week_env = os.getenv("NFL_WEEK")
    if season_env and week_env:
        return f"{int(season_env)}{_season_type()}", int(week_env)

    raise RuntimeError("Could not resolve current NFL timeframe from SportsDataIO")


# ---------------------------------------------------------------------------
# SportsDataIO Provider
# ---------------------------------------------------------------------------

class SportsDataIOProvider(NFLProvider):
    name = "sportsdataio"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        # allow explicit override
        if api_key:
            os.environ["SPORTSDATAIO_API_KEY"] = api_key
        if base_url:
            os.environ["SPORTSDATAIO_BASE"] = base_url

    # ----------------------- PLAYERS (cached) ------------------------------

    @cache.memoize(timeout=900)
    def _players_raw(self) -> List[Dict[str, Any]]:
        return _get("/scores/json/Players")

    def get_players(self, query: Optional[str] = None) -> Iterable[Player]:
        data = self._players_raw()
        q = (query or "").lower()
        for p in data:
            full_name = f"{(p.get('FirstName') or '').strip()} {(p.get('LastName') or '').strip()}".strip() or "?"
            if q and q not in full_name.lower():
                continue
            yield Player(
                id=str(p.get("PlayerID")),
                name=full_name,
                team=p.get("Team"),
                position=p.get("Position"),
            )

    # ---------------------- WEEKLY PROJECTIONS (cached) --------------------

    @cache.memoize(timeout=300)
    def _weekly_projections(self, season: str, week: int) -> List[Dict[str, Any]]:
        # Standard SportsDataIO Fantasy Projections endpoint:
        #   /projections/json/PlayerGameProjectionStatsByWeek/{season}/{week}
        path = f"/projections/json/PlayerGameProjectionStatsByWeek/{season}/{week}"
        return _get(path)

    # ---------------------- FANTASY SCORING -------------------------------

    @staticmethod
    def _fantasy_points(row: Dict[str, Any], scoring: str = "ppr") -> float:
        pass_yards = float(row.get("PassingYards") or 0)
        pass_tds = float(row.get("PassingTouchdowns") or 0)
        pass_ints = float(row.get("PassingInterceptions") or 0)

        rush_yards = float(row.get("RushingYards") or 0)
        rush_tds = float(row.get("RushingTouchdowns") or 0)

        recs = float(row.get("Receptions") or 0)
        rec_yards = float(row.get("ReceivingYards") or 0)
        rec_tds = float(row.get("ReceivingTouchdowns") or 0)

        fumbles_lost = float(row.get("FumblesLost") or 0)

        pts = (pass_yards / 25) + (rush_yards / 10) + (rec_yards / 10)
        pts += (pass_tds * 4) + (rush_tds * 6) + (rec_tds * 6)
        pts -= (pass_ints * 2) + (fumbles_lost * 2)

        if scoring == "ppr":
            pts += recs * 1
        elif scoring == "half":
            pts += recs * 0.5

        return round(pts, 2)

    # ---------------------- RANKINGS (public) ------------------------------

    def get_weekly_rankings(
        self,
        position: str,
        week: int,
        season: Optional[str] = None,
        scoring: str = "ppr",
    ) -> Iterable[Ranking]:

        # Allow override, else resolve automatically
        if season:
            if not season.endswith(("REG", "PRE", "POST")):
                season = f"{season}{_season_type()}"
            season_resolved, week_resolved = season, int(week)
        else:
            season_resolved, week_resolved = _resolve_season_and_week()

        data = self._weekly_projections(season_resolved, week_resolved)
        pos = position.upper()

        filtered = [r for r in data if (r.get("Position") or "").upper() == pos]

        scored: List[Dict[str, Any]] = []
        for r in filtered:
            fp = self._fantasy_points(r, scoring=scoring)
            scored.append({"row": r, "fp": fp})

        scored.sort(key=lambda x: (-x["fp"], x["row"].get("Name") or ""))

        for rank, item in enumerate(scored[:100], start=1):
            r = item["row"]
            yield Ranking(
                player_id=str(r.get("PlayerID") or r.get("PlayerId") or ""),
                player_name=r.get("Name") or "?",
                position=pos,
                week=week_resolved,
                rank=rank,
                source=self.name,
            )
