import os
import logging
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("todo-backend")

DB_HOST = os.getenv("POSTGRES_HOST", "todo-postgres-svc.project.svc.cluster.local")
DB_NAME = os.getenv("POSTGRES_DB", "todos_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgrespassword")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

class Todo(BaseModel):
    id: int
    text: str

class TodoCreate(BaseModel):
    text: str

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id SERIAL PRIMARY KEY,
                text VARCHAR(140) NOT NULL
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Todo Backend", lifespan=lifespan)

@app.get("/todos", response_model=List[Todo])
async def get_todos():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, text FROM todos ORDER BY id ASC;")
        rows = cur.fetchall()
        todos = [Todo(id=row[0], text=row[1]) for row in rows]
        cur.close()
        conn.close()
        return todos
    except Exception as e:
        logger.error(f"Failed to fetch todos: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.post("/todos", response_model=Todo, status_code=201)
async def create_todo(payload: TodoCreate):
    logger.info(f"Received todo request with text: '{payload.text}'")

    if len(payload.text) > 140:
        logger.warning(
            f"REJECTED: Todo text exceeds 140 characters (Length: {len(payload.text)}). Payload: '{payload.text}'"
        )
        raise HTTPException(
            status_code=400, 
            detail="Todo text must not exceed 140 characters."
        )

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO todos (text) VALUES (%s) RETURNING id, text;",
            (payload.text,)
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Successfully created todo ID {row[0]}")
        return Todo(id=row[0], text=row[1])
    except Exception as e:
        logger.error(f"Database insertion error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)