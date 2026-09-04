import json
import os
import logging
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2

NATS_URL = os.getenv("NATS_URL", "nats://my-nats-headless.nats.svc.cluster.local:4222")
TODO_EVENT_SUBJECT = os.getenv("TODO_EVENT_SUBJECT", "todo.events")

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
    done: bool

class TodoCreate(BaseModel):
    text: str


def build_todo_event(event: str, todo: Todo) -> dict:
    return {
        "event": event,
        "todo": {
            "id": todo.id,
            "text": todo.text,
            "done": todo.done,
        },
    }


async def publish_todo_event(event: str, todo: Todo):
    payload = build_todo_event(event, todo)
    nc = None
    try:
        import nats

        nc = await nats.connect(NATS_URL)
        await nc.publish(TODO_EVENT_SUBJECT, json.dumps(payload).encode("utf-8"))
        await nc.flush()
        logger.info("Published todo event '%s' for todo %s to NATS subject '%s'", event, todo.id, TODO_EVENT_SUBJECT)
    except Exception as exc:
        logger.warning("Failed to publish todo event '%s': %s", event, exc)
    finally:
        if nc is not None:
            await nc.drain()


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
                text VARCHAR(140) NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE
            );
        """)
        cur.execute("ALTER TABLE todos ADD COLUMN IF NOT EXISTS done BOOLEAN NOT NULL DEFAULT FALSE;")
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
        cur.execute("SELECT id, text, done FROM todos ORDER BY id ASC;")
        rows = cur.fetchall()
        todos = [Todo(id=row[0], text=row[1], done=row[2]) for row in rows]
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
            "INSERT INTO todos (text) VALUES (%s) RETURNING id, text, done;",
            (payload.text,)
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        created_todo = Todo(id=row[0], text=row[1], done=row[2])
        logger.info(f"Successfully created todo ID {row[0]}")
        await publish_todo_event("todo.created", created_todo)
        return created_todo
    except Exception as e:
        logger.error(f"Database insertion error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.put("/todos/{todo_id}", response_model=Todo)
async def complete_todo(todo_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE todos SET done = TRUE WHERE id = %s RETURNING id, text, done;",
            (todo_id,)
        )
        row = cur.fetchone()
        if row is None:
            conn.rollback()
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Todo not found")
        conn.commit()
        cur.close()
        conn.close()
        updated_todo = Todo(id=row[0], text=row[1], done=row[2])
        await publish_todo_event("todo.updated", updated_todo)
        return updated_todo
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database update error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    
is_healthy = True

@app.get("/healthz")
async def health_check():
    global is_healthy
    if not is_healthy:
        raise HTTPException(status_code=500, detail="unhealthy")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Health check failed (DB connection): {e}")
        raise HTTPException(status_code=500, detail="unhealthy")

@app.post("/break")
async def break_app():
    global is_healthy
    is_healthy = False
    return {"status": "broken"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)