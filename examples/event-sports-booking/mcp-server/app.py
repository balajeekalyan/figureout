import json
from pathlib import Path
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DATA_DIR = Path(__file__).parent / "data"

load_dotenv(Path(__file__).parent / ".env")

from figureout import FigureOut
from event_mcp import event_mcp, _get_seats, load_json
from roles import ROLES

app = FastAPI()
concierge = FigureOut(mcp_server=event_mcp, roles=ROLES)
concierge_discovery = FigureOut(mcp_server=event_mcp, roles=ROLES, max_roles=3, interpret_tool_response=True)
concierge_seats = FigureOut(mcp_server=event_mcp, interpret_tool_response=True, roles=ROLES)
concierge_fees = FigureOut(mcp_server=event_mcp, interpret_tool_response=True, roles=ROLES)

_events = load_json("events.json")
_AVAILABLE_GENRES = sorted({g for e in _events for g in e.get("genre", [])})
_DISCOVERY_ROLES = {
    "sports_discovery",
    "movie_discovery",
    "music_artist_discovery",
    "music_festival_discovery",
    "kids_family_shows_discovery",
    "standup_comedy_discovery",
    "theater_shows_discovery",
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    user_query: str
    role: str | None = None
    context: str | None = None
    output_schema: str | None = None


@app.get("/tools")
async def tools():
    return [
        {"name": name, "description": tool.description, "inputSchema": tool.parameters}
        for name, tool in event_mcp._tool_manager._tools.items()
    ]

@app.get("/seats/{event_id}")
async def get_seats(event_id: str, tier: str = None):
    seats = _get_seats()
    event_seats = next((s for s in seats if s["event_id"] == event_id), None)
    if not event_seats:
        return {"error": f"No seats found for event '{event_id}'"}
    rows = event_seats["section"]["rows"]
    if tier:
        rows = [r for r in rows if r["tier"].lower() == tier.lower()]
    return {
        "event_id": event_seats["event_id"],
        "section": {
            "id": event_seats["section"]["id"],
            "rows": rows,
        },
    }

@app.post("/ask")
async def ask(request: AskRequest):
    if request.role == "explain_fees":
        engine = concierge_fees
    elif request.role == "seat_selection":
        engine = concierge_seats
    elif request.role in _DISCOVERY_ROLES or request.role is None:
        engine = concierge_discovery
    else:
        engine = concierge

    context = request.context
    if request.role in _DISCOVERY_ROLES or request.role is None:
        genres_ctx = f"Available genres: {', '.join(_AVAILABLE_GENRES)}"
        context = f"{context}\n{genres_ctx}" if context else genres_ctx

    result = await engine.run(
        user_query=request.user_query,
        role=request.role,
        context=context,
        output_schema=request.output_schema,
    )
    return result


@app.get("/fees/{event_id}")
async def get_fees(event_id: str):
    fees = json.loads((DATA_DIR / "fees.json").read_text())
    result = next((f for f in fees if f["event_id"] == event_id), None)
    return result or []


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
