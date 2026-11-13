"""Render src/populate.sql from the data modules in tools/data/.

Usage (from the repository root):  python -I src/tools/build_populate.py > src/populate.sql

populate.sql is the deliverable and is committed; this script only keeps it reproducible.
Explicit IDs are written so the script is deterministic and readable. Rows not taken from
eukonkanto.fi (or Wikipedia for Main-series times) end with a `-- GENERATED:` comment.
"""
import datetime as dt
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import history, reference as ref, reg_2027, results_2026 as r26  # noqa: E402

GEN = "GENERATED"


# ---------------------------------------------------------------- helpers
def h(text: str) -> int:
    return int(hashlib.md5(text.encode("utf8")).hexdigest(), 16)


def secs(t: str):
    """'1:04.4' -> 64.4, '33.77' -> 33.77, 'DNS' -> None."""
    if t == "DNS":
        return None
    if ":" in t:
        m, s = t.split(":")
        return round(int(m) * 60 + float(s), 2)
    return float(t)


def split_name(full: str):
    parts = full.split()
    return (full, "") if len(parts) == 1 else (" ".join(parts[:-1]), parts[-1])


def sql_val(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"


class Out:
    def __init__(self):
        self.lines = []

    def comment(self, text):
        self.lines.append(f"\n-- {text}")

    def insert(self, table, cols, rows):
        """rows: list of (values_tuple, comment_or_None)."""
        if not rows:
            return
        for start in range(0, len(rows), 200):
            chunk = rows[start:start + 200]
            self.lines.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES")
            for i, (vals, note) in enumerate(chunk):
                end = ";" if i == len(chunk) - 1 else ","
                tail = f"  -- {note}" if note else ""
                self.lines.append(f"  ({', '.join(sql_val(v) for v in vals)}){end}{tail}")

    def text(self):
        return "\n".join(self.lines) + "\n"


# ---------------------------------------------------------------- model building
class World:
    def __init__(self):
        self.persons = {}        # name -> dict
        self.entries = {}        # key -> dict
        self.regs = []           # dicts
        self.results = []        # (reg_id, stage, raw, status, recorder, note)
        self.penalties = []
        self.awards = []
        self.editions = {}
        self.races = {}          # (year, series) -> dict

    # people ----------------------------------------------------------------
    def person(self, name, iso=None):
        p = self.persons.get(name)
        if p is None:
            first, last = split_name(name)
            p = self.persons[name] = {"id": len(self.persons) + 1, "first": first, "last": last,
                                      "cit": [], "recent": False, "m40_carrier": False,
                                      "carrier": False, "email": None, "generated": False,
                                      "latest_birth_year": 9999}
        if iso and not p["cit"]:
            p["cit"] = list(reg_2027.CITIZENSHIP_OVERRIDES.get(name, [iso]))
        return p

    # entries ---------------------------------------------------------------
    def entry(self, members, isos, team_name=None, org=None, generated=False, era=None):
        """members: [(role, name)]; isos: list of ISO codes."""
        pids = []
        for role, name in members:
            if role == "CARRIED":
                iso = isos[-1]
            elif len(isos) > 1 and team_name:
                iso = isos[0]
            else:
                iso = isos[0]
            pids.append((role, self.person(name, iso)["id"]))
        key = ("Team" if team_name else "Pair", team_name, tuple(sorted(pids)), era)
        e = self.entries.get(key)
        if e is None:
            e = self.entries[key] = {"id": len(self.entries) + 1, "type": key[0], "team": team_name,
                                     "org": org, "members": members, "pids": pids, "isos": isos,
                                     "recent": False, "generated": generated}
        return e

    def pair(self, carrier, carried, isos, generated=False, era=None):
        return self.entry([("CARRIER_1", carrier), ("CARRIED", carried)], isos, generated=generated, era=era)

    def team(self, team_name, org, carriers, carried, isos):
        members = [("CARRIER_1", carriers[0]), ("CARRIED", carried),
                   ("CARRIER_2", carriers[1]), ("CARRIER_3", carriers[2])]
        return self.entry(members, isos, team_name=team_name, org=org)

    # registrations -----------------------------------------------------------
    def register(self, e, year, series, bib, at, note=None, cancelled_at=None):
        race = self.races[(year, series)]
        reg = {"id": len(self.regs) + 1, "entry": e, "year": year, "race_no": race["no"],
               "series": series, "bib": None if cancelled_at else bib, "at": at,
               "cancelled": cancelled_at, "fee": race["fee"],
               "pay": "Refunded" if cancelled_at else "Paid", "note": note}
        self.regs.append(reg)
        min_age = {"M40": 40}.get(series, 18)
        for role, name in e["members"]:
            need = 17 if role == "CARRIED" else min_age
            p = self.persons[name]
            p["latest_birth_year"] = min(p["latest_birth_year"], year - need - 1)
        if year >= 2026:
            e["recent"] = True
            for role, name in e["members"]:
                p = self.persons[name]
                p["recent"] = True
                if role != "CARRIED":
                    p["carrier"] = True
                    if series == "M40":
                        p["m40_carrier"] = True
        return reg


def edition_dates(year):
    if year in history.KNOWN_DATES:
        return history.KNOWN_DATES[year], False
    d = dt.date(year, 7, 1)
    start = d + dt.timedelta(days=(4 - d.weekday()) % 7)          # first Friday of July
    end = start + dt.timedelta(days=1)
    deadline = dt.datetime.combine(start - dt.timedelta(days=2), dt.time(22, 0))   # Wednesday
    return (start.isoformat(), end.isoformat(), f"{year - 1}-11-01",
            deadline.strftime("%Y-%m-%d %H:%M:%S")), True


def build():
    w = World()

    # editions and races -----------------------------------------------------
    for y in history.YEARS:
        (start, end, opens, deadline), gen = edition_dates(y)
        level = "Finnish" if y in history.FINNISH_YEARS else "World"
        w.editions[y] = {"start": start, "end": end, "opens": opens, "deadline": deadline,
                         "level": level, "generated": gen}
        fees = ref.FEES_NOW if y >= 2026 else ref.FEES_OLD
        for code, first in history.SERIES_FROM.items():
            if y < first:
                continue
            no, day, hhmm = ref.RACE_SLOTS[code]
            date = start if day == "start" else end
            sched = dt.datetime.fromisoformat(f"{date} {hhmm}:00")
            last = None if y >= 2027 else sched + dt.timedelta(minutes=ref.LAST_FINISH_MIN[code])
            w.races[(y, code)] = {"no": no, "sched": sched, "fee": fees[code], "last": last}

    def reg_time(year, seed):
        """GENERATED registration timestamp inside the edition's window."""
        ed = w.editions[year]
        opens = dt.datetime.fromisoformat(ed["opens"] + " 10:00:00")
        if year == 2027:
            return opens + dt.timedelta(days=seed % 12, hours=seed % 9)
        if year == 2026:
            return opens + dt.timedelta(days=seed % 200, hours=seed % 9)
        return opens + dt.timedelta(days=30)

    timekeepers = []   # filled after officials are created (ids)

    # 2026: full results -------------------------------------------------------
    def rows(block):
        return [line.split("|") for line in block.strip().splitlines()]

    bib_reg = {}
    sprint_regs = {}
    for bib, carrier, carried, isos in rows(r26.SPRINT_ENTRIES):
        e = w.pair(carrier, carried, isos.split("/"))
        reg = w.register(e, 2026, "SPR", int(bib), reg_time(2026, h(carrier + "SPR")))
        sprint_regs[int(bib)] = reg
    for stage, results in r26.SPRINT_STAGES.items():
        for bib, t in results:
            w.results.append([sprint_regs[bib]["id"], stage, secs(t), "Finished", None])

    for series, block in (("WOMEN", r26.WOMEN), ("M40", r26.M40), ("MAIN", r26.MAIN)):
        for bib, carrier, carried, isos, t in rows(block):
            e = w.pair(carrier, carried, isos.split("/"))
            reg = w.register(e, 2026, series, int(bib), reg_time(2026, h(carrier + series)))
            bib_reg[(series, int(bib))] = reg
            raw = secs(t)
            w.results.append([reg["id"], "Single", raw, "Finished" if raw else "DNS", None])

    for bib, c1, carried, c2, c3, name, isos, t in rows(r26.TEAM):
        org = name if name in r26.TEAM_ORGANISATIONS else None
        e = w.team(name, org, [c1, c2, c3], carried, isos.split("/"))
        reg = w.register(e, 2026, "TEAM", int(bib), reg_time(2026, h(name)))
        bib_reg[("TEAM", int(bib))] = reg
        w.results.append([reg["id"], "Single", secs(t), "Finished", None])
    for bib, kind, seconds, reason in r26.TEAM_PENALTIES:
        w.penalties.append((bib_reg[("TEAM", bib)]["id"], "Single", 1, kind, seconds, reason))
    for bib, reg in sprint_regs.items():
        bib_reg[("SPR", bib)] = reg

    # GENERATED cancelled 2026 registration and unregistered entry
    series, carrier, carried, iso, at, cancelled = reg_2027.CANCELLED_2026
    e = w.pair(carrier, carried, [iso], generated=True)
    w.persons[carrier]["generated"] = w.persons[carried]["generated"] = True
    w.register(e, 2026, series, None, dt.datetime.fromisoformat(at),
               note=f"{GEN}: cancelled >30 days before the race",
               cancelled_at=dt.datetime.fromisoformat(cancelled))
    carrier, carried, iso = reg_2027.UNREGISTERED_ENTRY
    e = w.pair(carrier, carried, [iso], generated=True)
    e["recent"] = True
    for n in (carrier, carried):
        w.persons[n]["generated"] = w.persons[n]["recent"] = True
    w.persons[carrier]["carrier"] = True

    # historic champions ------------------------------------------------------
    hist_bib = {"MAIN": 1, "WOMEN": 2, "SPR": 70, "TEAM": 100}
    for y, (carrier, carried, iso, t, gen) in history.MAIN_CHAMPIONS.items():
        e = w.pair(carrier, carried, iso.split("/"))
        reg = w.register(e, y, "MAIN", hist_bib["MAIN"], reg_time(y, 0), note=f"{GEN}: registration details")
        w.results.append([reg["id"], "Single", secs(t), "Finished", None, f"{GEN}: time" if gen else None])
    for y, champs in history.SPRINT_CHAMPIONS.items():
        for i, (carrier, carried, iso, t, gen) in enumerate(champs):
            e = w.pair(carrier, carried, iso.split("/"))
            reg = w.register(e, y, "SPR", hist_bib["SPR"] + i, reg_time(y, 0), note=f"{GEN}: registration details")
            w.results.append([reg["id"], "Final", secs(t), "Finished", None, f"{GEN}: time" if gen else None])
    for y, (name, org, carriers, carried, iso, t, gen) in history.TEAM_CHAMPIONS.items():
        e = w.team(name, org, carriers, carried, iso.split("/"))
        reg = w.register(e, y, "TEAM", hist_bib["TEAM"], reg_time(y, 0), note=f"{GEN}: registration details")
        w.results.append([reg["id"], "Single", secs(t), "Finished", None, f"{GEN}: time" if gen else None])
    for y, (carrier, carried, iso, t, gen) in history.WOMEN_CHAMPIONS.items():
        e = w.pair(carrier, carried, iso.split("/"))
        reg = w.register(e, y, "WOMEN", hist_bib["WOMEN"], reg_time(y, 0), note=f"{GEN}: registration details")
        w.results.append([reg["id"], "Single", secs(t), "Finished", None, f"{GEN}: time" if gen else None])

    # 2027 registrations ---------------------------------------------------------
    for series, block in reg_2027.REGISTRATIONS_2027.items():
        bib = reg_2027.BIB_START_2027[series]
        for carrier, carried, iso in rows(block):
            e = w.pair(carrier, carried, iso.split("/"))
            if any(r["entry"] is e and r["year"] < 2027 for r in w.regs):
                # an entry that has raced is frozen (trigger); a returning pair gets a new entry
                e = w.pair(carrier, carried, iso.split("/"), era=2027)
            w.register(e, 2027, series, bib, reg_time(2027, h(carrier + series)),
                       note=f"{GEN}: timestamp and bib")
            for n in (carrier, carried):
                p = w.persons[n]
                if p["email"] is None:
                    p["email"] = (n.lower().replace(" ", ".").replace("ö", "o").replace("ä", "a")
                                  + "@mail.example")
            bib += 1
    return w, bib_reg


# ---------------------------------------------------------------- derived generated attributes
def dob_for(p, name):
    if not (p["recent"] or p["generated"]):
        return None
    k = h(name)
    if p["m40_carrier"]:
        year = 1962 + k % 20
    elif p["carrier"]:
        year = 1980 + k % 21
    else:
        year = 1984 + k % 20
    if year > p["latest_birth_year"]:          # old enough for the person's earliest race
        year = p["latest_birth_year"] - k % 6
    return f"{year}-{1 + (k // 7) % 12:02d}-{1 + (k // 13) % 28:02d}"


def weight_for(name):
    if name in reg_2027.LIGHT_CARRIED:
        return reg_2027.LIGHT_CARRIED[name]
    return round(50.0 + (h(name + "kg") % 230) / 10, 1)


def ranks(results, reg_ids, stage, penalties):
    """Net-time ranking used only to pick 2026 award winners (the DB computes ranks itself)."""
    pen = {}
    for reg, st, _no, kind, seconds, _r in penalties:
        if st == stage:
            pen[reg] = pen.get(reg, 0) + (seconds if kind == "Penalty" else -seconds if kind == "Bonus" else 0)
    rows = [(r[2] + pen.get(r[0], 0), r[0]) for r in results
            if r[0] in reg_ids and r[1] == stage and r[3] == "Finished"]
    return [reg for _t, reg in sorted(rows)]


# ---------------------------------------------------------------- SQL output
def main():
    w, bib_reg = build()
    o = Out()
    o.lines.append("-- Wife-Carrying World Championship database: population script (Phase 4, Team 69)")
    o.lines.append("-- Generated by src/tools/build_populate.py. Run after schema.sql:")
    o.lines.append("--   mysql -u <user> -p < populate.sql")
    o.lines.append("-- Real data: eukonkanto.fi (results 2026, champions & records, 2027 registrations, rules,")
    o.lines.append("-- programme, partners, market prices) and Wikipedia (Main-series winning times).")
    o.lines.append("-- Rows ending in '-- GENERATED:' are invented but consistent with the site's rules.")
    o.lines.append("USE eukonkanto_db;\nSET NAMES utf8mb4;")

    o.comment("Countries")
    o.insert("COUNTRY", ["ISO_Code", "Country_Name", "Continent"], [(c, None) for c in ref.COUNTRIES])
    o.comment("Roles in an entry")
    o.insert("ROLE", ["Role_Code", "Role_Name", "Leg_Order"], [(r, None) for r in ref.ROLES])
    o.comment("Series (rules page)")
    o.insert("SERIES", ["Series_Code", "Series_Name", "Track_Length_m", "Water_Obstacles", "Dry_Obstacles",
                        "Min_Carrier_Age", "Min_Carried_Age", "Min_Carried_Weight_kg", "Carrier_Count",
                        "Has_Heats"], [(s, None) for s in ref.SERIES])
    o.comment("Venues and facilities (programme, guidance for competitors)")
    o.insert("VENUE", ["Venue_ID", "Venue_Name", "Street", "Postal_Code", "City"],
             [(v[:5], None) for v in ref.VENUES])
    o.insert("VENUE_FACILITY", ["Venue_ID", "Facility"],
             [((v[0], f), None) for v in ref.VENUES for f in v[5]])

    o.comment("Editions 1992-2027 (2020-2021 cancelled)")
    o.insert("EDITION", ["Edition_Year", "Championship_Level", "Start_Date", "End_Date", "Registration_Opens",
                         "Registration_Deadline"],
             [((y, e["level"], e["start"], e["end"], e["opens"], e["deadline"]),
               f"{GEN}: dates" if e["generated"] else None) for y, e in w.editions.items()])
    o.comment("Races (one per series per edition), all at the Wife Carrying Arena")
    o.insert("RACE", ["Edition_Year", "Race_No", "Scheduled_Start", "Entry_Fee_EUR", "Series_Code", "Venue_ID",
                      "Last_Finish_At"],
             [((y, r["no"], str(r["sched"]), r["fee"], code, 1, str(r["last"]) if r["last"] else None),
               f"{GEN}: last-finish time" if r["last"] else None)
              for (y, code), r in sorted(w.races.items(), key=lambda kv: (kv[0][0], kv[1]["no"]))])

    o.comment("Sponsors (front-page partners) and the editions they support")
    o.insert("SPONSOR", ["Sponsor_ID", "Sponsor_Name", "Website_URL"], [(s, None) for s in ref.SPONSORS])
    o.insert("SPONSORS", ["Sponsor_ID", "Edition_Year"],
             [((s[0], y), None) for s in ref.SPONSORS for y in ref.SPONSOR_YEARS])
    o.comment("Official Grand Prix events")
    o.insert("GRAND_PRIX_EVENT", ["GP_Event_ID", "Event_Name", "Event_Month_Year", "City", "Region", "Organiser",
                                  "Host_ISO_Code"],
             [(g[:7], f"{GEN}: city/region/organiser" if g[7] else None) for g in ref.GRAND_PRIX])
    o.comment("Prizes (rules page) and which series offer them")
    o.insert("PRIZE", ["Prize_ID", "Prize_Name", "Prize_Type", "Placement_Rank", "Includes_Drink", "Description",
                       "Prize_Scope"], [(p[:7], None) for p in ref.PRIZES])
    o.insert("OFFERS", ["Series_Code", "Prize_ID"], [((s, p[0]), None) for p in ref.PRIZES for s in p[7]])

    # people
    officials = []
    for first, last, dob, gender, title, since, supervised, duty in ref.OFFICIALS:
        officials.append((len(w.persons) + 1 + len(officials), first, last, dob, gender, title, since, supervised, duty))
    persons = sorted(w.persons.items(), key=lambda kv: kv[1]["id"])
    o.comment("Persons: competitors (real names; DOB and e-mail generated where shown) and officials")
    prow = []
    for name, p in persons:
        dob = dob_for(p, name)
        note = None
        if p["generated"]:
            note = f"{GEN}: person"
        elif dob or p["email"]:
            note = f"{GEN}: date of birth" + (" and e-mail" if p["email"] else "")
        prow.append(((p["id"], p["first"], p["last"], dob, None, p["email"]), note))
    for oid, first, last, dob, gender, *_ in officials:
        prow.append(((oid, first, last, dob, gender, f"{first.lower()}.{last.lower().replace('ä', 'a').replace('ö', 'o')}@eukonkanto.example"),
                     f"{GEN}: official"))
    o.insert("PERSON", ["Person_ID", "First_Name", "Last_Name", "Date_of_Birth", "Gender", "Email"], prow)
    o.insert("PERSON_PHONE", ["Person_ID", "Phone"],
             [((oid, f"+358 44 200 {3000 + i}"), f"{GEN}: phone") for i, (oid, *_) in enumerate(officials)])
    cit = [((p["id"], iso), None) for _n, p in persons for iso in p["cit"]]
    cit += [((oid, "FIN"), f"{GEN}") for oid, *_ in officials]
    o.insert("PERSON_CITIZENSHIP", ["Person_ID", "ISO_Code"], cit)
    o.insert("COMPETITOR", ["Person_ID"], [((p["id"],), None) for _n, p in persons])
    chief = officials[0][0]
    o.insert("OFFICIAL", ["Person_ID", "Duty_Title", "Certified_Since", "Supervisor_ID"],
             [((oid, title, since, chief if sup else None), f"{GEN}: official")
              for oid, _f, _l, _d, _g, title, since, sup, _duty in officials])
    o.comment("Officials on duty at the 2026 and 2027 races")
    o.insert("OFFICIATES_IN", ["Official_ID", "Edition_Year", "Race_No", "Duty"],
             [((oid, y, r["no"], duty), f"{GEN}")
              for (y, _c), r in sorted(w.races.items()) if y >= 2026
              for oid, *_rest, duty in officials])

    # entries
    entries = sorted(w.entries.values(), key=lambda e: e["id"])
    o.comment("Entries (a pair or team that persists across years) and who fills each role")
    o.insert("ENTRY", ["Entry_ID", "Entry_Type", "Team_Name", "Represented_Organisation", "GP_Event_ID"],
             [((e["id"], e["type"], e["team"], e["org"], None), f"{GEN}: entry" if e["generated"] else None)
              for e in entries])
    pa = []
    for e in entries:
        for role, name in e["members"]:
            kg = weight_for(name) if role == "CARRIED" and e["recent"] else None
            pa.append(((e["id"], role, w.persons[name]["id"], kg), f"{GEN}: weight" if kg else None))
    o.insert("PARTICIPATES_AS", ["Entry_ID", "Role_Code", "Person_ID", "Measured_Weight_kg"], pa)
    o.insert("REPRESENTS", ["Entry_ID", "ISO_Code"], [((e["id"], iso), None) for e in entries for iso in dict.fromkeys(e["isos"])])

    o.comment("Registrations (one per entry per race); 2026 timestamps generated, bibs from the results")
    o.insert("REGISTRATION", ["Registration_ID", "Bib_No", "Registered_At", "Cancelled_At", "Payment_Status",
                              "Fee_Paid_EUR", "Entry_ID", "Edition_Year", "Race_No"],
             [((r["id"], r["bib"], str(r["at"]), str(r["cancelled"]) if r["cancelled"] else None, r["pay"],
                r["fee"], r["entry"]["id"], r["year"], r["race_no"]),
               r["note"] or (f"{GEN}: timestamp" if r["year"] == 2026 else None)) for r in w.regs])

    # recorders for 2026 results: the two timekeepers alternate (GENERATED)
    tks = [oid for oid, *_rest, duty in officials if duty == "Timekeeper"]
    reg_year = {r["id"]: r["year"] for r in w.regs}
    res_rows = []
    for i, res in enumerate(w.results):
        reg_id, stage, raw, status, _rec = res[:5]
        note = res[5] if len(res) > 5 else None
        rec = tks[i % 2] if reg_year[reg_id] == 2026 else None
        res_rows.append(((reg_id, stage, raw, status, rec), note or (f"{GEN}: recorder" if rec else None)))
    o.comment("Results per stage (times in seconds)")
    o.insert("RESULT", ["Registration_ID", "Stage", "Raw_Time_s", "Status", "Recorded_By_Official_ID"], res_rows)
    o.insert("PENALTY", ["Registration_ID", "Stage", "Penalty_No", "Adjustment_Type", "Seconds", "Reason"],
             [(p, None) for p in w.penalties])

    # awards: placement prizes by actual rank; historic winners; 2026 specials (GENERATED)
    awards = []
    by_race = {}
    for r in w.regs:
        by_race.setdefault((r["year"], r["series"]), []).append(r["id"])
    end_of = {y: e["end"] for y, e in w.editions.items()}
    for (y, series), reg_ids in sorted(by_race.items()):
        stage = "Final" if series == "SPR" else "Single"
        order = ranks(w.results, set(reg_ids), stage, w.penalties)
        if not order:
            continue
        best = min(t[2] + 0 for t in w.results if t[0] in reg_ids and t[1] == stage and t[3] == "Finished")
        places = order[:3] if y == 2026 else [rid for rid in order
                                              if next(t[2] for t in w.results if t[0] == rid and t[1] == stage) == best]
        for idx, rid in enumerate(places):
            rank = 1 if y != 2026 else idx + 1
            prize = {1: 1 if series == "MAIN" else 2, 2: 3, 3: 4}[rank]
            awards.append(((prize, rid, end_of[y]), None if y == 2026 else f"{GEN}: award date"))
    for prize, (series, bib) in reg_2027.SPECIAL_AWARDS_2026.items():
        awards.append(((prize, bib_reg[(series, bib)]["id"], end_of[2026]), f"{GEN}: special prize recipient"))
    o.comment("Prizes awarded")
    o.insert("AWARDED", ["Prize_ID", "Registration_ID", "Awarded_On"], awards)

    # protests (GENERATED)
    prot, votes = [], []
    jury = [oid for oid, *_rest, duty in officials if duty == "Jury"]
    for i, (series, bib, after, reason, outcome, decide_min, vs) in enumerate(reg_2027.PROTESTS_2026, start=1):
        race = w.races[(2026, series)]
        filed = race["last"] + dt.timedelta(minutes=after)
        decided = filed + dt.timedelta(minutes=decide_min) if decide_min else None
        reg = bib_reg[(series, bib)]
        prot.append(((i, str(filed), reason, outcome, str(decided) if decided else None, reg["entry"]["id"],
                      2026, race["no"]), f"{GEN}: protest"))
        for oid, v in zip(jury, vs or []):
            votes.append(((oid, i, v), f"{GEN}: vote"))
    o.comment("Protests to the jury and the jury's votes")
    o.insert("PROTEST", ["Protest_ID", "Filed_At", "Reason", "Outcome", "Decided_At", "Entry_ID", "Edition_Year",
                         "Race_No"], prot)
    o.insert("DECIDES", ["Official_ID", "Protest_ID", "Vote"], votes)

    o.comment("Market place vendors, product categories and booth bookings (prices from the market page)")
    o.insert("VENDOR", ["Vendor_ID", "Business_Name", "Contact_Name", "Phone", "Email"],
             [(v[:5], f"{GEN}: vendor") for v in ref.VENDORS])
    o.insert("VENDOR_PRODUCT_CATEGORY", ["Vendor_ID", "Category"],
             [((v[0], c), None) for v in ref.VENDORS for c in v[5]])
    o.insert("EXHIBITS_AT", ["Vendor_ID", "Edition_Year", "Booth_Size", "Booth_Fee_EUR", "Electricity_Required",
                             "Paid"], [(b, f"{GEN}: booking") for b in ref.BOOKINGS])
    sys.stdout.write(o.text())


if __name__ == "__main__":
    main()
