from flask import jsonify, request
from . import api_bp
from ...services.rankings import CompositeRankings

@api_bp.get("/health")
def health():
    return {"status": "ok"}

@api_bp.get("/players")
def players():
    q = request.args.get("q")
    svc = CompositeRankings()
    data = svc.search_players(query=q)
    return jsonify([p.model_dump() for p in data])

@api_bp.get("/rankings")
def rankings():
    position = request.args.get("position", "RB")
    week = int(request.args.get("week", 1))
    svc = CompositeRankings()
    data = svc.weekly_rankings(position=position, week=week)
    return jsonify([r.model_dump() for r in data])
