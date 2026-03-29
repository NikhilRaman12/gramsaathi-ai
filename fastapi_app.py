from fastapi import FastAPI
from pydantic import BaseModel
from scripts.generator import GramsaathiEngine

# Initialize FastAPI
app = FastAPI(title="GramSaathi AI – Agriculture & Rural Development Assistant")

# Initialize engine
engine = GramsaathiEngine()

# Define request schema
class QueryRequest(BaseModel):
    query: str

# Define response schema
class QueryResponse(BaseModel):
    answer: str

@app.post("/ask", response_model=QueryResponse)
def ask_query(request: QueryRequest):
    response = engine.run(request.query)
    return QueryResponse(answer=response)

@app.get("/")
def root():
    return {"message": "Welcome to GramSaathi AI – use /ask endpoint to query schemes"}

