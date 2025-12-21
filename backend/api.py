from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

from backend.nl_to_sql import answer_question

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    sql: str
    rows: list[Dict[str, Any]]
    explanation: str

app = FastAPI(title="NFL Stat SQL API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def post_query(req: QueryRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="`question` is required")

    try:
        result = answer_question(req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result
