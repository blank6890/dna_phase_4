# Staff login: design

**Date:** 2026-11-13 · **Size:** small change (one feature across schema, API, UI, tests and docs)

## Intent

Only staff may use the Staff Desk (Organiser, Jury, Committee reports). The protection must hold at
the **API**, not only in the browser: a staff action sent straight to the server without a login is
refused. Each official logs in as themselves, so the server knows who acted.

This reverses "login/authentication" being out of scope in the Phase 4 design
(`2026-11-13-eukonkanto-phase4-design.md`).

## Goals / non-goals / anti-goals

- **Goals:** a login page; a separate account for each official; every staff API route returns `401` without a
  valid session; the acting official is taken from the session, never from the request body.
- **Non-goals:** roles (organiser vs jury), sign-up, changing or resetting passwords, limiting repeated
  login attempts, HTTPS/deployment.
- **Anti-goals:** any public page breaking or asking for a login; any staff write still possible without
  a session; passwords stored in plain text.

## Approaches (decided)

| Approach | Trade-off | Decision |
|---|---|---|
| **Flask signed session cookie** + Werkzeug password hashes | Built into Flask, no new dependency; the browser sends the cookie automatically, so `api.js` barely changes | **Chosen** |
| JWT token kept in localStorage | Built for a separate frontend and API on different domains (not our case); needs a new library and an extra header on every request; a token in localStorage can be read by any script on the page | Rejected |
| HTTP Basic auth | No login page (which was the request); no real logout; the password goes with every request | Rejected |

Account model (decided): **one login per official** (option B), not one shared password and no roles.

## Design

### Database
- New table `STAFF_ACCOUNT (Person_ID INT PK → OFFICIAL(Person_ID) ON DELETE CASCADE,
  Username VARCHAR(40) NOT NULL UNIQUE, Password_Hash VARCHAR(255) NOT NULL)`.
- Seeded by `tools/build_populate.py` into `populate.sql`, one row per official (8). Each row is marked
  `-- GENERATED:`. *My call:* username = lower-case first name (with a number added if two officials
  share one); every official has the same demo password, `staff2027`, listed in the README and DEMO.
  Hashes come from `werkzeug.security.generate_password_hash`.
- README design-changes table: new row 11 (table added because login is now in scope).

### Backend
- `config.py`: `SECRET_KEY` from the environment, with a dev default; session cookie set to `HttpOnly`
  (Flask's default) and `SameSite=Lax`, which blocks other sites from sending staff requests with the
  staff member's cookie.
- New auth endpoints:
  - `POST /api/auth/login {username, password}`: checks the hash; on success stores `official_id` in
    the session and returns the official's name. On failure: `401 "Wrong username or password"`
    (the same message whichever field was wrong).
  - `POST /api/auth/logout`: clears the session.
  - `GET /api/auth/me`: returns the logged-in official, or `401`.
- A `staff_required` decorator (it also makes the official's ID available to the route) is applied to every staff route:
  - **Desk reads:** `GET /api/registrations`, `GET /api/protests`, `/api/editions/<y>/persons`,
    `/api/editions/<y>/heaviest-carried`, `/api/reports/<name>`, `GET /api/entries/unregistered`,
    `GET /api/officials`, `GET /api/prizes`.
  - **Staff writes:** `DELETE /api/registrations/<id>` (D1), `DELETE /api/entries/<id>` (D2),
    `POST /api/results` (I2), `PATCH /api/results/...` and `POST /api/penalties` (U1),
    `POST /api/protests` (I3), `POST /api/protests/<id>/decide` (U3), `POST /api/awards` (I4),
    `DELETE /api/booths/...` (D3).
  - **Stays public:** all public reads, `POST /api/registrations` (I1), and the "Manage my registration"
    routes (`GET /api/registrations/<id>`, cancel (U2), replace member (U4)).
- I2/U1: `Recorded_By_Official_ID` comes from the session; any `official_id` in the body is ignored.
- U3 *(my call)*: the logged-in official records the whole panel's votes (the form still lists every jury
  member), since a protest is decided by the panel together, not by whoever is typing.

### Frontend
- New page `/desk/login`: username and password fields, an error message on failure, then a redirect to
  the `?next=` page (default `/desk/organiser`).
- A `StaffProvider` checks `/api/auth/me` once on load; a `RequireStaff` wrapper around the three desk
  routes sends anyone not logged in to `/desk/login?next=…`.
- Menu: the "Staff Desk" group shows **Staff login** when logged out; when logged in it shows the three desk
  links and **Log out (First Last)**.
- `api.js`: a `401` from a staff call clears the login state so the user lands back on the login page
  (e.g. after a server restart with a new secret).
- Jury desk: the "acting official" dropdown is removed; the page header shows who is logged in.
- *My call:* the **remove booth** button (D3) moves from the public Market Place to the Organiser desk
  (the Phase 4 design already lists P3/D3 under `/desk/organiser`); Market Place becomes read-only.

### Tests
- New `tests/test_auth.py`: login success and failure, `me`, logout; every route in the staff list returns
  `401` when not logged in; public routes still answer without a login; a result recorded with a
  forged `official_id` in the body is stored with the session's official.
- Existing desk/jury/write tests log in through a fixture (`staff_client`) before calling staff routes.
- Schema/populate tests: `STAFF_ACCOUNT` exists and has one row per official.

### Docs
- README: design-changes row, staff login section with the demo credentials, updated route table.
- DEMO.md: a login step before the desk sections; show a `401` from a direct API call.
- Phase 4 design: remove login from the out-of-scope line, with a pointer to this file.

## Left to the builder
- Exact markup and styles of the login page (follow `DESIGN.md` and the existing `theme.css`).
- How the decorator passes the official's ID to the route (`flask.g` or an argument).
- Whether the seed hashes are made reproducible (fixed salt) or regenerated each time `populate.sql` is built.
