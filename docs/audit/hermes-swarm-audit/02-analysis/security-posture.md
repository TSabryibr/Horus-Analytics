# Layer 2: Security & Integrity Analysis (Amended)

**Author:** `security-engineer`  
**System:** Horus Analytics II (`c:\Users\TSabr\Horus\Horus-Analytics-II`)  
**Context:** **Single-Operator Local Terminal** (Non-shared, proprietary trading & signal dispatch workstation)

---

## 1. Threat Model for a Local Admin Terminal

In a single-user local deployment where the admin is the sole operator and sells the **outputs** (signals/services) rather than the application itself:

- **Enterprise SaaS Auth is Unnecessary:** Requiring complex API keys, JWTs, or session cookies between the local frontend and local backend adds artificial friction to an active trading console.
- **The True Threat Surface:**
  1. **Network Boundary Exposure:** If Uvicorn or the API accidentally binds to `0.0.0.0` or a public IP, anyone on the local Wi-Fi / network could send commands to the terminal.
  2. **Browser-Originated Cross-Site Attacks (CSRF):** If the trader visits external websites while Horus is running on `http://localhost:8200`, a wildcard CORS (`*`) policy might allow malicious scripts on third-party sites to issue background fetch requests against local endpoints.
  3. **Outbound Credential Stability:** The commercial value of the business relies on signals landing in subscribers' Telegram chats. Corrupted tokens or connection dropping directly impairs revenue.

```
       [Trader Browsing Web]                [Local Wi-Fi Network]
                 │                                    │
                 ▼                                    ▼
       (Third-Party Website)               (Other Devices on LAN)
                 │                                    │
       [Fetch to localhost:8200?]           [Direct HTTP to Host?]
                 │                                    │
       ┌─────────┴─────────┐                ┌─────────┴─────────┐
       │ CORS Protection   │                │ Loopback Binding  │
       │ (Origin Check)    │                │ (127.0.0.1 Only)  │
       └───────────────────┘                └───────────────────┘
```

---

## 2. Pragmatic Hardening Recommendations

### 1. Enforce Strict Loopback Binding (`127.0.0.1`)
- **Location:** [`api.py:L259`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/api.py#L259) & [`.env:L8`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/.env#L8)
- **Current State:** `HOST` defaults to `127.0.0.1`.
- **Recommendation:** Keep `HOST=127.0.0.1` hardcoded for local operations so the port is never opened to external network interfaces.

### 2. Tighten CORS from Wildcard `*` to Localhost
- **Location:** [`.env:L9`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/.env#L9) & [`config/middleware.py:L60-L80`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config/middleware.py#L60-L80)
- **Current State:** `.env` sets `CORS_ALLOWED_ORIGINS=*`.
- **Recommendation:** Restrict to explicit local development origins:
  ```env
  CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8200,http://127.0.0.1:8200
  ```
  This prevents any external tab opened in Chrome/Edge from issuing background requests to your trading terminal.

### 3. Outbound Signal Broadcast Health & Telegram Token Protection
- **Location:** [`.env:L32-L42`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/.env#L32-L42)
- **Context:** The Telegram bot tokens represent the direct pipeline to your paying subscribers.
- **Recommendation:** 
  - Ensure `.env` is never committed to public git repositories (verified: `.env` is properly present in `.gitignore`).
  - Add a connection health-check job to verify Telegram bot reachability before market open (09:45 Cairo Time).

### 4. Sanitize `harvester_service.py` Process Termination
- **Location:** [`data_engine/harvester_service.py:L271`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/data_engine/harvester_service.py#L271)
- **Recommendation:** Replace `shell=True` with explicit token arrays:
  ```python
  subprocess.run(["taskkill", "/F", "/PID", str(int(pid))], shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  ```

---

## SOURCES (LAYER 3 NAVIGATION)

- [`03-dossiers/vulnerability-catalog.md`](file:///C:/Users/TSabr/.gemini/antigravity/brain/c45fd366-d276-45c2-8215-42dfda3dbf44/03-dossiers/vulnerability-catalog.md)  
  $\rightarrow$ Code-level patch diffs for local CORS tightening and subprocess hardening.
