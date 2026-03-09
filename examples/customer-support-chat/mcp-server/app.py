import uvicorn
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv(Path(__file__).parent / ".env")

from figureout import FigureOut
from chat_mcp import chat_mcp
from roles import ROLES

app = FastAPI()
concierge = FigureOut(mcp_server=chat_mcp, roles=ROLES, interpret_tool_response=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    user_query: str
    role: str | None = None
    context: str | None = None


@app.post("/chat")
async def chat(request: ChatRequest):
    result = await concierge.run(
        user_query=request.user_query,
        role=request.role,
        context=request.context,
    )
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
