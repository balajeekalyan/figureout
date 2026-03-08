import json
import traceback
from pathlib import Path
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from thingstodo_mcp import thingstodo_mcp

DATA_DIR = Path(__file__).parent / "data"

load_dotenv(Path(__file__).parent / ".env")

from figureout import FigureOut
from roles import ROLES

app = FastAPI()
concierge = FigureOut(mcp_server=thingstodo_mcp, roles=ROLES)
concierge_fees = FigureOut(mcp_server=thingstodo_mcp, interpret_tool_response=True, roles=ROLES)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)},
    )


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


@app.get("/activities/{place_id}")
async def get_activities(place_id: int, from_date: str = Query(default=""), to_date: str = Query(default="")):
    activities = json.loads((DATA_DIR / "thingstodo.json").read_text())
    results = []
    for a in activities:
        if a["place_id"] != place_id:
            continue
        filtered_details = [
            d for d in a["details"]
            if (not from_date or d["date"] >= from_date) and (not to_date or d["date"] <= to_date)
        ]
        if filtered_details:
            results.append({**a, "details": filtered_details})
    return results


@app.get("/addons/{activity_id}")
async def get_addons(activity_id: int):
    addons = json.loads((DATA_DIR / "addons.json").read_text())
    return [a for a in addons if a["activity_id"] == activity_id]


@app.get("/fees/{place_id}")
async def get_fees(place_id: int):
    fees = json.loads((DATA_DIR / "fees.json").read_text())
    result = next((f for f in fees if f["place_id"] == place_id), None)
    return result or []


@app.get("/tools")
async def get_tools():
    tools = []
    for tool in thingstodo_mcp._tool_manager.list_tools():
        tools.append({"name": tool.name, "description": tool.description})
    return tools


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
