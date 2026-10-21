# Testing

The backend has 125 automated tests, written with pytest and FastAPI's `TestClient`. They run against a separate PostgreSQL database, `early_intervention_test`, and never touch the development data. The tests exercise the API as a client would: requests go in, responses come out, and the database state is checked where it matters.

## Running the tests

From the `backend` folder, with `.venv` active:

```powershell
python -m pytest -q
```

Expected result: `125 passed`. The run takes about 1 to 2 minutes, because each test logs in and writes to the database.

For the full list of test names:

```powershell
python -m pytest -v
```

To run one file:

```powershell
python -m pytest tests/test_permissions.py -v
```

Run pytest from `backend`, not the project root. The `pytest.ini` file in `backend` sets the import path, so tests can import `app`. Running from the wrong folder produces `No module named 'app'`.

## Test database

The test suite needs