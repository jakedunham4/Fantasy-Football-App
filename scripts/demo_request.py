# Quick smoke test for a provider call (run from project root):
#   python scripts/demo_request.py
import os, requests
BASE = os.getenv("SLEEPER_BASE", "https://api.sleeper.app/v1")
r = requests.get(f"{BASE}/players/nfl", timeout=30)
print("Status:", r.status_code, "Count:", len(r.json()))
