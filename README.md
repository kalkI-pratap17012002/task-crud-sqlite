# Task API — Assignment 2: Connecting your CRUD to the database

A FastAPI CRUD API for tasks, backed by a real SQLite database (`tasks.db`)
via SQLModel. Same endpoints as Assignment 1 — only the storage layer
changed, from an in-memory list to a database file on disk.

## Why SQLite

- **Zero setup** — no separate database server to install, configure, or
  run. The whole database is a single file.
- **Perfect for this stage of the project** — the assignment's goal is
  persistence, not scale, and SQLite gives that with the least ceremony.
- **Easy to inspect** — you can open `tasks.db` directly in a GUI tool
  (DB Browser for SQLite) or the built-in `sqlite3` CLI and see exactly
  what your API sees.
- **A stepping stone, not a dead end** — because the storage layer is
  isolated behind SQLModel, moving to PostgreSQL or MySQL later is a
  connection-string change, not a rewrite.

## Where the database file lives

`tasks.db`, created automatically in the project root the first time the
app starts. It's listed in `.gitignore` so every fresh clone starts with a
clean database — the app recreates the file and table, and seeds three
example tasks, with no manual setup.

## How to run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API is then live at `http://localhost:8000`. Interactive docs (from
FastAPI automatically) are at `http://localhost:8000/docs`.

## Endpoints (unchanged from Assignment 1)

| Method | Path            | Behaviour                                    |
|--------|-----------------|-----------------------------------------------|
| GET    | `/tasks`        | List all tasks (supports `?search=`, `?done=`, `?sort=title`) |
| GET    | `/tasks/{id}`   | Get one task, `404` if unknown id             |
| POST   | `/tasks`        | Create a task, `400` if title missing, `201` on success |
| PUT    | `/tasks/{id}`   | Update a task, `404`/`400` as above           |
| DELETE | `/tasks/{id}`   | Delete a task, `204` on success               |
| GET    | `/stats`        | `{total, completed, remaining}` computed in SQL |

## Example SQL query I ran by hand (Stage 4)

Opened `tasks.db` in DB Browser for SQLite and ran:

```sql
SELECT COUNT(*) FROM tasks WHERE done = 1;
```

This returned the number of completed tasks — and calling `GET /stats`
through the running API returned the same number in its `completed`
field, with no restart needed, confirming the API and the database file
are reading the exact same source of truth.

## Notes on the build

- Table is explicitly named `tasks` (`__tablename__ = "tasks"`) — by
  default SQLModel would have used the singular class name (`task`), so
  this was a real bug I hit and fixed while testing.
- All queries go through SQLModel/SQLAlchemy, which parameterizes values
  automatically — nothing is ever glued into a raw SQL string.
- Seeding is guarded by a row-count check (`if count == 0`), so restarting
  the server never duplicates the three example tasks.
- `created_at` / `updated_at` timestamps are included as an extra.

## AI vs me (Stage 6)

This stage asks you to write your own migration prompt from memory, run
it in a separate `ai-version/` folder, and diff it against your hand-built
code — that comparison only works if the two versions come from different
processes. Since this whole file was generated in one pass, I didn't fake
a second "AI-generated" version here. To actually complete Stage 6:

1. Write a prompt from memory (don't copy the assignment PDF) describing
   the migration: lane + library, the `tasks` table's columns, "create
   table if missing," "seed three tasks only when empty," the five
   endpoints and their status codes, and parameterized queries.
2. Run it against a fresh copy of your Assignment 1 code, in `ai-version/`.
3. `git diff --no-index` your `main.py` against the AI's file and note
   what it did better, what it got wrong, and what your prompt left
   unspecified.
