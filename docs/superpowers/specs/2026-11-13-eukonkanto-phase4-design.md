# Phase 4 Design — Wife-Carrying World Championship (eukonkanto.fi)

**Date:** 2026-11-13
**Team:** 69 (Phase 1 author) · Phase 2 by Team 65 · Phase 3 by Team 56
**Status:** Approved in conversation; awaiting written-spec review

## 1. Goal and success criteria

Turn the Phase 3 relational schema (Team 56) into a populated MariaDB database and a locally running web application modelled on https://eukonkanto.fi/en/, implementing **all 32 functional requirements** from the Team 69 Phase 1 document (15 retrievals, 6 analysis reports, 4 insertions, 4 updates, 3 deletions).

Success means:

1. `mysql -u <user> -p < src/schema.sql` then `mysql -u <user> -p < src/populate.sql` on a fresh server reproduces the database exactly, with all triggers active during population.
2. Every one of the 32 FRs is reachable through a natural UI interaction (search bar, filter, detail page, form, delete button) and runs a raw, parameterised SQL query from the Python backend.
3. Constraint and trigger violations appear in the UI as clear messages.
4. A1 (world records) and S3 (2026 Sprint final) reproduce what eukonkanto.fi shows.
5. The README covers everything the brief asks for (paradigm/versions, stack, Design Changes, setup, numbered feature list in demo order). `DEMO.md` gives a video script.

Out of scope: login/authentication, deployment, the video recording and zip packaging (the student does these), and the features Phase 1 lists as out of scope (web shop, tickets, accommodation, news, accreditation).

## 2. Stack

| Layer | Choice |
|---|---|
| DBMS | MariaDB (MySQL-compatible), installed via `pacman -S mariadb`; SQL paradigm |
| Driver | PyMySQL (`%s` parameters, `DictCursor`, `autocommit=False`) |
| Backend | Python 3 + Flask, JSON API under `/api/*`; also serves the built frontend |
| Frontend | React + Vite + react-router; dev server proxies `/api` to `:5000` |
| Tests | pytest against a fresh `eukonkanto_test` database |

Production-style run: `npm run build` produces `src/frontend/dist`, which Flask serves. Everything is at `http://localhost:5000`.

## 3. Rule-enforcement approach (Approach A)

- Rules that involve **one row** are declarative: PK, FK with explicit `ON DELETE`/`ON UPDATE`, `NOT NULL`, `UNIQUE`, `CHECK`, `ENUM`.
- Rules that need **another table** are `BEFORE INSERT/UPDATE` triggers that `SIGNAL SQLSTATE '45000'` with a readable message.
- **Derived attributes are never stored.** Views compute them (window functions for rank and gap).
- **Multi-statement writes** (I1, U1, U3, D3) are explicit transactions in Python, written as raw SQL, with rollback on any error.

## 4. Schema

### 4.1 Relations (Phase 3 baseline, 30 relations)

COUNTRY, PERSON, PERSON_PHONE, PERSON_CITIZENSHIP, COMPETITOR, OFFICIAL, EDITION, VENUE, VENUE_FACILITY, SERIES, RACE, ROLE, ENTRY, PARTICIPATES_AS, REPRESENTS, REGISTRATION, RESULT, PENALTY, PROTEST, DECIDES, OFFICIATES_IN, GRAND_PRIX_EVENT, PRIZE, AWARDED, OFFERS, SPONSOR, SPONSORS, VENDOR, VENDOR_PRODUCT_CATEGORY, EXHIBITS_AT.

Table and column names follow Phase 3, as do the composite keys: RACE (Edition_Year, Race_No); RESULT (Registration_ID, Stage); PENALTY (Registration_ID, Stage, Penalty_No); PARTICIPATES_AS (Entry_ID, Role_Code) plus UNIQUE (Entry_ID, Person_ID); REGISTRATION UNIQUE (Entry_ID, Edition_Year, Race_No).

### 4.2 Design Changes (each becomes a README line)

| # | Change | Reason |
|---|---|---|
| 1 | Surrogate IDs (Person, Entry, Registration, Protest, Prize, Venue, Sponsor, Vendor, GP_Event) become `INT AUTO_INCREMENT`; natural codes (ISO_Code `CHAR(3)`, Series_Code, Role_Code) stay `VARCHAR` | The application creates rows and needs DB-generated keys |
| 2 | `PERSON.Date_of_Birth` and `Gender` become nullable; `Email` is nullable + `UNIQUE` | Historic champions (1992 onwards) have no published DOB, gender or e-mail (Phase 2 also flagged Email) |
| 3 | `REGISTRATION.Bib_No` becomes nullable, with `UNIQUE (Edition_Year, Bib_No)` | Enforces "bib unique within edition" declaratively; cancelling sets it to NULL, which releases the bib (Phase 1 U2) |
| 4 | Time and money go from FLOAT to `DECIMAL` (`Raw_Time_s DECIMAL(7,2)`, `*_EUR DECIMAL(8,2)`, weights `DECIMAL(5,1)`) | Sprint times have hundredths; money must be exact |
| 5 | `EDITION.Registration_Deadline` goes from DATE to `DATETIME` | The real deadline is Wednesday 22:00 |
| 6 | Add `SERIES.Has_Heats BOOLEAN NOT NULL` | Phase 1 rule "heat stages only in series with heats" had no attribute to check against |
| 7 | Add `RACE.Last_Finish_At DATETIME NULL` | Phase 1 rule "protest within 15 min of the last finisher" needs a stored finish time |
| 8 | Add `UNIQUE (Edition_Year, Series_Code)` on RACE | Phase 1 rule "at most one race per series per edition" |
| 9 | Restricted VARCHARs become ENUM/CHECK: Entry_Type (Pair, Team), Payment_Status (Pending, Paid, Refunded), RESULT.Status (Finished, DNS, DNF, DQ), Stage (Heat 1–3, Final, Single), Adjustment_Type (Penalty, Bonus, Warning), Outcome (Pending, Upheld, Rejected), Vote (Uphold, Reject), Prize_Type (Placement, Special), Prize_Scope (Series, Weekend), Booth_Size (4x4, 4x8, Custom), Championship_Level (Finnish, World), Gender (Female, Male, Other) | Phase 1 and Phase 2 defined these domains; Phase 3 left them as free text |

Kept as in Phase 3 (also noted in the README):

- No stored REGISTRATION status. Status is derived from `Cancelled_At IS NULL`.
- No QUALIFIES relationship (added by Phase 2, but no FR uses it).
- No protest fee column. 150 EUR is a business rule, used as a constant in AR4.

### 4.3 Referential actions

- RESTRICT (the default) applies to anything referencing COUNTRY, SERIES, VENUE, PRIZE, EDITION, RACE, ENTRY (from REGISTRATION), PERSON and OFFICIAL.
- CASCADE applies only to:
  - REGISTRATION → RESULT → PENALTY
  - ENTRY → PARTICIPATES_AS and REPRESENTS
  - PERSON → PERSON_PHONE and PERSON_CITIZENSHIP
  - VENUE → VENUE_FACILITY
  - VENDOR → VENDOR_PRODUCT_CATEGORY and EXHIBITS_AT
  - SPONSOR → SPONSORS
  - PROTEST → DECIDES
  - SERIES/PRIZE → OFFERS
- SET NULL applies to `OFFICIAL.Supervisor_ID` and `RESULT.Recorded_By_Official_ID`.
- `ON UPDATE CASCADE` applies to all FKs that reference natural keys.

### 4.4 CHECK constraints (single row)

- COUNTRY: `ISO_Code REGEXP '^[A-Z]{3}$'`
- PERSON: Email format (`LIKE '%_@_%._%'`)
- SERIES: `Min_Carrier_Age >= 18`, `Min_Carried_Age >= 17`, `Min_Carried_Weight_kg >= 49`, `Carrier_Count IN (1,3)`, and lengths/obstacles `>= 0`
- EDITION: `End_Date >= Start_Date`, `Registration_Opens < Registration_Deadline`, `Registration_Deadline < Start_Date`
- RACE: `Entry_Fee_EUR >= 0`
- RESULT: `(Status='Finished') = (Raw_Time_s IS NOT NULL)`, `Raw_Time_s > 0`
- PENALTY: Seconds > 0 for Penalty and Bonus; Seconds = 0 for Warning
- PARTICIPATES_AS: `Measured_Weight_kg IS NULL OR (Role_Code='CARRIED' AND Measured_Weight_kg > 0)`
- PROTEST: `Decided_At IS NULL OR Decided_At >= Filed_At`, and `(Outcome='Pending') = (Decided_At IS NULL)`
- PRIZE: `(Prize_Type='Placement') = (Placement_Rank BETWEEN 1 AND 3)`; special prizes have NULL rank
- OFFICIAL: `Supervisor_ID <> Person_ID`
- EXHIBITS_AT: `Booth_Fee_EUR >= 0`
- REGISTRATION: `Bib_No > 0`, `Fee_Paid_EUR >= 0`, and `(Cancelled_At IS NULL) OR (Bib_No IS NULL)`

### 4.5 Triggers

| Trigger | Table / event | Rule (Phase 1 source) |
|---|---|---|
| `trg_reg_bi` | REGISTRATION BEFORE INSERT | `Registered_At` within [Registration_Opens, Registration_Deadline]; entry's role set matches the series (Carrier_Count 1 means CARRIER_1 + CARRIED, 3 means CARRIER_1–3 + CARRIED); each participant's age on the race date meets Min_Carrier_Age / Min_Carried_Age (skipped when DOB is NULL for historic rows); Fee_Paid_EUR equals RACE.Entry_Fee_EUR when Payment_Status = Paid; Edition_Year matches the race |
| `trg_reg_bu` | REGISTRATION BEFORE UPDATE | Setting Cancelled_At is refused if any RESULT exists; on cancel, Bib_No is forced to NULL |
| `trg_pa_bi` / `trg_pa_bu` | PARTICIPATES_AS BEFORE INSERT/UPDATE | Refused if the entry has any RESULT (U4); age re-checked against every live registration of the entry; Team roles CARRIER_2/3 only for Entry_Type = Team |
| `trg_res_bi` / `trg_res_bu` | RESULT BEFORE INSERT/UPDATE | Registration not cancelled; Heat stages and Final only if `Has_Heats`, Single only if not; the recorder must be an OFFICIAL |
| `trg_prot_bi` | PROTEST BEFORE INSERT | Entry has a live registration in the race; `Filed_At` within [Last_Finish_At, Last_Finish_At + 15 min] |
| `trg_aw_bi` | AWARDED BEFORE INSERT | The series of the registration's race OFFERS the prize; a placement prize's rank equals the registration's rank in the deciding stage (Final, or Single), taken from `v_result` |
| `trg_ex_bi` | EXHIBITS_AT BEFORE INSERT | Booth_Fee is 70 (4x4) or 140 (4x8) unless the booth is Custom or the vendor sells food (contract price) |

### 4.6 Views (derived attributes)

- `v_entry_name`: Entry_ID, Display_Name ("Carrier1[, Carrier2, Carrier3] / Carried"), Team_Name, a country list built with GROUP_CONCAT over REPRESENTS.
- `v_result`: one row per RESULT with Edition_Year, Race_No, Series_Code, Bib_No, Net_Time_s = Raw + SUM(Penalty) − SUM(Bonus), Rank_In_Stage = `RANK() OVER (PARTITION BY race, stage ORDER BY Net_Time_s)` for Finished rows only, and Gap_To_Leader_s = Net − `MIN(Net) OVER (...)`.
- `v_registration`: Status (Registered/Cancelled), Refund_EUR (Fee − 10 if cancelled at least 30 days before the race start, else 0), and the derived Required_Backpack_kg for the carried person.

## 5. Data (`populate.sql`)

Insertion order goes from parent tables to children. Every block of invented data carries a `-- GENERATED:` comment, and the README says which data was invented.

**From eukonkanto.fi (real):**

- **Editions** 1992–2027, except 2020 and 2021. 1992–95 are Finnish level; World level from 1996. 2027: 2–3 July, registration 2026-11-01 to 2027-06-30 22:00.
- **Series:** Main (253.5 m, 1 water + 2 dry obstacles, 55 €), Women's, +40 (carrier ≥ 40), Team (Carrier_Count 3, 160 €), Sprint (~120 m, 1 water obstacle, Has_Heats, 55 €). Race start times come from the programme.
- **2026 complete results:**
  - Sprint: heats A1–A3 and the final
  - Main: 45 entries, including 2 DNS
  - Women's: 6 entries, including 1 DNS
  - +40: 13 entries
  - Team: 7 entries, with real team names and organisations, plus Team 105's +15 s penalty
  - Real bibs, multi-country REPRESENTS rows, and the same PERSON row reused across series and entries
- **Champions 1992–2026** (Main, Sprint, Team) stored as rank-1 results.
- **World records** stored with their real times and years: Main 56.9 (2006), Team 1:24.6 (2008), Sprint 31.34 (2012), +40 1:13.49 (2026), Women's 1:39.51 (2025).
- **2027 registrations:** the real list, excluding "Name not published" and "To be determined" placeholders.
- **Venues and facilities, sponsors, prizes, Grand Prix events** (2024 China, Australia, Belgium, USA, plus the UK announcement), and booth prices.

**Generated (believable, flagged):**

- Champion times where none is published (Wikipedia is checked first). Estimates are always slower than the series record.
- DOBs that satisfy the series age rules, and carried weights (some below 49 kg, so AR2 returns rows).
- About 8 officials with a supervisor hierarchy, their race duties, and recorders on results.
- 4–5 protests in 2026 (upheld, rejected, pending) with votes.
- About 8 vendors with categories and 2026/2027 bookings, some unpaid.
- E-mails for 2027 registrants.
- Registration windows and `Registered_At` timestamps for historic editions, so that population passes the deadline trigger.

**Coverage:** the data includes rows that match and rows that don't (a series with no race in a year, an entry with no registration, a vendor with no booking), plus rows that can safely be updated or deleted.

## 6. Backend

```
src/
  app.py            Flask app: routes only; serves frontend/dist
  config.py         get_db_config() from env vars DB_HOST/DB_USER/DB_PASS/DB_NAME
  db.py             get_connection(); query(sql, params); execute(...);
                    transaction() context manager; error mapping
  repo/             one module per area, raw parameterised SQL constants
    results.py registrations.py protests.py people.py vendors.py prizes.py reports.py
  tests/
```

- Each repo function exposes its SQL string. Each API response is `{"rows": [...], "sql": "<the SQL text>"}` (writes return `{"ok": true, ..., "sql": ...}`), which feeds the frontend's "Show SQL" panel.
- **Input handling:** values are coerced to int/Decimal/date/enum whitelists before any query, and invalid input returns 400. User input is never placed into SQL text.
- **Error mapping** to a JSON `{"error": message}` with HTTP 409/400/404:
  - 1062 duplicate
  - 1451 / 1452 FK
  - 3819 / 4025 CHECK
  - 1644 trigger SIGNAL (the trigger's message is passed through)
  - 1048 NOT NULL

## 7. Frontend

React SPA. The look follows eukonkanto.fi: navy `#223c76`, cyan `#82ddf0`, orange `#f76a0c`, a white content area, the site's top navigation groups and a sponsor footer.

| Route | Page |
|---|---|
| `/` | Home: hero (2027 dates, register CTA), series cards, latest champions, sponsors |
| `/results?year=` | Results by edition, with a tab per series; the Sprint shows the heats and final; DNS and warnings rows |
| `/results/champions-and-records` | World records and the champions list |
| `/competitors?year=&series=&country=` | Registered competitors by series, plus a Teams tab |
| `/register` | Registration form (pair/team, pick or create persons, weight) |
| `/my-registration` | Look up by registration no.: view, cancel (shows refund), replace a member |
| `/search?q=` | Persons and teams results; links to `/people/:id` (competition history) |
| `/grand-prix` | GP events grouped by continent |
| `/market` | Market info, vendor search, booking table for an edition |
| `/desk/organiser` | S1, P1, A5, D1, D2, I4, P3/D3 |
| `/desk/jury` | S2, I2, U1, I3, U3 |
| `/desk/reports` | A2, A3, A4, AR1–AR6 |

Each feature has a collapsible **Show SQL** panel (read-only). Errors appear as inline alerts.

## 8. Functional-requirement map

| FR | Endpoint | UI trigger |
|---|---|---|
| S1 | `GET /api/registrations?year&series` | Desk › Organiser: edition + series selector |
| S2 | `GET /api/protests?status=Pending` | Desk › Jury: pending list |
| S3 | `GET /api/results?year&series=SPR&stage=Final` | Results › Sprint tab › Final |
| P1 | `GET /api/editions/:y/persons` | Desk › Organiser: persons in edition |
| P2 | `GET /api/teams` | Competitors › Teams tab |
| P3 | `GET /api/editions/:y/booths` | Market › bookings table |
| A1 | `GET /api/records` | Champions & Records |
| A2 | `GET /api/reports/avg-times` | Reports tab |
| A3 | `GET /api/reports/fees` | Reports tab |
| A4 | `GET /api/reports/registrations-by-country?year` | Reports tab |
| A5 | `GET /api/editions/:y/heaviest-carried` | Desk › Organiser card |
| Q1 | `GET /api/search/persons?q` | Header search |
| Q2 | `GET /api/search/teams?q` | Header search |
| Q3 | `GET /api/entries?country&series&year` | Competitors filters |
| Q4 | `GET /api/vendors?q&category` | Market search |
| AR1–AR6 | `GET /api/reports/{medals,backpacks,multi-series,income,protests,above-average}` | Reports tabs |
| I1 | `POST /api/registrations` | Register form |
| I2 | `POST /api/results` | Desk › Jury › record result |
| I3 | `POST /api/protests` | Desk › Jury › file protest |
| I4 | `POST /api/awards` | Desk › Organiser › award prize |
| U1 | `PATCH /api/results/:reg/:stage`, `POST /api/penalties` | Desk › Jury › edit time / add penalty |
| U2 | `POST /api/registrations/:id/cancel` | My registration › Cancel |
| U3 | `POST /api/protests/:id/decide` | Desk › Jury › decide |
| U4 | `PATCH /api/entries/:id/roles/:role` | My registration › Replace member |
| D1 | `DELETE /api/registrations/:id` | Desk › Organiser › delete |
| D2 | `DELETE /api/entries/:id` | Desk › Organiser › unregistered entries |
| D3 | `DELETE /api/booths/:vendor/:year` | Market › bookings › remove unpaid |

Transaction details:

- **I1:** insert any new PERSON (+ COMPETITOR, CITIZENSHIP) → ENTRY → PARTICIPATES_AS → REPRESENTS → REGISTRATION. The triggers validate the whole set; any error rolls back everything.
- **U1:** update RESULT or insert PENALTY → set Recorded_By to the editing official → delete stale placement AWARDED rows for that race's deciding stage → re-insert placement awards by the new rank. Ranks themselves come from `v_result`, so they update automatically.
- **U3:** set Outcome/Decided_At → insert DECIDES votes → if upheld, delete the chosen PENALTY or set the chosen RESULT to DQ → run U1's prize re-assignment.
- **D1:** refused unless the registration is Registered, has no RESULT and has no AWARDED row; checked in the transaction with `SELECT ... FOR UPDATE`.
- **D2:** refused if any REGISTRATION exists; this check is the FK RESTRICT itself.
- **D3:** only for unpaid bookings whose edition has not started; deletes the VENDOR too when it has no other bookings.

## 9. Testing

- A pytest fixture loads `schema.sql` and `populate.sql` into `eukonkanto_test` (via the `mysql` client) once per session. Write tests run inside a transaction that is rolled back, or reload the database.
- **Per FR:** assert the shape plus known real values (A1 equals the site's records; S3 order is Tuovinen, Wasenius, Nash, Lee; A3 and A4 totals).
- **Per trigger and CHECK:** assert rejection, covering an under-age carrier, a +40 carrier under 40, a late registration, a duplicate bib, a pair entering the Team series, a heat result in a non-Sprint series, a result for a cancelled registration, a protest outside 15 minutes, an award for a prize not offered, a wrong placement award, cancelling after results, and deleting a registration that has run.
- **Frontend:** `npm run build` succeeds, plus a manual click-through of every FR.

## 10. Deliverables in this repository

- `src/` (schema.sql, populate.sql, app.py, requirements.txt, helpers, frontend/, tests/)
- `README.md` (all brief sections; feature list in demo order; Design Changes as in §4.2, team numbers 69/65/56; data provenance)
- `DEMO.md` (video script with before/after SQL for each create, update and delete)

`phase3.pdf`, the mp4 and the zip are assembled by the student.
