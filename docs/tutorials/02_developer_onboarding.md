# Tutorial: Developer Onboarding — Setting Up and Extending Horus Analytics

> **Document Type:** Diátaxis Tutorial (Learning-Oriented)  
> **Audience:** Backend Engineers, Full-Stack Developers, Contributing Engineers  
> **Estimated Duration:** 30 minutes  
> **Target System:** Horus Analytics v1.0.0 Architecture  

---

## What You Will Learn

By the end of this tutorial, you will:
1. Configure your local Windows Python 3.13 and Node.js environment.
2. Initialize the SQLite database with Write-Ahead Logging (WAL).
3. Run the automated backend test batches using `scripts/run_backend_tests.py`.
4. Run the application in developer mode without requiring live market feeds.
5. Create a simple test route and verify it through the FastAPI test client.

---

## Step 1: Environment Prerequisites

Ensure the following tools are installed on your Windows machine:
- **Python:** Python 3.13.x (with system PATH configured).
- **Node.js:** v18+ (LTS) & npm.
- **Git:** 2.40+.

Open PowerShell and verify:
```powershell
python --version
node --version
npm --version
```

---

## Step 2: Clone & Install Dependencies

1. Navigate to the project root:
   ```powershell
   cd c:\Users\TSabr\Horus\Horus-Analytics-v1
   ```
2. Install Python packages:
   ```powershell
   python -m pip install -r requirements.txt
   ```
3. Install frontend dependencies:
   ```powershell
   cd frontend
   npm install
   cd ..
   ```

---

## Step 3: Run the Test Suite

Horus includes over 1,000 unit and integration tests grouped into batches for parallel efficiency.

### 1. Fast Health & Watchdog Check:
```powershell
pytest tests/test_health_routes.py tests/test_signal_sla_and_watchdog.py
```
*Expected result: All tests pass in ~30 seconds.*

### 2. Full Batch Runner:
```powershell
python scripts/run_backend_tests.py --collect-only
```
This inspects all active test files mapped to batches.

---

## Step 4: Launching in Development Mode

You do not need a live MetaStock or Mubasher PRO installation to develop features. Horus provides built-in fallback modes.

1. **Start the Backend API:**
   ```powershell
   python -m uvicorn api:app --port 8000 --reload
   ```
2. **Start the Frontend Web App:**
   In a separate terminal:
   ```powershell
   cd frontend
   npm run dev -- --hostname 127.0.0.1 --port 3100
   ```
3. Open your browser:
   - Dashboard: `http://127.0.0.1:3100`
   - Swagger API Docs: `http://127.0.0.1:8000/docs`

---

## Step 5: Adding a Custom API Route

Follow this pattern to add a new route while respecting Horus layering invariants:

1. Open `routes/system.py` or create a new submodule in `routes/`.
2. Define your endpoint using FastAPI `APIRouter`:
   ```python
   from fastapi import APIRouter

   sample_router = APIRouter(tags=["sample"])

   @sample_router.get("/api/v1/sample/ping")
   def ping_endpoint():
       return {"message": "pong", "version": "1.0.0"}
   ```
3. Register the router in `config/route_registry.py`:
   ```python
   app.include_router(sample_router)
   ```
4. Write a unit test in `tests/test_api_endpoints.py`:
   ```python
   def test_sample_ping(client):
       response = client.get("/api/v1/sample/ping")
       assert response.status_code == 200
       assert response.json()["message"] == "pong"
   ```
5. Run the test:
   ```powershell
   pytest tests/test_api_endpoints.py -k "test_sample_ping"
   ```

---

## Core Invariants to Remember

1. **Timezone Rule:** Never call `datetime.now()` for business logic. Always import and use `core.TimeUtils.now()`, which enforces `Africa/Cairo` time.
2. **EGX Session Rule:** Market bars stop at 14:15:00 on EGX. Always query `settings.get_market_session_phase()` before asserting bar freshness.
3. **Database Rule:** Never open direct SQLite connections without using `database.db` or `atomic_write_retry`.

### Next Steps:
- Review [docs/reference/api_endpoints_reference.md](file:///c:/Users/TSabr/Horus/Horus-Analytics-v1/docs/reference/api_endpoints_reference.md) for existing route contracts.
- Review [docs/reference/database_schema_reference.md](file:///c:/Users/TSabr/Horus/Horus-Analytics-v1/docs/reference/database_schema_reference.md) for Peewee models.
