"""Prizes: what a series offers, awarding (I4) and re-assigning placement prizes after a change."""
import db
from api import as_int

FOR_SERIES_SQL = """
SELECT p.Prize_ID, p.Prize_Name, p.Prize_Type, p.Placement_Rank, p.Includes_Drink, p.Prize_Scope
FROM PRIZE p
JOIN OFFERS o ON o.Prize_ID = p.Prize_ID
WHERE o.Series_Code = %s
ORDER BY p.Prize_Type, p.Placement_Rank, p.Prize_Name"""


def for_series(series):
    return db.query(FOR_SERIES_SQL, (series,)), FOR_SERIES_SQL


AWARD_SQL = "INSERT INTO AWARDED (Prize_ID, Registration_ID, Awarded_On) VALUES (%s, %s, CURDATE())"


def award(payload):
    """I4: the trigger checks the series offers the prize and a placement prize matches the rank."""
    prize = as_int(payload.get("prize_id"), "prize_id", minimum=1)
    reg = as_int(payload.get("registration_id"), "registration_id", minimum=1)
    db.execute(AWARD_SQL, (prize, reg))
    return AWARD_SQL


DELETE_PLACEMENTS_SQL = """
DELETE a FROM AWARDED a
JOIN PRIZE p        ON p.Prize_ID = a.Prize_ID
JOIN REGISTRATION r ON r.Registration_ID = a.Registration_ID
WHERE p.Prize_Type = 'Placement' AND r.Edition_Year = %s AND r.Race_No = %s"""
INSERT_PLACEMENTS_SQL = """
INSERT INTO AWARDED (Prize_ID, Registration_ID, Awarded_On)
SELECT o.Prize_ID, v.Registration_ID, e.End_Date
FROM v_result v
JOIN SERIES s  ON s.Series_Code = v.Series_Code
JOIN EDITION e ON e.Edition_Year = v.Edition_Year
JOIN OFFERS o  ON o.Series_Code = v.Series_Code
JOIN PRIZE p   ON p.Prize_ID = o.Prize_ID
              AND p.Prize_Type = 'Placement' AND p.Placement_Rank = v.Rank_In_Stage
WHERE v.Edition_Year = %s AND v.Race_No = %s AND v.Stage = IF(s.Has_Heats, 'Final', 'Single')"""
REASSIGN_SQLS = (DELETE_PLACEMENTS_SQL, INSERT_PLACEMENTS_SQL)


def reassign_placements(cur, year, race_no):
    """Called inside U1/U3 transactions: placement prizes follow the recomputed ranks."""
    cur.execute(DELETE_PLACEMENTS_SQL, (year, race_no))
    cur.execute(INSERT_PLACEMENTS_SQL, (year, race_no))
