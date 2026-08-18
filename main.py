"""
Task CRUD API — backed by SQLite via SQLModel.

Assignment 1 gave you the API shape (in-memory list).
Assignment 2 (this file) swaps the storage layer for a real SQLite
database (tasks.db) while keeping every endpoint's behaviour identical.

Run with:
    uvicorn main:app --reload
"""


from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select, func

# ---------------------------------------------------------------------------
# Stage 0 — Create your database
# ---------------------------------------------------------------------------

DATABASE_FILE = "tasks.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# check_same_thread=False is needed because FastAPI can use the connection
# from more than one thread in dev mode; SQLModel/SQLAlchemy handles the
# actual thread-safety for us via the session.
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


class Task(SQLModel, table=True):
    """The `tasks` table. id is the primary key SQLite assigns for us."""

    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# --- request/response shapes (kept separate from the table model) --------

class TaskCreate(SQLModel):
    title: str
    done: bool = False


class TaskUpdate(SQLModel):
    title: str
    done: bool = False


def create_db_and_tables() -> None:
    """Create tasks.db and the `tasks` table if they don't already exist."""
    SQLModel.metadata.create_all(engine)


def seed_if_empty() -> None:
    """Insert three example tasks — but only the very first time (Stage 0)."""
    with Session(engine) as session:
        count = session.exec(select(func.count()).select_from(Task)).one()
        if count == 0:
            examples = [
                Task(title="Buy milk", done=False),
                Task(title="Write README", done=False),
                Task(title="Learn SQL", done=True),
            ]
            session.add_all(examples)
            session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the app starts — this is what makes the DB and seed
    # rows appear automatically for anyone who clones the repo.
    create_db_and_tables()
    seed_if_empty()
    yield


app = FastAPI(title="Task API", lifespan=lifespan)


def get_task_or_404(session: Session, task_id: int) -> Task:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def validate_title(title: str) -> None:
    if not title or not title.strip():
        raise HTTPException(status_code=400, detail="Title is required")


# ---------------------------------------------------------------------------
# Stage 1 — Read from the database
# ---------------------------------------------------------------------------

@app.get("/tasks")
def list_tasks(
    # ★ optional extras — all query params are optional, plain GET /tasks
    # still behaves exactly like Assignment 1.
    search: Optional[str] = Query(default=None, description="Filter by title, e.g. ?search=milk"),
    done: Optional[bool] = Query(default=None, description="Filter by status, e.g. ?done=true"),
    sort: Optional[str] = Query(default=None, description="Set to 'title' to sort alphabetically"),
):
    with Session(engine) as session:
        statement = select(Task)
        if search:
            statement = statement.where(Task.title.like(f"%{search}%"))  # parameterized under the hood
        if done is not None:
            statement = statement.where(Task.done == done)
        if sort == "title":
            statement = statement.order_by(Task.title)
        return session.exec(statement).all()


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with Session(engine) as session:
        return get_task_or_404(session, task_id)


# ★ optional extra — real statistics computed in SQL, not in Python
@app.get("/stats")
def stats():
    with Session(engine) as session:
        total = session.exec(select(func.count()).select_from(Task)).one()
        completed = session.exec(
            select(func.count()).select_from(Task).where(Task.done == True)  # noqa: E712
        ).one()
        return {"total": total, "completed": completed, "remaining": total - completed}


# ---------------------------------------------------------------------------
# Stage 2 — Create new tasks
# ---------------------------------------------------------------------------

@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    validate_title(payload.title)
    with Session(engine) as session:
        task = Task(title=payload.title.strip(), done=payload.done)
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


# ---------------------------------------------------------------------------
# Stage 3 — Update and delete
# ---------------------------------------------------------------------------

@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    validate_title(payload.title)
    with Session(engine) as session:
        task = get_task_or_404(session, task_id)
        task.title = payload.title.strip()
        task.done = payload.done
        task.updated_at = datetime.utcnow()
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with Session(engine) as session:
        task = get_task_or_404(session, task_id)
        session.delete(task)
        session.commit()
    return None
