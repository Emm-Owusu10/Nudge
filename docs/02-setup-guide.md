# Setup Guide

This guide sets up the project on Windows using PowerShell. Commands for macOS or Linux differ only in the activation step and path separators.

## Prerequisites

- Python 3.12
- PostgreSQL 18, installed locally (Docker is not used)
- A code editor, such as VS Code

## 1. Create the project folders

From the folder where the project lives:

```powershell
New-Item -ItemType Directory -Force -Path backend/app/core, backend/tests, docs
```

## 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python --version
```

If PowerShell reports that scripts are disabled, run this once and activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

When the environment is active, your prompt shows `(.venv)`.

## 3. Install dependencies

From the project root, with `(.venv)` active:

```powershell
python -m pip install -r requirements.txt
```

Versions are pinned in `requirements.txt`, so every installation matches.

## 4. Create the PostgreSQL role and databases

Find `psql.exe` in your PostgreSQL `bin` folder, for example `C:\Program Files\PostgreSQL\18\bin\psql.exe`. Connect as the `postgres` superuser:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost
```

At the `postgres=#` prompt, run the following, replacing `YourPassword` with a password containing only letters and numbers:

```sql
CREATE USER ei_user WITH PASSWORD 'YourPassword';
CREATE DATABASE early_intervention OWNER ei_user;
CREATE DATABASE early_intervention_test OWNER ei_user;
\q
```

The test database must be separate. The test suite deletes all rows in it.

To change the password later:

```sql
ALTER USER ei_user WITH PASSWORD 'NewPassword';
```

Then update `.env` to match.

## 5. Configure environment variables

Copy the template from the project root:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set the same password in both lines:

```dotenv
DATABASE_URL=postgresql+psycopg://ei_user:YourPassword@localhost:5432/early_intervention
TEST_DATABASE_URL=postgresql+psycopg://ei_user:YourPassword@localhost:5432/early_intervention_test
```

Rules for the password in the URL:

- Use letters and numbers only. Characters such as `@`, `:`, `/`, and `#` must be percent-encoded (`@` becomes `%40`) or the URL breaks.
- Never commit `.env`. It is listed in `.gitignore`.

## 6. Apply database migrations

From the `backend` folder:

```powershell
cd backend
alembic upgrade head
alembic current
```

`alembic current` should show the latest revision followed by `(head)`.

## 7. Check the configuration and database connection

```powershell
python -c "from app.core.config import get_settings; s = get_settings(); print(s.app_name, '|', s.app_env)"
```

Expected output:

```
Early Intervention Decision-Support API | development
```

## 8. Start the server

From the `backend` folder:

```powershell
uvicorn app.main:app --reload
```

Check it:

- `http://127.0.0.1:8000/health` returns `{"status":"ok","database":"connected"}`.
- `http://127.0.0.1:8000/docs` shows the interactive API documentation.

## 9. Run the tests

From the `backend` folder:

```powershell
python -m pytest -v
```

The tests use `early_intervention_test`. The suite stops before deleting anything if the test connection points at a database whose name does not end in `_test`, or at the development database.

## Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| `psql` is not recognised | Use the full path to `psql.exe`, as in step 4. |
| `password authentication failed` | The password in `.env` differs from the one set in PostgreSQL. Reset it with `ALTER USER`, then update both `.env` lines. |
| `role "ei_user" does not exist` | The `CREATE USER` step was not run, or was run against a different server. |
| `No module named 'app'` | Run pytest and uvicorn from the `backend` folder, not the project root. |
| `No module named 'backend'` | An import starts with `from backend.app...`. Change it to `from app...`. Find these with `Get-ChildItem -Recurse -Filter *.py \| Select-String "from backend"`. |
| `database_url field required` | `.env` is missing or is in the wrong folder. It must be in the project root. |
| Tables missing after tests | Tests create and drop their own tables in the test database. They don't touch the development database. Run `alembic upgrade head` to build the development tables. |
| Browser shows old behaviour after an edit | Restart uvicorn. |
| Scripts disabled when activating | Run the `Set-ExecutionPolicy` command in step 2. |

## Security notes for local use

- Keep the password out of shared screenshots and documents.
- Clear PowerShell history if a password was typed on the command line: `Clear-History`, then delete the file shown by `(Get-PSReadLineOption).HistorySavePath`.
- The API has no authentication yet. Do not expose it beyond your own machine.