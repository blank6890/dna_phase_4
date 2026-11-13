# Staff Login Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Officials log in with their own account; every Staff Desk API route answers `401` without a session, and the desk pages send logged-out users to a login page.

**Architecture:** A new `STAFF_ACCOUNT` table (one row per official, Werkzeug password hash) seeded in `populate.sql`. Flask's signed session cookie holds `official_id`; a `staff_required` decorator in a new `src/auth.py` guards staff routes and supplies the acting official to I2/U1. React gets a `StaffProvider` context, a `RequireStaff` route wrapper and a `/desk/login` page.

**Tech Stack:** MariaDB, Flask 3.1 sessions, `werkzeug.security` (ships with Flask, no new dependency), React 18 + react-router 6, pytest.

**Spec:** `docs/superpowers/specs/2026-11-13-staff-login-design.md`

## Global Constraints

- No new Python or npm dependencies.
- Raw parameterised SQL only (no ORM), SQL strings live in `src/repo/*.py` like the existing modules; responses use `respond()` / `done()` from `src/api/__init__.py` so the SQL panel keeps working.
- Demo credentials: username = lower-case first name of each official (`matti`, `riitta`, `juha`, `anne`, `pekka`, `jari`, `sari`, `minna`); password `staff2027` for all.
- Seed rows end with `-- GENERATED: staff login`.
- Login failure message, identical for unknown user and wrong password: `Wrong username or password` (401).
- Unauthenticated staff call: `401` with error `Staff login required`.
- Session cookie: `HttpOnly`, `SameSite=Lax`. `SECRET_KEY` from the environment; if unset, a random `secrets.token_hex(32)` per process (sessions end on restart; never a constant in the repo).
- Public routes stay open: all public reads, `POST /api/registrations` (I1), `GET /api/registrations/<id>`, `POST /api/registrations/<id>/cancel` (U2), `PATCH /api/entries/<id>/roles/<role>` (U4).
- Git: work on a branch `staff-login`. The working tree has unrelated uncommitted changes (`.gitignore`, `theme.css`, `requirements.txt`, `DESIGN.md`, `PRODUCT.md`, `voiceover/`, `src/tools/voiceover.py`): `git add` only the files each task names; never `git add -A`.
- Tests run with `cd src && pytest` (MariaDB test DB `eukonkanto_test`); frontend builds with `cd src/frontend && npm run build`.

## Review Focus

1. **Server restarted while a staff tab is open** (new random secret → old cookie invalid): the next desk call gets 401 and the page goes to the login page rather than showing a raw error. Pinned by `test_cookie_from_other_secret_is_401` (Task 2) and the `api.js` 401 event (Task 4).
2. **Username typed with capitals or spaces** (`" Matti "`): login succeeds; usernames are trimmed and lower-cased; the password is not trimmed. Pinned by `test_login_username_case_and_spaces` (Task 2).
3. **After logout, a staff call from the same browser** gets 401. Pinned by `test_logout_ends_session` (Task 2).
4. **Login with a non-text or missing field** (`{"username": 5}`, `{}`, JSON list): 400, never 500. Pinned by `test_login_bad_payload_400` (Task 2).
5. **Login page `?next=` pointing off-site** (`?next=https://evil.example` or `//evil`): ignored, goes to `/desk/organiser`. Only values starting with `/desk/` are followed. Checked in Task 4's manual verification.

---

### Task 1: STAFF_ACCOUNT table and seed

**Files:**
- Modify: `src/schema.sql` (after the `OFFICIAL` table, ~line 72)
- Modify: `src/tools/build_populate.py` (after the `OFFICIAL` insert, ~line 391)
- Regenerate: `src/populate.sql`
- Test: `src/tests/test_schema.py`, `src/tests/test_populate.py`

**Interfaces:**
- Produces: table `STAFF_ACCOUNT (Person_ID INT PK, Username VARCHAR(40) NOT NULL UNIQUE, Password_Hash VARCHAR(255) NOT NULL)`, `fk_staff_account_official` → `OFFICIAL(Person_ID) ON DELETE CASCADE`; 8 seeded rows.

- [ ] **Step 1: Write the failing tests**

In `test_schema.py` add `"STAFF_ACCOUNT"` to `TABLES`. In `test_populate.py`:

```python
def test_one_staff_account_per_official(db_conn):
    assert scalar(db_conn, "SELECT COUNT(*) FROM STAFF_ACCOUNT") == 8
    assert scalar(db_conn, "SELECT COUNT(*) FROM OFFICIAL o LEFT JOIN STAFF_ACCOUNT s USING (Person_ID) "
                           "WHERE s.Person_ID IS NULL") == 0

def test_staff_passwords_hashed(db_conn):
    from werkzeug.security import check_password_hash
    rows = q(db_conn, "SELECT Username, Password_Hash FROM STAFF_ACCOUNT ORDER BY Person_ID")
    assert [r["Username"] for r in rows] == ["matti", "riitta", "juha", "anne", "pekka", "jari", "sari", "minna"]
    assert all(check_password_hash(r["Password_Hash"], "staff2027") for r in rows)
    assert not any("staff2027" in r["Password_Hash"] for r in rows)
```

(import `q`, `scalar` from `conftest` if not already.)

- [ ] **Step 2: Run to verify they fail**

Run: `cd src && pytest tests/test_schema.py::test_all_tables_exist tests/test_populate.py -k "staff or all_tables" -v`
Expected: FAIL (table missing).

- [ ] **Step 3: Add the table to `schema.sql`** with the columns and FK above, in the same style as `OFFICIAL`.

- [ ] **Step 4: Seed it from `build_populate.py`**

Add `o.insert("STAFF_ACCOUNT", ["Person_ID", "Username", "Password_Hash"], ...)` with note `f"{GEN}: staff login"`, username `first.lower()`. The script must stay deterministic, so don't use `generate_password_hash` (random salt). Instead add a helper that writes Werkzeug's own scrypt format with a salt derived from the username:

```python
def staff_hash(username: str, password: str = "staff2027") -> str:
    """Werkzeug-compatible scrypt hash with a deterministic salt (keeps populate.sql reproducible)."""
    n, r, p = 2**15, 8, 1
    salt = hashlib.sha256(f"staff:{username}".encode()).hexdigest()[:16]
    digest = hashlib.scrypt(password.encode(), salt=salt.encode(), n=n, r=r, p=p, maxmem=132 * n * r * p, dklen=64)
    return f"scrypt:{n}:{r}:{p}${salt}${digest.hex()}"
```

- [ ] **Step 5: Regenerate** — `cd src && python tools/build_populate.py > populate.sql`, then `git diff --stat src/populate.sql`: only the new STAFF_ACCOUNT block should appear. Run the script a second time to confirm no further diff.

- [ ] **Step 6: Run the full backend suite** — `cd src && pytest -q`. Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add src/schema.sql src/tools/build_populate.py src/populate.sql src/tests/test_schema.py src/tests/test_populate.py
git commit -m "feat(db): STAFF_ACCOUNT table with one login per official"
```

---

### Task 2: Login, logout, session and the `staff_required` guard

**Files:**
- Create: `src/auth.py`, `src/repo/staff.py`, `src/tests/test_auth.py`
- Modify: `src/config.py`, `src/app.py` (`create_app`), `src/tests/conftest.py`

**Interfaces:**
- Consumes: `STAFF_ACCOUNT` (Task 1).
- Produces:
  - `repo/staff.py`: `account(username: str) -> dict | None` (keys `Person_ID, Username, Password_Hash, First_Name, Last_Name, Duty_Title`), `official(person_id: int) -> dict | None` (same minus `Password_Hash`), module constants `ACCOUNT_SQL`, `OFFICIAL_SQL`.
  - `auth.py`: `staff_required(view)` decorator (raises `ApiError(401, "Staff login required")` when `session.get("official_id")` is missing); `current_official_id() -> int` (reads the session; only called inside guarded views); `register_auth_routes(app)`.
  - `config.py`: `get_secret_key() -> str`.
  - Routes: `POST /api/auth/login` → `done("Logged in", ACCOUNT_SQL, official={...})`; `POST /api/auth/logout` → `done("Logged out")`; `GET /api/auth/me` → `respond([], OFFICIAL_SQL, official={...})` or 401. `official` object keys: `Person_ID, Username, First_Name, Last_Name, Duty_Title`.
  - Fixtures: `client` and `wclient` are now **logged in as `matti`**; new `anon` (read-only DB, no login) and `wanon` (fresh DB, no login). `STAFF = ("matti", "staff2027")` constant in `conftest.py`.

- [ ] **Step 1: Write the failing tests** in `test_auth.py`:

```python
def test_login_ok_and_me(anon):
    r = anon.post("/api/auth/login", json={"username": "matti", "password": "staff2027"})
    assert r.status_code == 200 and r.get_json()["official"]["First_Name"] == "Matti"
    assert anon.get("/api/auth/me").get_json()["official"]["Username"] == "matti"

def test_login_wrong_password_and_unknown_user_same_message(anon):
    a = anon.post("/api/auth/login", json={"username": "matti", "password": "nope"})
    b = anon.post("/api/auth/login", json={"username": "nobody", "password": "staff2027"})
    assert a.status_code == b.status_code == 401
    assert a.get_json()["error"] == b.get_json()["error"] == "Wrong username or password"
    assert anon.get("/api/auth/me").status_code == 401

def test_login_username_case_and_spaces(anon):
    assert anon.post("/api/auth/login", json={"username": " Matti ", "password": "staff2027"}).status_code == 200

def test_login_bad_payload_400(anon):
    for payload in ({}, {"username": 5, "password": "x"}, {"username": "matti", "password": 5}, [1, 2]):
        assert anon.post("/api/auth/login", json=payload).status_code == 400

def test_logout_ends_session(client):
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401

def test_cookie_flags(anon):
    r = anon.post("/api/auth/login", json={"username": "matti", "password": "staff2027"})
    cookie = r.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie

def test_cookie_from_other_secret_is_401(anon):
    anon.post("/api/auth/login", json={"username": "matti", "password": "staff2027"})
    from app import create_app
    other = create_app(); other.testing = True                # new random secret
    c2 = other.test_client()
    c2.set_cookie("session", anon.get_cookie("session").value)
    assert c2.get("/api/auth/me").status_code == 401
```

- [ ] **Step 2: Run to verify they fail** — `cd src && pytest tests/test_auth.py -v`. Expected: FAIL (fixtures/routes missing).

- [ ] **Step 3: Implement**
  - `config.get_secret_key()`: `os.environ.get("SECRET_KEY") or secrets.token_hex(32)`.
  - `create_app`: `app.secret_key = get_secret_key()`, `app.config["SESSION_COOKIE_SAMESITE"] = "Lax"`, call `register_auth_routes(app)`.
  - Login: read `body()`; `username` via `as_str(..., max_len=40)` then `.lower()`; `password` must be `str` of length 1–200 (not stripped) else `ApiError(400, "password is required")`. Look up with `staff.account`; on miss or `not check_password_hash(...)` → `ApiError(401, "Wrong username or password")`. On success `session.clear()` then `session["official_id"] = Person_ID`.
  - `me`: `staff.official(session id)`; missing session or deleted official → 401 `Staff login required` (and `session.clear()`).
  - Fixtures: `client`/`wclient` build the app as today, then POST the `STAFF` login and assert 200; `anon`/`wanon` are today's fixtures unchanged.

- [ ] **Step 4: Run** — `cd src && pytest -q`. Expected: all pass (existing tests now run logged in).

- [ ] **Step 5: Commit**

```bash
git add src/auth.py src/repo/staff.py src/config.py src/app.py src/tests/conftest.py src/tests/test_auth.py
git commit -m "feat(api): staff login, logout and session"
```

---

### Task 3: Lock the staff routes; acting official from the session

**Files:**
- Modify: `src/app.py` (`register_desk_routes`, `register_registration_routes`, `register_jury_routes`), `src/repo/results.py` (`record_result`, `correct_result`, `add_penalty`)
- Test: `src/tests/test_auth.py`, `src/tests/test_api_jury.py`

**Interfaces:**
- Consumes: `staff_required`, `current_official_id()` (Task 2); fixtures `client`, `wclient`, `anon`, `wanon`.
- Produces: `results.record_result(payload, official_id: int)`, `results.correct_result(reg, stage, payload, official_id: int)`, `results.add_penalty(payload, official_id: int)`. The body's `official_id` is no longer read.

- [ ] **Step 1: Write the failing tests** in `test_auth.py`:

```python
STAFF_ROUTES = [
    ("GET", "/api/registrations?year=2026&series=MAIN"), ("GET", "/api/protests?status=Pending"),
    ("GET", "/api/editions/2026/persons"), ("GET", "/api/editions/2026/heaviest-carried"),
    ("GET", "/api/reports/medals"), ("GET", "/api/reports/registrations-by-country?year=2026"),
    ("GET", "/api/entries/unregistered"), ("GET", "/api/officials"), ("GET", "/api/prizes?series=MAIN"),
    ("DELETE", "/api/registrations/1"), ("DELETE", "/api/entries/1"),
    ("POST", "/api/results"), ("PATCH", "/api/results/1/Single"), ("POST", "/api/penalties"),
    ("POST", "/api/protests"), ("POST", "/api/protests/1/decide"), ("POST", "/api/awards"),
    ("DELETE", "/api/booths/8/2027"),
]

@pytest.mark.parametrize("method,url", STAFF_ROUTES)
def test_staff_route_needs_login(wanon, method, url):
    r = wanon.open(url, method=method, json={})
    assert r.status_code == 401 and r.get_json()["error"] == "Staff login required"

PUBLIC_ROUTES = ["/api/editions", "/api/results?year=2026&series=MAIN", "/api/records", "/api/champions",
                 "/api/grand-prix", "/api/entries?year=2027&series=MAIN", "/api/teams",
                 "/api/search/persons?q=ta", "/api/vendors", "/api/editions/2027/booths"]

@pytest.mark.parametrize("url", PUBLIC_ROUTES)
def test_public_reads_need_no_login(anon, url):
    assert anon.get(url).status_code == 200

def test_manage_my_registration_needs_no_login(wanon, fresh_db):
    rid = scalar(fresh_db, "SELECT Registration_ID FROM REGISTRATION WHERE Edition_Year=2027 AND Bib_No=20")
    assert wanon.get(f"/api/registrations/{rid}").status_code == 200
    assert wanon.post(f"/api/registrations/{rid}/cancel").status_code == 200

def test_result_official_comes_from_session(wclient, fresh_db):
    matti = scalar(fresh_db, "SELECT Person_ID FROM STAFF_ACCOUNT WHERE Username='matti'")
    rid = scalar(fresh_db, "SELECT Registration_ID FROM REGISTRATION WHERE Edition_Year=2026 AND Bib_No=49")
    forged = matti + 1
    assert wclient.patch(f"/api/results/{rid}/Single", json={"raw_time_s": 60.0, "official_id": forged}).status_code == 200
    assert scalar(fresh_db, "SELECT Recorded_By_Official_ID FROM RESULT WHERE Registration_ID=%s AND Stage='Single'",
                  (rid,)) == matti
```

In `test_api_jury.py::test_u1_correct_time_reranks_and_reawards`, change the last assertion to expect matti's `Person_ID` (the logged-in official) instead of the timekeeper; drop `official_id` from that test's request body.

- [ ] **Step 2: Run to verify they fail** — `cd src && pytest tests/test_auth.py tests/test_api_jury.py -v`. Expected: the staff-route and session-official tests FAIL.

- [ ] **Step 3: Implement** — add `@staff_required` under each route decorator for exactly the routes in `STAFF_ROUTES` (put it below `@app.get/...`). Pass `current_official_id()` into the three results functions and remove their `payload.get("official_id")` parsing.

- [ ] **Step 4: Run** — `cd src && pytest -q`. Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/app.py src/repo/results.py src/tests/test_auth.py src/tests/test_api_jury.py
git commit -m "feat(api): staff routes require login; acting official from session"
```

---

### Task 4: Login page, staff context and guarded desk routes

**Files:**
- Create: `src/frontend/src/components/staff.jsx`, `src/frontend/src/pages/desk/Login.jsx`
- Modify: `src/frontend/src/api.js`, `src/frontend/src/App.jsx`, `src/frontend/src/main.jsx`, `src/frontend/src/components/Layout.jsx`, `src/frontend/src/theme.css` (login form styles only, if existing classes don't cover it)

**Interfaces:**
- Consumes: `/api/auth/login|logout|me` (Task 2).
- Produces (`components/staff.jsx`):
  - `StaffProvider({ children })`: on mount `GET /api/auth/me`; state `{ staff: official | null, ready: boolean }`; listens for `window` event `"staff:unauthorized"` → `staff = null`.
  - `useStaff() -> { staff, ready, login(username, password): Promise<void>, logout(): Promise<void> }` (`login` throws with the server's error message).
  - `RequireStaff({ children })`: while `!ready` render nothing; if `!staff` → `<Navigate to={"/desk/login?next=" + encodeURIComponent(pathname)} replace />`.
- `api.js`: in `handle`, on `res.status === 401` dispatch `new Event("staff:unauthorized")` on `window` before throwing (skip for `/api/auth/login` so a wrong password doesn't reset state; `handle` will need the path passed in).

- [ ] **Step 1: Implement `staff.jsx` and the 401 event in `api.js`.** Wrap `<App />` in `<StaffProvider>` inside `BrowserRouter` in `main.jsx`.

- [ ] **Step 2: Implement `Login.jsx`** at route `/desk/login`: heading "Staff login", fields Username / Password (`autoComplete="username"` / `"current-password"`), submit "Log in", `<Alert>` with the error. On success navigate to `next` if it starts with `/desk/` and is not `/desk/login`, else `/desk/organiser`. If already logged in, redirect the same way. Follow `DESIGN.md` and existing `.field` / `.btn` classes.

- [ ] **Step 3: Guard routes in `App.jsx`** — wrap the three desk elements in `<RequireStaff>`; add the `/desk/login` route.

- [ ] **Step 4: Menu in `Layout.jsx`** — `MENU`'s Staff Desk group renders from `useStaff()`: logged out → one item "Staff login" (`/desk/login`); logged in → the three desk links plus a "Log out (First Last)" button that calls `logout()` and navigates to `/`.

- [ ] **Step 5: Verify** — `cd src/frontend && npm test && npm run build` (no errors). Start Flask (`cd src && python app.py`) and check in the browser:
  1. `/desk/jury` logged out → login page with `?next=%2Fdesk%2Fjury`; log in as `matti` / `staff2027` → lands on Jury desk; menu shows "Log out (Matti Hyvönen)".
  2. Wrong password → "Wrong username or password", stays on page.
  3. `/desk/login?next=https://evil.example` and `?next=//evil` → after login goes to `/desk/organiser`.
  4. Restart Flask, click a desk action → back on the login page.
  5. Log out → menu shows "Staff login"; public pages (Results, Register, Manage my registration) work.

- [ ] **Step 6: Commit**

```bash
git add src/frontend/src/components/staff.jsx src/frontend/src/pages/desk/Login.jsx src/frontend/src/api.js \
        src/frontend/src/App.jsx src/frontend/src/main.jsx src/frontend/src/components/Layout.jsx
git commit -m "feat(ui): staff login page and guarded desk routes"
```

(`theme.css` has unrelated uncommitted edits: if login styles were needed, use `git add -p src/frontend/src/theme.css` and stage only the login hunks.)

---

### Task 5: Jury uses the logged-in official; booth removal moves to the Organiser desk

**Files:**
- Modify: `src/frontend/src/pages/desk/Jury.jsx`, `src/frontend/src/pages/desk/Organiser.jsx`, `src/frontend/src/pages/Market.jsx`

**Interfaces:**
- Consumes: `useStaff()` (Task 4); results routes no longer read `official_id` (Task 3).

- [ ] **Step 1: Jury** — remove the "Acting official" select, the `official` state, the "Choose the acting official first" check and every `official_id` sent in request bodies (`RowActions`, `RecordResult`, penalties). Show `Recording as {staff.First_Name} {staff.Last_Name}` in the toolbar. Keep the `/api/officials` fetch (it feeds the protest vote list) and the panel vote form unchanged.

- [ ] **Step 2: Move `Bookings`** — cut the `Bookings` component out of `Market.jsx` into `Organiser.jsx` as a new "Market booth bookings" section (same table, the "Remove booking" button, its own message/error/SQL state). Market Place keeps `VendorSearch` and adds a read-only booth list for the selected edition: the same `DataTable` without the action column.

- [ ] **Step 3: Verify** — `cd src/frontend && npm run build`; in the browser, logged in: record a result on the Jury desk (no official picker, succeeds); remove an unpaid 2027 booking on the Organiser desk; Market Place shows bookings with no remove button; logged out, Market Place still loads.

- [ ] **Step 4: Commit**

```bash
git add src/frontend/src/pages/desk/Jury.jsx src/frontend/src/pages/desk/Organiser.jsx src/frontend/src/pages/Market.jsx
git commit -m "feat(ui): jury acts as the logged-in official; booth removal on organiser desk"
```

---

### Task 6: Documentation

**Files:**
- Modify: `README.md`, `DEMO.md`, `docs/superpowers/specs/2026-11-13-eukonkanto-phase4-design.md`

- [ ] **Step 1: README** — design-changes table row 11: `New STAFF_ACCOUNT (Person_ID → OFFICIAL, Username UNIQUE, Password_Hash)` / reason `Staff Desk requires a login per official`. Under setup: a "Staff login" section with the credentials table (Global Constraints) and the `SECRET_KEY` env var (unset = random per run, logins end on restart). Replace the "there is no login; anyone running the app locally acts as staff" sentence (~line 136). Move D3 from Market Place to Desk › Organiser in the requirement/route tables. Mention that STAFF_ACCOUNT rows are generated.
- [ ] **Step 2: DEMO.md** — add a step before the first desk step: open `/desk/organiser` logged out → login page; log in as `matti`. Add one line showing `curl -i -X DELETE http://localhost:5000/api/registrations/1` → `401 Staff login required`. In step 7 (I2) drop "Choose the acting official". Move the D3 step to Desk › Organiser.
- [ ] **Step 3: Phase 4 design** — remove "login/authentication" from the out-of-scope line, adding `(added later: see 2026-11-13-staff-login-design.md)`.
- [ ] **Step 4: Final check** — `cd src && pytest -q` and `cd src/frontend && npm test && npm run build`; all green.
- [ ] **Step 5: Commit**

```bash
git add README.md DEMO.md docs/superpowers/specs/2026-11-13-eukonkanto-phase4-design.md docs/superpowers/specs/2026-11-13-staff-login-design.md docs/superpowers/plans/2026-11-13-staff-login.md
git commit -m "docs: staff login in README, demo script and design"
```
