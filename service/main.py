# service/main.py
import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

app = FastAPI(title="Target Registry")
DB = "targets.db"

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

with get_conn() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS targets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL UNIQUE,
        is_cdn INTEGER NOT NULL DEFAULT 0)""")

class TargetIn(BaseModel):
    url: HttpUrl
    is_cdn: bool = False

@app.post("/targets", status_code=201)
def create_target(t: TargetIn):
    conn = get_conn()
    try:
        cur = conn.execute("INSERT INTO targets (url, is_cdn) VALUES (?, ?)",
                           (str(t.url), int(t.is_cdn)))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="URL already registered")
    return {"id": cur.lastrowid, "url": str(t.url), "is_cdn": t.is_cdn}

@app.get("/targets")
def list_targets():
    rows = get_conn().execute("SELECT * FROM targets").fetchall()
    return [dict(r) for r in rows]


# ’d use FastAPI. It gives you a built-in Swagger page at /docs, which is a good way to see requests and responses live,
# Run it with: Command:  uvicorn service.main:app --reload, then open http://localhost:8000/docs.
# --reload: automatically restarts when you modify your Python code.
# FastAPI = builds the API
# Uvicorn = runs the API server
# Swagger = lets you test/view the API in your browser (So you don't necessarily need Postman just to test basic API endpoints.)

# uvicorn service.main:app --reload, (start the server,python mode path, use app object)
# Go to service/main.py, find the object called app, and run it as my web application.

# uvicorn
#    ↓
# start web server
#    ↓
# service/main.py
#    ↓
# app = FastAPI()
#    ↓
# listen on localhost:8000