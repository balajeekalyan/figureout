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
from flight_mcp import flight_mcp, seats, addons
from roles import ROLES

app = FastAPI()
concierge = FigureOut(mcp_server=flight_mcp, roles=ROLES)
concierge_fees = FigureOut(mcp_server=flight_mcp, interpret_tool_response=True, roles=ROLES)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/tools")
async def tools():
    return [
        {"name": name, "description": tool.description, "inputSchema": tool.parameters}
        for name, tool in flight_mcp._tool_manager._tools.items()
    ]

class AskRequest(BaseModel):
    user_query: str
    role: str | None = None
    context: str | None = None
    output_schema: str | None = None


@app.post("/ask")
async def ask(request: AskRequest):
    engine = concierge_fees if request.role == "explain_fees" else concierge
    result = await engine.run(
        user_query=request.user_query,
        role=request.role,
        context=request.context,
        output_schema=request.output_schema,
    )
    return result

@app.get("/seats/{flight_number}")
async def get_seats(flight_number: str, tier: str = None):
    flight_seats = next((s for s in seats if s["flight_number"].upper() == flight_number.upper()), None)
    if not flight_seats:
        return {"error": f"No seats found for flight '{flight_number}'"}
    rows = flight_seats["section"]["rows"]
    if tier:
        rows = [r for r in rows if r["tier"].lower() == tier.lower()]
    return {
        "flight_number": flight_seats["flight_number"],
        "section": {
            "id": flight_seats["section"]["id"],
            "rows": rows,
        },
    }


@app.get("/addons/{flight_number}")
async def get_addons(flight_number: str, tier: str = None):
    results = [
        a for a in addons
        if a["flight_number"].upper() == flight_number.upper()
    ]
    if not results:
        return {"error": f"No add-ons found for flight '{flight_number}'"}
    if tier:
        results = [a for a in results if a["tier"].lower() == tier.lower()]
    return results


@app.get("/fees/{flight_number}")
async def get_fees(flight_number: str):
    fees = json.loads((DATA_DIR / "fees.json").read_text())
    result = next((f for f in fees if f["flight_number"].upper() == flight_number.upper()), None)
    return result or []


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
