"""Registrations: listing (S1), persons per edition (P1), heaviest carried (A5); writes in Task 8."""
import db

LIST_SQL = """
SELECT r.Registration_ID, r.Bib_No, r.Registered_At, r.Cancelled_At, r.Payment_Status,
       r.Fee_Paid_EUR, r.Status, r.Refund_EUR, r.Entry_ID, r.Edition_Year, r.Race_No,
       r.Series_Code, r.Carried_Weight_kg, r.Required_Backpack_kg,
       n.Display_Name, n.Team_Name, n.Countries
FROM v_registration r
JOIN v_entry_name n ON n.Entry_ID = r.Entry_ID
WHERE r.Edition_Year = %s AND r.Series_Code = %s
ORDER BY r.Status DESC, r.Bib_No"""


def list_for_race(year, series):
    return db.query(LIST_SQL, (year, series)), LIST_SQL


PERSONS_SQL = """
SELECT DISTINCT p.First_Name, p.Last_Name, p.Date_of_Birth
FROM PERSON p
JOIN PARTICIPATES_AS pa ON pa.Person_ID = p.Person_ID
JOIN REGISTRATION r     ON r.Entry_ID = pa.Entry_ID
WHERE r.Edition_Year = %s AND r.Cancelled_At IS NULL
ORDER BY p.Last_Name, p.First_Name"""


def persons_in_edition(year):
    return db.query(PERSONS_SQL, (year,)), PERSONS_SQL


HEAVIEST_SQL = """
SELECT p.First_Name, p.Last_Name, pa.Measured_Weight_kg, n.Display_Name, ra.Series_Code, r.Bib_No
FROM PARTICIPATES_AS pa
JOIN PERSON p       ON p.Person_ID = pa.Person_ID
JOIN REGISTRATION r ON r.Entry_ID = pa.Entry_ID
JOIN RACE ra        ON ra.Edition_Year = r.Edition_Year AND ra.Race_No = r.Race_No
JOIN v_entry_name n ON n.Entry_ID = pa.Entry_ID
WHERE r.Edition_Year = %s AND r.Cancelled_At IS NULL AND pa.Role_Code = 'CARRIED'
  AND pa.Measured_Weight_kg = (
        SELECT MAX(pa2.Measured_Weight_kg)
        FROM PARTICIPATES_AS pa2
        JOIN REGISTRATION r2 ON r2.Entry_ID = pa2.Entry_ID
        WHERE r2.Edition_Year = %s AND r2.Cancelled_At IS NULL AND pa2.Role_Code = 'CARRIED')
ORDER BY ra.Race_No"""


def heaviest_carried(year):
    return db.query(HEAVIEST_SQL, (year, year)), HEAVIEST_SQL


# ---------------------------------------------------------------- writes (I1, U2, U4, D1, D2)
from api import ApiError, as_choice, as_date, as_float, as_int, as_str  # noqa: E402

ROLES = {"CARRIER_1", "CARRIER_2", "CARRIER_3", "CARRIED"}
GENDERS = {"Female", "Male", "Other"}

INSERT_PERSON_SQL = ("INSERT INTO PERSON (First_Name, Last_Name, Date_of_Birth, Gender, Email) "
                     "VALUES (%s, %s, %s, %s, %s)")
INSERT_COMPETITOR_SQL = "INSERT IGNORE INTO COMPETITOR (Person_ID) VALUES (%s)"
INSERT_CITIZENSHIP_SQL = "INSERT INTO PERSON_CITIZENSHIP (Person_ID, ISO_Code) VALUES (%s, %s)"
FIND_ENTRY_SQL = """
SELECT pa.Entry_ID
FROM PARTICIPATES_AS pa
JOIN ENTRY e ON e.Entry_ID = pa.Entry_ID
WHERE e.Entry_Type = %s AND (pa.Role_Code, pa.Person_ID) IN ({pairs})
GROUP BY pa.Entry_ID
HAVING COUNT(*) = %s
   AND COUNT(*) = (SELECT COUNT(*) FROM PARTICIPATES_AS x WHERE x.Entry_ID = pa.Entry_ID)
LIMIT 1"""
INSERT_ENTRY_SQL = ("INSERT INTO ENTRY (Entry_Type, Team_Name, Represented_Organisation) "
                    "VALUES (%s, %s, %s)")
INSERT_PARTICIPANT_SQL = ("INSERT INTO PARTICIPATES_AS (Entry_ID, Role_Code, Person_ID, Measured_Weight_kg) "
                          "VALUES (%s, %s, %s, %s)")
INSERT_REPRESENTS_SQL = "INSERT INTO REPRESENTS (Entry_ID, ISO_Code) VALUES (%s, %s)"
NEXT_BIB_SQL = ("SELECT COALESCE(MAX(Bib_No), 0) + 1 AS bib FROM REGISTRATION "
                "WHERE Edition_Year = %s FOR UPDATE")
INSERT_REGISTRATION_SQL = """
INSERT INTO REGISTRATION (Bib_No, Registered_At, Payment_Status, Fee_Paid_EUR, Entry_ID, Edition_Year, Race_No)
SELECT %s, NOW(), 'Paid', ra.Entry_Fee_EUR, %s, ra.Edition_Year, ra.Race_No
FROM RACE ra
WHERE ra.Edition_Year = %s AND ra.Series_Code = %s"""
FEE_SQL = "SELECT Fee_Paid_EUR FROM REGISTRATION WHERE Registration_ID = %s"


def _iso(value, name):
    code = as_str(value, name, max_len=3)
    if len(code) != 3 or not code.isalpha():
        raise ApiError(400, f"{name} must be a 3-letter ISO country code")
    return code.upper()


def _new_person(data, label):
    if not isinstance(data, dict):
        raise ApiError(400, f"{label}: new person details must be an object")
    return {"first": as_str(data.get("first_name"), f"{label} first name", max_len=60),
            "last": as_str(data.get("last_name"), f"{label} last name", max_len=60),
            "dob": as_date(data.get("dob"), f"{label} date of birth"),
            "gender": as_choice(data.get("gender"), f"{label} gender", GENDERS, required=False),
            "email": as_str(data.get("email"), f"{label} e-mail", required=False, max_len=120),
            "citizenship": _iso(data.get("citizenship"), f"{label} citizenship")}


def _member(data, index):
    if not isinstance(data, dict):
        raise ApiError(400, f"Member {index + 1} must be an object")
    role = as_choice(data.get("role"), f"Member {index + 1} role", ROLES)
    weight = as_float(data.get("weight_kg"), f"{role} weight", required=(role == "CARRIED"))
    if weight is not None and role != "CARRIED":
        raise ApiError(400, "Only the carried person has a measured weight")
    if data.get("person_id") is not None:
        return {"role": role, "person_id": as_int(data["person_id"], f"{role} person", minimum=1),
                "weight": weight}
    return {"role": role, "new": _new_person(data.get("new"), role), "weight": weight}


def parse_registration(payload, series_allowed):
    entry_type = as_choice(payload.get("entry_type"), "entry_type", {"Pair", "Team"})
    members = payload.get("members")
    if not isinstance(members, list) or not members:
        raise ApiError(400, "members must be a non-empty list")
    parsed = [_member(m, i) for i, m in enumerate(members)]
    roles = [m["role"] for m in parsed]
    if len(set(roles)) != len(roles):
        raise ApiError(400, "Each role can be filled only once")
    countries = payload.get("countries")
    if not isinstance(countries, list) or not countries:
        raise ApiError(400, "countries must be a non-empty list")
    return {
        "year": as_int(payload.get("year"), "year"),
        "series": as_choice(payload.get("series"), "series", series_allowed),
        "entry_type": entry_type,
        "team_name": as_str(payload.get("team_name"), "team_name", required=(entry_type == "Team")),
        "organisation": as_str(payload.get("organisation"), "organisation", required=False),
        "countries": list(dict.fromkeys(_iso(c, "country") for c in countries)),
        "members": parsed,
    }


def _person_id(cur, member):
    """Insert a new person (with COMPETITOR and citizenship) or reuse an existing one."""
    if "person_id" in member:
        pid = member["person_id"]
    else:
        p = member["new"]
        cur.execute(INSERT_PERSON_SQL, (p["first"], p["last"], p["dob"], p["gender"], p["email"]))
        pid = cur.lastrowid
        cur.execute(INSERT_CITIZENSHIP_SQL, (pid, p["citizenship"]))
    cur.execute(INSERT_COMPETITOR_SQL, (pid,))
    return pid


def register(payload, series_allowed):
    """I1: one transaction for persons, entry, roles, countries and the registration."""
    data = parse_registration(payload, series_allowed)
    with db.transaction() as cur:
        members = [(m, _person_id(cur, m)) for m in data["members"]]
        entry_id = None
        find_sql = None
        if all("person_id" in m for m, _ in members):
            find_sql = FIND_ENTRY_SQL.format(pairs=", ".join(["(%s, %s)"] * len(members)))
            params = [data["entry_type"]]
            for m, pid in members:
                params += [m["role"], pid]
            cur.execute(find_sql, (*params, len(members)))
            found = cur.fetchone()
            entry_id = found["Entry_ID"] if found else None
        if entry_id is None:
            cur.execute(INSERT_ENTRY_SQL, (data["entry_type"],
                                           data["team_name"] if data["entry_type"] == "Team" else None,
                                           data["organisation"] if data["entry_type"] == "Team" else None))
            entry_id = cur.lastrowid
            for m, pid in members:
                cur.execute(INSERT_PARTICIPANT_SQL, (entry_id, m["role"], pid, m["weight"]))
            for iso in data["countries"]:
                cur.execute(INSERT_REPRESENTS_SQL, (entry_id, iso))
        cur.execute(NEXT_BIB_SQL, (data["year"],))
        bib = cur.fetchone()["bib"]
        cur.execute(INSERT_REGISTRATION_SQL, (bib, entry_id, data["year"], data["series"]))
        if cur.rowcount == 0:
            raise ApiError(404, f"There is no {data['series']} race in {data['year']}")
        reg_id = cur.lastrowid
        cur.execute(FEE_SQL, (reg_id,))
        fee = float(cur.fetchone()["Fee_Paid_EUR"])
    sqls = [INSERT_PERSON_SQL, INSERT_COMPETITOR_SQL, INSERT_CITIZENSHIP_SQL]
    sqls += [find_sql] if find_sql else []
    sqls += [INSERT_ENTRY_SQL, INSERT_PARTICIPANT_SQL, INSERT_REPRESENTS_SQL, NEXT_BIB_SQL,
             INSERT_REGISTRATION_SQL]
    return {"registration_id": reg_id, "entry_id": entry_id, "bib_no": bib, "fee": fee}, sqls


DETAIL_SQL = """
SELECT r.Registration_ID, r.Bib_No, r.Registered_At, r.Cancelled_At, r.Payment_Status, r.Fee_Paid_EUR,
       r.Status, r.Refund_EUR, r.Entry_ID, r.Edition_Year, r.Series_Code, r.Race_Start,
       n.Display_Name, n.Team_Name, n.Countries, n.Entry_Type,
       EXISTS (SELECT 1 FROM RESULT x WHERE x.Registration_ID = r.Registration_ID) AS Has_Results
FROM v_registration r
JOIN v_entry_name n ON n.Entry_ID = r.Entry_ID
WHERE r.Registration_ID = %s"""
MEMBERS_SQL = """
SELECT pa.Role_Code, ro.Role_Name, p.Person_ID, p.First_Name, p.Last_Name, p.Date_of_Birth,
       pa.Measured_Weight_kg
FROM PARTICIPATES_AS pa
JOIN PERSON p  ON p.Person_ID = pa.Person_ID
JOIN ROLE ro   ON ro.Role_Code = pa.Role_Code
WHERE pa.Entry_ID = %s
ORDER BY ro.Leg_Order IS NULL, ro.Leg_Order"""


def details(reg_id):
    found = db.query(DETAIL_SQL, (reg_id,))
    if not found:
        raise ApiError(404, "Registration not found")
    return found[0], db.query(MEMBERS_SQL, (found[0]["Entry_ID"],)), (DETAIL_SQL, MEMBERS_SQL)


CANCEL_SQL = """
UPDATE REGISTRATION r
JOIN RACE ra ON ra.Edition_Year = r.Edition_Year AND ra.Race_No = r.Race_No
SET r.Cancelled_At = NOW(),
    r.Bib_No = NULL,
    r.Payment_Status = IF(NOW() <= ra.Scheduled_Start - INTERVAL 30 DAY, 'Refunded', r.Payment_Status)
WHERE r.Registration_ID = %s AND r.Cancelled_At IS NULL"""
REFUND_SQL = "SELECT Refund_EUR FROM v_registration WHERE Registration_ID = %s"
EXISTS_SQL = "SELECT Cancelled_At FROM REGISTRATION WHERE Registration_ID = %s"


def cancel(reg_id):
    """U2: cancel, release the bib, refund by the 30-day rule (the trigger refuses if results exist)."""
    with db.transaction() as cur:
        cur.execute(CANCEL_SQL, (reg_id,))
        if cur.rowcount == 0:
            cur.execute(EXISTS_SQL, (reg_id,))
            if cur.fetchone() is None:
                raise ApiError(404, "Registration not found")
            raise ApiError(409, "This registration is already cancelled")
        cur.execute(REFUND_SQL, (reg_id,))
        refund = float(cur.fetchone()["Refund_EUR"])
    return refund, (CANCEL_SQL, REFUND_SQL)


REPLACE_SQL = "UPDATE PARTICIPATES_AS SET Person_ID = %s, Measured_Weight_kg = %s WHERE Entry_ID = %s AND Role_Code = %s"
ROLE_EXISTS_SQL = "SELECT 1 FROM PARTICIPATES_AS WHERE Entry_ID = %s AND Role_Code = %s"


def replace_member(entry_id, role, payload):
    """U4: put another person in one role (triggers re-check results, ages and role shape)."""
    role = as_choice(role, "role", ROLES)
    member = _member({**payload, "role": role}, 0)
    with db.transaction() as cur:
        cur.execute(ROLE_EXISTS_SQL, (entry_id, role))
        if cur.fetchone() is None:
            raise ApiError(404, "This entry has no such role")
        pid = _person_id(cur, member)
        cur.execute(REPLACE_SQL, (pid, member["weight"], entry_id, role))
    return pid, (INSERT_PERSON_SQL, REPLACE_SQL)


LOCK_SQL = "SELECT Cancelled_At FROM REGISTRATION WHERE Registration_ID = %s FOR UPDATE"
HAS_RESULTS_SQL = "SELECT EXISTS (SELECT 1 FROM RESULT WHERE Registration_ID = %s) AS x"
HAS_AWARDS_SQL = "SELECT EXISTS (SELECT 1 FROM AWARDED WHERE Registration_ID = %s) AS x"
DELETE_SQL = "DELETE FROM REGISTRATION WHERE Registration_ID = %s"


def delete(reg_id):
    """D1: only a live registration with no results and no awards."""
    with db.transaction() as cur:
        cur.execute(LOCK_SQL, (reg_id,))
        row = cur.fetchone()
        if row is None:
            raise ApiError(404, "Registration not found")
        if row["Cancelled_At"] is not None:
            raise ApiError(409, "Registration is cancelled")
        cur.execute(HAS_RESULTS_SQL, (reg_id,))
        if cur.fetchone()["x"]:
            raise ApiError(409, "Registration has results")
        cur.execute(HAS_AWARDS_SQL, (reg_id,))
        if cur.fetchone()["x"]:
            raise ApiError(409, "Registration has awards")
        cur.execute(DELETE_SQL, (reg_id,))
    return (LOCK_SQL, HAS_RESULTS_SQL, HAS_AWARDS_SQL, DELETE_SQL)


UNREGISTERED_SQL = """
SELECT e.Entry_ID, e.Entry_Type, e.Team_Name, n.Display_Name, n.Countries
FROM ENTRY e
JOIN v_entry_name n ON n.Entry_ID = e.Entry_ID
WHERE NOT EXISTS (SELECT 1 FROM REGISTRATION r WHERE r.Entry_ID = e.Entry_ID)
ORDER BY e.Entry_ID"""
DELETE_ENTRY_SQL = "DELETE FROM ENTRY WHERE Entry_ID = %s"


def unregistered_entries():
    return db.query(UNREGISTERED_SQL), UNREGISTERED_SQL


def delete_entry(entry_id):
    """D2: FK RESTRICT from REGISTRATION refuses entries still registered; roles and countries cascade."""
    with db.transaction() as cur:
        cur.execute(DELETE_ENTRY_SQL, (entry_id,))
        if cur.rowcount == 0:
            raise ApiError(404, "Entry not found")
    return DELETE_ENTRY_SQL
