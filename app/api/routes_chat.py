from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.agents import FinancialReportAgent

router = APIRouter()
agent = FinancialReportAgent()   # loads dotenv & retriever

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    answer = agent.run(req.message)
    return ChatResponse(response=answer)
