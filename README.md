# Wife-Carrying World Championship: Phase 4

Team 69's Mini World is the **Wife Carrying World Championships** in Sonkajärvi, Finland
(<https://eukonkanto.fi/en/>). This phase turns the Phase 3 relational schema into a populated
MariaDB database and a web application modelled on that site. All 32 functional requirements from
our Phase 1 document run as raw, parameterised SQL from a Python backend and are triggered from the UI.

## Stack

| Part | Technology and version |
|---|---|
| Paradigm / DBMS | Relational, **MariaDB 13.0.2** (MySQL-compatible; scripts run with the `mysql`/`mariadb` client) |
| Query language | SQL (raw strings with `%s` parameters, no ORM or query builder) |
| Python driver | PyMySQL 1.2.4 |
| Backend | Python 3.14, Flask 3.1.3 (JSON API under `/api`, also serves the built frontend) |
| Frontend | React 18.3.1 + react-router-dom 6.28.0, built with Vite 6.3.5 (plain CSS, Barlow fonts) |
| Tests | pytest 9.2.0 against a separate `eukonkanto_test` database; vitest 2.1.8 for frontend helpers |

## Design changes

Phase 1: Team 69 (us) · **Phase 2: Team 65** · **Phase 3: Team 56**.

The Phase 3 schema (30 relations) is the baseline. Table and column names, the composite keys of
the weak entities (RACE, RESULT, PENALTY) and the ternary PARTICIPATES_AS are unchanged. The changes:

| # | Change | Reason |
|---|---|---|
| 1 | Surrogate keys (Person, Entry, Registration, Protest, Prize, Venue, Sponsor, Vendor, GP_Event) are `INT AUTO_INCREMENT` instead of VARCHAR; natural codes (ISO_Code `CHAR(3)`, Series_Code, Role_Code) stay text | The web app creates rows, so the database must generate the keys |
| 2 | `PERSON.Date_of_Birth` and `Gender` nullable; `Email` nullable but `UNIQUE` | The site publishes no birth date, gender or e-mail for champions back to 1992 (Phase 2 flagged the Email problem) |
| 3 | `REGISTRATION.Bib_No` nullable with `UNIQUE (Edition_Year, Bib_No)` and a CHECK that a cancelled registration has no bib | "Bib unique within an edition, released on cancellation" (Phase 1) enforced declaratively |
| 4 | Times and money `DECIMAL` instead of FLOAT (`Raw_Time_s DECIMAL(7,2)`, `*_EUR DECIMAL(8,2)`, weights `DECIMAL(5,1)`, `Track_Length_m DECIMAL(6,1)`) | Sprint times have hundredths, the track is 253.5 m, money must be exact |
| 5 | `EDITION.Registration_Deadline` DATE → DATETIME | The real deadline is "Wednesday 30 June 2027 at 10 pm" |
| 6 | New `SERIES.Has_Heats BOOLEAN` | Phase 1 rule "heat stages only in a series with heats" had nothing to check against |
| 7 | New `RACE.Last_Finish_At DATETIME NULL` | Phase 1 rule "protest within 15 minutes of the last finisher" needs a stored finish time |
| 8 | New `UNIQUE (Edition_Year, Series_Code)` on RACE | Phase 1 rule "at most one race per series per edition" |
| 9 | Fixed-domain VARCHARs become ENUM/CHECK (Entry_Type, Payment_Status, result Status, Stage, Adjustment_Type, Outcome, Vote, Prize_Type, Prize_Scope, Booth_Size, Category, Duty, Championship_Level, Gender, Continent); other type refinements: `Bib_No SMALLINT`, `Certified_Since SMALLINT`, `Event_Month_Year DATE` (first day of the month) | Phase 1/2 defined these domains; Phase 3 left them as free text |
| 10 | `OFFICIAL.Person_ID`, `OFFICIAL.Supervisor_ID` and `PARTICIPATES_AS.Role_Code` foreign keys are `RESTRICT` (not CASCADE/SET NULL) | MariaDB forbids a CHECK on a column whose FK has a cascading action (error 1901); those columns carry CHECKs (supervisor ≠ self, weight only for the carried role) |
| 11 | New `STAFF_ACCOUNT (Person_ID → OFFICIAL, Username UNIQUE, Password_Hash)`, one row per official | The Staff Desk now requires a login per official, so the server knows who recorded each result |

**Kept as in Phase 3:** registration status is derived from `Cancelled_At` (no stored Status column);
QUALIFIES stays as Phase 3's nullable `ENTRY.GP_Event_ID`; there is no protest-fee column (150 € is a
business rule, used as a constant in the income report).

**Added rules, from the Phase 1 "Enforcement" column:**

- **Triggers** (each raises `SQLSTATE '45000'` with a sentence the UI shows as is):
  - registration: inside the registration window; entry's roles match the series (1 or 3 carriers + 1 carried); ages on race day (18 / 40 for +40 / 17); fee equals the race fee
  - cancelling: refused once results exist; releases the bib
  - team change: refused once results exist; re-checks age and pair/team roles
  - results: no result for a cancelled registration; heats and final only in the Sprint
  - protests: within 15 minutes of the last finisher; the entry must have raced
  - awards: the series must offer the prize; a placement prize must match the actual rank
  - booths: standard booth prices (70 € / 140 €) unless the booth is food or custom
- **Views:** derived attributes are computed, never stored:
  - `v_result`: net time, rank (ties share a rank) and gap, using window functions
  - `v_entry_name`: display name "carriers / carried" and countries
  - `v_registration`: status, refund under the 30-day rule, and the required backpack weight
- **Delete rules:** RESTRICT by default; CASCADE only down REGISTRATION → RESULT → PENALTY, ENTRY →
  PARTICIPATES_AS/REPRESENTS, and from owners to their multivalued attributes.

## Data

`populate.sql` loads **with every trigger active**, so loading it also checks that the data obeys the rules.

**From eukonkanto.fi:**
- The complete **2026 results**:
  - Sprint heats 1–3 and final
  - Main series: 45 pairs, including 2 DNS
  - Women's (with a DNS), +40 and Team, with Team 105's real +15 s penalty
- Real bib numbers and multi-country entries.
- **Champions 1992–2026** (Main, Sprint, Team) and the **world records**. Main-series winning times
  come from Wikipedia, which cites the official archive.
- The **2027 registrations**.
- Series rules and fees, programme times, venues and facilities, partners, booth prices, and the
  official Grand Prix events (including the 2026 UK qualifier in Kirkcudbright).

**Generated (every such row ends with `-- GENERATED:` in `populate.sql`):**
- Birth dates of recent competitors (each meets its series' age rules) and the carried people's
  weights (a few under 49 kg).
- 8 officials and their Staff Desk logins, 4 protests and their votes, 2026 special prizes, 9 market vendors and their bookings,
  e-mail addresses for 2027 registrants, and edition dates other than 2026/2027.
- Sprint and Team champion times, which are not published; they are always slower than the official record.
- One cancelled registration and one entry with no registration, for the demos.

**Departures from the published data:**
- Wikipedia's 2000–2001 Main times (55.5 / 55.6 s) are faster than the site's official record (56.9 s,
  2006), so those two are generated as slower times.
- The 2001 team champion has no archived members and is omitted.
- For older years the site lists only winners, so historic medal tables show mostly gold.

`src/tools/build_populate.py` regenerates `populate.sql` from the data files in `src/tools/data/`.
The committed `populate.sql` is the deliverable.

## Setup and run

1. **Install and start MariaDB**, then create the app's user (one time, needs sudo):
   ```bash
   sudo pacman -S mariadb                       # or your distribution's mariadb/mysql package
   sudo mariadb-install-db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
   sudo systemctl enable --now mariadb
   sudo mariadb -e 'CREATE USER IF NOT EXISTS "phase4"@"localhost" IDENTIFIED BY "phase4";
                    GRANT ALL PRIVILEGES ON `eukonkanto\_%`.* TO "phase4"@"localhost"; FLUSH PRIVILEGES;'
   ```
2. **Create and fill the database** (from the repository root; the schema script drops and
   recreates `eukonkanto_db`):
   ```bash
   mysql -u phase4 -p < src/schema.sql        # password: phase4
   mysql -u phase4 -p < src/populate.sql
   ```
3. **Install the Python dependencies** (from the repository root; versions above are the ones tested):
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r src/requirements.txt
   ```
4. **Build the frontend** (Node 18 or newer), then return to the root:
   ```bash
   cd src/frontend && npm install && npm run build && cd ../..
   ```
5. **Start the app** with the virtual environment active: `cd src && python app.py`, then open
   **<http://localhost:5000>**.

Credentials come from the environment variables `DB_HOST`, `DB_USER`, `DB_PASS` and `DB_NAME`
(defaults: `localhost`, `phase4`, `phase4`, `eukonkanto_db`; see `src/config.py`).
For frontend development, run `npm run dev` in `src/frontend` (port 5173, proxies `/api` to Flask).

**Staff login.** The Staff Desk pages (`/desk/...`) and their API routes need a login; without one the
API answers `401 Staff login required`. Each official has an account (generated demo data, password
stored only as a hash):

| Username | Official | Password |
|---|---|---|
| `matti` | Matti Hyvönen, Chief Judge | `staff2027` |
| `riitta`, `juha` | Jury Members | `staff2027` |
| `anne`, `pekka` | Timekeepers | `staff2027` |
| `jari` | Starter | `staff2027` |
| `sari`, `minna` | Info Desk Officers | `staff2027` |

The session cookie is signed with `SECRET_KEY` from the environment. If it is unset, a random key is
made at start-up, so restarting the server logs everyone out. Results and penalties are stored with the
logged-in official as recorder. Public pages, registering and "Manage my registration" need no login.

**Tests:**
- Backend: `cd src && pytest`. It rebuilds the separate `eukonkanto_test` database from the two
  scripts, so `eukonkanto_db` is untouched.
- Frontend helpers: `cd src/frontend && npm test`.

Every page has a **Show SQL** panel with the exact parameterised SQL the backend ran for it.

## Features

The order matches the demo video: writes first, then reads. The Staff Desk pages
(`/desk/...`) stand in for the organiser, jury and committee screens that Phase 1 describes. They
need a staff login (see "Staff login" above).

**Insert, update and delete**

1. **Register a pair or team (I1):** Register page (`/register`).
   - Choose the series, then for each role pick an existing person or enter a new one, and give the
     carried person's weight. Press "Register and pay".
   - One transaction inserts any new PERSON/COMPETITOR/citizenship, the ENTRY (or reuses the pair's
     existing entry), the PARTICIPATES_AS and REPRESENTS rows, and the REGISTRATION with the next free
     bib and the race's fee.
   - Triggers check the deadline, roles, ages and fee. Any failure rolls everything back and shows
     the reason, e.g. "Carrier must be at least 18 on race day for series MAIN".
2. **Cancel a registration (U2):** Manage my registration (`/my-registration?id=<no>`), "Cancel registration".
   - Sets `Cancelled_At`, releases the bib and applies the 30-day refund rule (fee − 10 €).
   - Refused once results exist.
3. **Replace a member (U4):** Manage my registration, "Replace" on a role.
   - Puts another person in that role.
   - The trigger re-checks ages and the pair/team shape, and refuses once the entry has results.
4. **Delete a registration that never ran (D1):** Staff Desk › Organiser (`/desk/organiser`), "Delete" on a registration.
   - Allowed only for a live registration with no results and no awards.
   - Otherwise shows "Registration has results", "Registration has awards" or "Registration is cancelled".
5. **Delete an entry with no registrations (D2):** Organiser, "Entries with no registrations", "Delete entry".
   - Its roles and countries cascade; the people stay.
   - The foreign key refuses entries that are still registered.
6. **Remove an unpaid booth booking (D3):** Staff Desk › Organiser, "Market booth bookings", "Remove booking".
   - Only unpaid bookings before the event.
   - The vendor is deleted too when it has no other booking.
7. **Record a result (I2):** Staff Desk › Jury (`/desk/jury`). Choose the race, then use "Record a
   result". The logged-in official is stored as recorder.
   - Inserts the RESULT.
   - Triggers refuse a cancelled registration or a stage the series does not have.
8. **Correct a time or add a penalty (U1):** Jury, "Edit time" or "Add penalty" on a result.
   - Ranks and gaps update everywhere, because they come from `v_result`.
   - Placement prizes for that race are re-assigned in the same transaction, and the logged-in official is stored as recorder.
9. **File a protest (I3):** Jury, "File a protest". Choose the entry, the time and the reason.
   - The trigger requires the time to be within 15 minutes of the race's last finisher and the entry to have raced.
10. **Decide a protest (U3):** Jury, "Pending protests", "Record decision".
    - Stores the outcome, the decision time and each jury vote.
    - If upheld, it can remove the contested penalty or disqualify a result; ranks and prizes then update.
11. **Award a prize (I4):** Organiser, "Award a prize…" on a registration.
    - The trigger checks that the series offers the prize and that a placement prize matches the actual rank.

**Queries**

12. **Sprint final results (S3):** Results (`/results?year=2026&series=SPR`), Sprint tab, "Final"
    (also Heats 1–3). Complete result rows for the chosen edition's Sprint final: rank, bib, pair,
    country, time and difference. The other tabs show every series of any edition.
13. **World records (A1):** Champions and Records (`/results/champions-and-records`). The fastest net
    time in each series across all editions, with the holders and the year (matches the site).
    The page also lists every gold medallist since 1992.
14. **Search people (Q1):** the header search box (`/search?q=kirk`). Partial match on first name, last
    name or full name, so "kirk" finds Kirkliauskas. Each person links to their competition history
    (`/people/<id>`).
15. **Search teams and organisations (Q2):** same results page, "Teams and organisations" section.
    Partial match on team name or represented organisation.
16. **Entries by country and series (Q3):** Registered Competitors (`/competitors`). Choose the
    edition and series tab, type a country code (e.g. GBR) and press "Filter".
17. **Teams and their organisations (P2):** Registered Competitors, "Teams" tab. Shows only the team
    name and the organisation it represents.
18. **Find vendors (Q4):** Market Place, "Find a vendor". Part of the business name and/or a product
    category (Food, Handicrafts, Local specialities).
19. **Booth size and fee per vendor (P3):** Market Place, booth bookings for the chosen edition (read-only; the Organiser desk has the same table with "Remove booking").
20. **Registrations for one race (S1):** Organiser, choose the edition and series tab. Complete
    registration rows: bib, entry, time registered, payment, refund, backpack.
21. **People registered in an edition (P1):** Organiser, "Everyone registered in <year>". First name,
    last name and date of birth only.
22. **Heaviest carried person (A5):** Organiser, "Heaviest carried person" (MAX weight in the edition).
23. **Pending protests (S2):** Jury, "Pending protests". Complete rows of all protests still pending.
24. **Average finishing times (A2):** Staff Desk › Committee reports (`/desk/reports`), "Average times".
    AVG net time of finishers per series and edition.
25. **Fees per edition (A3):** Committee reports, "Fees". SUM of registration fees paid per edition.
26. **Registrations per country (A4):** Committee reports, "By country", with an edition picker
    (COUNT per country represented).
27. **Medal table (AR1):** Committee reports, "Medal table". Gold, silver and bronze in the main series
    across all editions, by country.
28. **Backpack report (AR2):** Committee reports, "Backpacks". Carried people under 49 kg, their
    series and the backpack weight required.
29. **Multi-series competitors (AR3):** Committee reports, "Multi-series", with an edition picker.
    People who raced in more than one series in the same edition, with role and result in each.
30. **Edition income (AR4):** Committee reports, "Income". Registration fees net of refunds, protest
    fees and paid booth fees side by side.
31. **Protest outcomes (AR5):** Committee reports, "Protests". Protests filed, upheld and pending per
    race, and the officials who voted.
32. **Countries faster than average (AR6):** Committee reports, "Faster than average", with an
    edition picker. Countries whose average main-series time beats the edition average.

Other pages modelled on the site: the front page (2027 dates, latest winners, rules in brief),
Programme 2027 (`/programme`) and Official Grand Prix (`/grand-prix`).
