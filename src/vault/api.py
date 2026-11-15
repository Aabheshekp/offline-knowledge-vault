from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field
from .index import initialize, ingest_folder, search, stats

app=FastAPI(title="Offline Knowledge Vault",version="1.0.0",description="Local-only document retrieval")
STATIC=Path(__file__).resolve().parents[2]/"web"/"static"
app.mount("/static",StaticFiles(directory=STATIC),name="static")

class IngestRequest(BaseModel): path:str=Field(min_length=1,max_length=1000)

@app.on_event("startup")
def startup(): initialize()

@app.get("/",include_in_schema=False)
def home(): return FileResponse(STATIC/"index.html")

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/api/v1/stats")
def index_stats(): return stats()

@app.get("/api/v1/search")
def search_api(q:str=Query(min_length=1,max_length=500),limit:int=Query(8,ge=1,le=50)):
    try:return {"query":q,"results":search(q,limit)}
    except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.post("/api/v1/ingest")
def ingest(body:IngestRequest):
    try:return {"results":ingest_folder(body.path)}
    except (ValueError,OSError) as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc
