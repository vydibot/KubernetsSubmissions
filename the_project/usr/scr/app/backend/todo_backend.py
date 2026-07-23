import os
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Todo Backend")


class Todo(BaseModel):
    id: int
    text: str = Field(..., max_length=140)


class TodoCreate(BaseModel):
    text: str = Field(..., max_length=140)


todos_db: List[Todo] = [
    Todo(id=1, text="Learn Kubernetes basics"),
    Todo(id=2, text="Deploy application to cluster"),
    Todo(id=3, text="Configure persistent volumes"),
]


@app.get("/todos", response_model=List[Todo])
async def get_todos():
    return todos_db


@app.post("/todos", response_model=Todo, status_code=201)
async def create_todo(payload: TodoCreate):
    new_id = len(todos_db) + 1 if todos_db else 1
    todo = Todo(id=new_id, text=payload.text)
    todos_db.append(todo)
    return todo


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)