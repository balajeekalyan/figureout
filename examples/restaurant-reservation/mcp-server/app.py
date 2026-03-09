import json
import traceback
from pathlib import Path
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from restaurant_mcp import restaurant_mcp

DATA_DIR = Path(__file__).parent / "data"

load_dotenv(Path(__file__).parent / ".env")


from figureout import FigureOut
from roles import ROLES

app = FastAPI()
concierge_discovery = FigureOut(mcp_server=restaurant_mcp, roles=ROLES, interpret_tool_response=True)
concierge_fees = FigureOut(mcp_server=restaurant_mcp, interpret_tool_response=True, roles=ROLES)

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
    engine = concierge_fees if request.role == "explain_fees" else concierge_discovery
    result = await engine.run(
        user_query=request.user_query,
        role=request.role,
        context=request.context,
        output_schema=request.output_schema,
    )
    return result


@app.get("/addons/{restaurant_id}")
async def get_addons(restaurant_id: int):
    addons = json.loads((DATA_DIR / "addons.json").read_text())
    return [a for a in addons if a["restaurant_id"] == restaurant_id]


@app.get("/fees/{restaurant_id}")
async def get_fees(restaurant_id: int):
    fees = json.loads((DATA_DIR / "fees.json").read_text())
    result = next((f for f in fees if f["restaurant_id"] == restaurant_id), None)
    return result or []


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
