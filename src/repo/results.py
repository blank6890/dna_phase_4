"""Editions, results, records, champions and Grand Prix events (read-only)."""
import db

SERIES = {"MAIN", "WOMEN", "M40", "TEAM", "SPR"}
STAGES = {"Heat 1", "Heat 2", "Heat 3", "Final", "Single"}
SERIES_ORDER = "FIELD({col}, 'MAIN', 'WOMEN', 'M40', 'TEAM', 'SPR')"

EDITIONS_SQL = """
SELECT e.Edition_Year, e.Championship_Level, e.Start_Date, e.End_Date,
       e.Registration_Opens, e.Registration_Deadline,
       GROUP_CONCAT(ra.Series_Code ORDER BY ra.Race_No SEPARATOR ',') AS Series
FROM EDITION e
LEFT JOIN RACE ra ON ra.Edition_Year = e.Edition_Year
GROUP BY e.Edition_Year
ORDER BY e.Edition_Year DESC"""


def editions():
    return db.query(EDITIONS_SQL), EDITIONS_SQL


RESULTS_SQL = """
SELECT v.Rank_In_Stage, v.Bib_No, n.Display_Name, n.Team_Name, n.Countries,
       v.Stage, v.Status, v.Raw_Time_s, v.Penalty_s, v.Net_Time_s, v.Gap_To_Leader_s,
       v.Registration_ID, v.Entry_ID,
       (SELECT GROUP_CONCAT(CONCAT(pe.Adjustment_Type, ' ', CAST(pe.Seconds AS DOUBLE), ' s: ', pe.Reason)
                            ORDER BY pe.Penalty_No SEPARATOR '; ')
          FROM PENALTY pe
         WHERE pe.Registration_ID = v.Registration_ID AND pe.Stage = v.Stage) AS Adjustments,
       (SELECT GROUP_CONCAT(pe.Penalty_No ORDER BY pe.Penalty_No SEPARATOR ',')
          FROM PENALTY pe
         WHERE pe.Registration_ID = v.Registration_ID AND pe.Stage = v.Stage) AS Penalty_Nos
FROM v_result v
JOIN v_entry_name n ON n.Entry_ID = v.Entry_ID
WHERE v.Edition_Year = %s AND v.Series_Code = %s AND (%s IS NULL OR v.Stage = %s)
ORDER BY FIELD(v.Stage, 'Heat 1', 'Heat 2', 'Heat 3', 'Final', 'Single'),
         v.Rank_In_Stage IS NULL, v.Rank_In_Stage, v.Bib_No"""


def results(year, series, stage=None):
    return db.query(RESULTS_SQL, (year, series, stage, stage)), RESULTS_SQL


RECORDS_SQL = """
WITH best AS (
    SELECT Series_Code, MIN(Net_Time_s) AS Best_Time_s
    FROM v_result
    WHERE Status = 'Finished'
    GROUP BY Series_Code
)
SELECT s.Series_Code, s.Series_Name, best.Best_Time_s, v.Edition_Year,
       n.Display_Name, n.Team_Name, n.Countries
FROM best
JOIN v_result v     ON v.Series_Code = best.Series_Code AND v.Net_Time_s = best.Best_Time_s
JOIN SERIES s       ON s.Series_Code = best.Series_Code
JOIN v_entry_name n ON n.Entry_ID = v.Entry_ID
ORDER BY FIELD(s.Series_Code, 'MAIN', 'TEAM', 'SPR', 'M40', 'WOMEN')"""


def records():
    return db.query(RECORDS_SQL), RECORDS_SQL


CHAMPIONS_SQL = """
SELECT v.Edition_Year, e.Championship_Level, v.Series_Code, s.Series_Name,
       n.Display_Name, n.Team_Name, n.Countries, v.Net_Time_s
FROM v_result v
JOIN SERIES s       ON s.Series_Code = v.Series_Code
JOIN EDITION e      ON e.Edition_Year = v.Edition_Year
JOIN v_entry_name n ON n.Entry_ID = v.Entry_ID
WHERE v.Rank_In_Stage = 1
  AND v.Stage = IF(s.Has_Heats, 'Final', 'Single')
ORDER BY v.Edition_Year DESC, FIELD(v.Series_Code, 'MAIN', 'WOMEN', 'M40', 'TEAM', 'SPR')"""


def champions():
    return db.query(CHAMPIONS_SQL), CHAMPIONS_SQL


GRAND_PRIX_SQL = """
SELECT g.GP_Event_ID, g.Event_Name, g.Event_Month_Year, g.City, g.Region, g.Organiser,
       c.ISO_Code, c.Country_Name, c.Continent
FROM GRAND_PRIX_EVENT g
JOIN COUNTRY c ON c.ISO_Code = g.Host_ISO_Code
ORDER BY c.Continent, g.Event_Month_Year DESC"""


def grand_prix():
    return db.query(GRAND_PRIX_SQL), GRAND_PRIX_SQL


# ---------------------------------------------------------------- jury writes (I2, U1)
from api import ApiError, as_choice, as_float, as_int, as_str  # noqa: E402
from repo import prizes  # noqa: E402

STATUSES = {"Finished", "DNS", "DNF", "DQ"}
ADJUSTMENTS = {"Penalty", "Bonus", "Warning"}

OFFICIALS_SQL = """
SELECT o.Person_ID, p.First_Name, p.Last_Name, o.Duty_Title, o.Certified_Since, o.Supervisor_ID
FROM OFFICIAL o
JOIN PERSON p ON p.Person_ID = o.Person_ID
ORDER BY o.Supervisor_ID IS NOT NULL, o.Duty_Title, p.Last_Name"""


def officials():
    return db.query(OFFICIALS_SQL), OFFICIALS_SQL


RACE_OF_SQL = "SELECT Edition_Year, Race_No FROM REGISTRATION WHERE Registration_ID = %s"
INSERT_RESULT_SQL = ("INSERT INTO RESULT (Registration_ID, Stage, Raw_Time_s, Status, Recorded_By_Official_ID) "
                     "VALUES (%s, %s, %s, %s, %s)")
NEXT_PENALTY_SQL = ("SELECT COALESCE(MAX(Penalty_No), 0) + 1 AS n FROM PENALTY "
                    "WHERE Registration_ID = %s AND Stage = %s FOR UPDATE")
INSERT_PENALTY_SQL = ("INSERT INTO PENALTY (Registration_ID, Stage, Penalty_No, Adjustment_Type, Seconds, Reason) "
                      "VALUES (%s, %s, %s, %s, %s, %s)")
CURRENT_RESULT_SQL = ("SELECT Raw_Time_s, Status FROM RESULT WHERE Registration_ID = %s AND Stage = %s "
                      "FOR UPDATE")
UPDATE_RESULT_SQL = ("UPDATE RESULT SET Raw_Time_s = %s, Status = %s, Recorded_By_Official_ID = %s "
                     "WHERE Registration_ID = %s AND Stage = %s")
TOUCH_RESULT_SQL = ("UPDATE RESULT SET Recorded_By_Official_ID = %s "
                    "WHERE Registration_ID = %s AND Stage = %s")


def _time_for(status, raw):
    if status == "Finished" and raw is None:
        raise ApiError(400, "A finished result needs a time")
    if status != "Finished" and raw is not None:
        raise ApiError(400, f"A {status} result has no time")
    if raw is not None and raw <= 0:
        raise ApiError(400, "Time must be above 0")
    return raw


def _penalty(p):
    if not isinstance(p, dict):
        raise ApiError(400, "Each penalty must be an object")
    kind = as_choice(p.get("type"), "penalty type", ADJUSTMENTS)
    seconds = as_float(p.get("seconds"), "penalty seconds", required=(kind != "Warning"), maximum=600) or 0
    return kind, seconds, as_str(p.get("reason"), "penalty reason", max_len=200)


def _race_of(cur, reg):
    cur.execute(RACE_OF_SQL, (reg,))
    row = cur.fetchone()
    if row is None:
        raise ApiError(404, "Registration not found")
    return row["Edition_Year"], row["Race_No"]


def record_result(payload):
    """I2: result (+ optional penalties) for one registration and stage; triggers check the rules."""
    reg = as_int(payload.get("registration_id"), "registration_id", minimum=1)
    stage = as_choice(payload.get("stage"), "stage", STAGES)
    status = as_choice(payload.get("status"), "status", STATUSES)
    raw = _time_for(status, as_float(payload.get("raw_time_s"), "raw_time_s", required=False, maximum=3600))
    official = as_int(payload.get("official_id"), "official_id", minimum=1)
    penalties = [_penalty(p) for p in (payload.get("penalties") or [])]
    with db.transaction() as cur:
        year, race_no = _race_of(cur, reg)
        cur.execute(INSERT_RESULT_SQL, (reg, stage, raw, status, official))
        for no, (kind, seconds, reason) in enumerate(penalties, start=1):
            cur.execute(INSERT_PENALTY_SQL, (reg, stage, no, kind, seconds, reason))
        prizes.reassign_placements(cur, year, race_no)
    return (INSERT_RESULT_SQL, INSERT_PENALTY_SQL, *prizes.REASSIGN_SQLS)


def correct_result(reg, stage, payload):
    """U1: correct a time or status; ranks follow from v_result, placement prizes are re-assigned."""
    stage = as_choice(stage, "stage", STAGES)
    official = as_int(payload.get("official_id"), "official_id", minimum=1)
    with db.transaction() as cur:
        cur.execute(CURRENT_RESULT_SQL, (reg, stage))
        current = cur.fetchone()
        if current is None:
            raise ApiError(404, "Result not found")
        status = as_choice(payload.get("status"), "status", STATUSES, required=False) or current["Status"]
        raw = as_float(payload.get("raw_time_s"), "raw_time_s", required=False, maximum=3600)
        if raw is None and status == "Finished" and "raw_time_s" not in payload:
            raw = current["Raw_Time_s"]
        raw = _time_for(status, raw)
        year, race_no = _race_of(cur, reg)
        cur.execute(UPDATE_RESULT_SQL, (raw, status, official, reg, stage))
        prizes.reassign_placements(cur, year, race_no)
    return (UPDATE_RESULT_SQL, *prizes.REASSIGN_SQLS)


def add_penalty(payload):
    """U1: add a time penalty / bonus / warning to a result."""
    reg = as_int(payload.get("registration_id"), "registration_id", minimum=1)
    stage = as_choice(payload.get("stage"), "stage", STAGES)
    official = as_int(payload.get("official_id"), "official_id", minimum=1)
    kind, seconds, reason = _penalty(payload)
    with db.transaction() as cur:
        year, race_no = _race_of(cur, reg)
        cur.execute(NEXT_PENALTY_SQL, (reg, stage))
        number = cur.fetchone()["n"]
        cur.execute(INSERT_PENALTY_SQL, (reg, stage, number, kind, seconds, reason))
        cur.execute(TOUCH_RESULT_SQL, (official, reg, stage))
        prizes.reassign_placements(cur, year, race_no)
    return (NEXT_PENALTY_SQL, INSERT_PENALTY_SQL, TOUCH_RESULT_SQL, *prizes.REASSIGN_SQLS)
