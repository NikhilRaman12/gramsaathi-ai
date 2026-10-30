"""Optional FastAPI wrapper around the same evidence-first engine."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from scripts.generator import GramsaathiEngine


app = FastAPI(title="Gramsaathi One — Rural Intelligence & Action Agent")
engine: GramsaathiEngine | None = None


def _get_engine() -> GramsaathiEngine:
    global engine
    if engine is None:
        engine = GramsaathiEngine()
    return engine


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    language: Literal["en", "hi"] = "en"


class SummaryItem(BaseModel):
    text: str
    source_ids: list[str]


class ActionItem(BaseModel):
    step: str
    source_ids: list[str]


class EvidenceItem(BaseModel):
    id: str
    text: str
    source_file: str
    source_title: str
    page: int | None = None
    source_urls: list[str] = Field(default_factory=list)
    source_date: str | None = None
    score: float = 0.0


class QueryResponse(BaseModel):
    status: str
    query: str
    language: str
    message: str = ""
    summary: list[SummaryItem] = Field(default_factory=list)
    action_plan: list[ActionItem] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "gramsaathi-one"}


@app.post("/ask", response_model=QueryResponse)
def ask_query(request: QueryRequest) -> dict:
    return _get_engine().run(request.query, request.language)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Gramsaathi One evidence-first rural assistance API",
        "health": "/health",
        "ask": "POST /ask",
    }
