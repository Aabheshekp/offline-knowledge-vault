from __future__ import annotations
from pathlib import Path
import hashlib
import html
import re
import sqlite3
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .settings import DB_PATH, LIBRARY_ROOT, CHUNK_SIZE, CHUNK_OVERLAP

SUPPORTED={".txt",".md",".rst",".html",".htm",".pdf"}

def connect():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(DB_PATH,timeout=10); con.row_factory=sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON"); return con

def initialize():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY,path TEXT UNIQUE NOT NULL,title TEXT NOT NULL,sha256 TEXT NOT NULL,size_bytes INTEGER NOT NULL,modified_at TEXT NOT NULL,indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY,document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,chunk_no INTEGER NOT NULL,page_no INTEGER,text TEXT NOT NULL,UNIQUE(document_id,chunk_no));
        CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id,chunk_no);
        """)

def safe_path(path: str | Path) -> Path:
    candidate=Path(path).expanduser().resolve()
    try: candidate.relative_to(LIBRARY_ROOT)
    except ValueError as exc: raise ValueError("Path must be inside the configured library root") from exc
    if not candidate.is_file(): raise ValueError("Path is not a file")
    if candidate.suffix.lower() not in SUPPORTED: raise ValueError(f"Unsupported file type: {candidate.suffix}")
    return candidate

def extract(path: Path) -> list[tuple[int|None,str]]:
    if path.suffix.lower()==".pdf":
        return [(i+1,page.extract_text() or "") for i,page in enumerate(PdfReader(path).pages)]
    text=path.read_text(encoding="utf-8",errors="replace")
    if path.suffix.lower() in {".html",".htm"}:
        text=re.sub(r"(?is)<(script|style).*?>.*?</\1>"," ",text)
        text=html.unescape(re.sub(r"(?s)<[^>]+>"," ",text))
    return [(None,text)]

def chunk_text(text: str, size: int=CHUNK_SIZE, overlap: int=CHUNK_OVERLAP) -> list[str]:
    if size<100 or overlap<0 or overlap>=size: raise ValueError("Chunk size must be >= 100 and overlap must be smaller")
    paragraphs=[re.sub(r"\s+"," ",p).strip() for p in re.split(r"\n\s*\n",text) if p.strip()]
    blocks=[]; current=""
    for paragraph in paragraphs:
        while len(paragraph)>size:
            if current: blocks.append(current); current=""
            blocks.append(paragraph[:size]); paragraph=paragraph[size-overlap:]
        candidate=(current+" "+paragraph).strip()
        if len(candidate)>size and current:
            blocks.append(current); current=current[-overlap:] if overlap else ""
            candidate=(current+" "+paragraph).strip()
        current=candidate
    if current: blocks.append(current)
    return blocks

def ingest_file(path: str|Path) -> dict:
    initialize(); file=safe_path(path); digest=hashlib.sha256(file.read_bytes()).hexdigest()
    text_pages=extract(file); all_chunks=[]
    for page,text in text_pages:
        for chunk in chunk_text(text): all_chunks.append((page,chunk))
    if not all_chunks: raise ValueError("No searchable text found")
    relative=file.relative_to(LIBRARY_ROOT).as_posix()
    with connect() as con:
        old=con.execute("SELECT id,sha256 FROM documents WHERE path=?",(relative,)).fetchone()
        if old and old["sha256"]==digest: return {"path":relative,"status":"unchanged","chunks":con.execute("SELECT COUNT(*) FROM chunks WHERE document_id=?",(old["id"],)).fetchone()[0]}
        if old:
            doc_id=old["id"]
            con.execute("UPDATE documents SET title=?,sha256=?,size_bytes=?,modified_at=?,indexed_at=CURRENT_TIMESTAMP WHERE id=?",(file.stem,digest,file.stat().st_size,file.stat().st_mtime_ns,doc_id))
            con.execute("DELETE FROM chunks WHERE document_id=?",(doc_id,))
        else:
            cur=con.execute("INSERT INTO documents(path,title,sha256,size_bytes,modified_at) VALUES(?,?,?,?,?)",(relative,file.stem,digest,file.stat().st_size,str(file.stat().st_mtime_ns)))
            doc_id=cur.lastrowid
        con.executemany("INSERT INTO chunks(document_id,chunk_no,page_no,text) VALUES(?,?,?,?)",[(doc_id,i,page,chunk) for i,(page,chunk) in enumerate(all_chunks)])
    return {"path":relative,"status":"indexed","chunks":len(all_chunks)}

def ingest_folder(path: str|Path) -> list[dict]:
    folder=Path(path).expanduser().resolve()
    try: folder.relative_to(LIBRARY_ROOT)
    except ValueError as exc: raise ValueError("Folder must be inside the configured library root") from exc
    if not folder.is_dir(): raise ValueError("Path is not a directory")
    results=[]
    for file in sorted(folder.rglob("*")):
        if file.is_file() and file.suffix.lower() in SUPPORTED:
            try: results.append(ingest_file(file))
            except (OSError,ValueError) as exc: results.append({"path":str(file.relative_to(LIBRARY_ROOT)),"status":"error","error":str(exc)})
    return results

def stats() -> dict:
    initialize()
    with connect() as con:
        return {"documents":con.execute("SELECT COUNT(*) FROM documents").fetchone()[0],"chunks":con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],"library_root":str(LIBRARY_ROOT)}

def search(query: str, limit: int=8) -> list[dict]:
    if not query.strip(): raise ValueError("Search query cannot be empty")
    initialize()
    with connect() as con: rows=con.execute("SELECT c.text,c.page_no,d.path,d.title FROM chunks c JOIN documents d ON d.id=c.document_id").fetchall()
    if not rows:return []
    texts=[r["text"] for r in rows]
    try:
        matrix=TfidfVectorizer(stop_words="english",ngram_range=(1,2),max_features=100000).fit_transform(texts+[query])
        scores=cosine_similarity(matrix[-1],matrix[:-1]).ravel()
    except ValueError:return []
    ranked=scores.argsort()[::-1][:max(1,min(limit,50))]
    return [{"source":rows[i]["path"],"title":rows[i]["title"],"page":rows[i]["page_no"],"score":round(float(scores[i]),4),"text":rows[i]["text"]} for i in ranked if scores[i]>0]
