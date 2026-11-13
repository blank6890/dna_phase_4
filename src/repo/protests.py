"""Protests: listing (S2); writes in Task 9."""
import db

OUTCOMES = {"Pending", "Upheld", "Rejected"}

LIST_SQL = """
SELECT pr.Protest_ID, pr.Filed_At, pr.Reason, pr.Outcome, pr.Decided_At,
       pr.Entry_ID, pr.Edition_Year, pr.Race_No, ra.Series_Code, n.Display_Name, n.Team_Name
FROM PROTEST pr
JOIN RACE ra        ON ra.Edition_Year = pr.Edition_Year AND ra.Race_No = pr.Race_No
JOIN v_entry_name n ON n.Entry_ID = pr.Entry_ID
WHERE (%s IS NULL OR pr.Outcome = %s)
ORDER BY pr.Filed_At DESC"""


def list_protests(outcome=None):
    return db.query(LIST_SQL, (outcome, outcome)), LIST_SQL


# ---------------------------------------------------------------- writes (I3, U3)
from api import ApiError, as_choice, as_datetime, as_int, as_str  # noqa: E402
from repo import prizes  # noqa: E402

FILE_SQL = ("INSERT INTO PROTEST (Filed_At, Reason, Entry_ID, Edition_Year, Race_No) "
            "VALUES (COALESCE(%s, NOW()), %s, %s, %s, %s)")


def file_protest(payload):
    """I3: the trigger checks the 15-minute window and that the entry ran in the race."""
    values = (as_datetime(payload.get("filed_at"), "filed_at", required=False),
              as_str(payload.get("reason"), "reason", max_len=500),
              as_int(payload.get("entry_id"), "entry_id", minimum=1),
              as_int(payload.get("year"), "year"),
              as_int(payload.get("race_no"), "race_no", minimum=1))
    protest_id = db.execute(FILE_SQL, values)
    return protest_id, FILE_SQL


LOCK_SQL = "SELECT Outcome, Edition_Year, Race_No FROM PROTEST WHERE Protest_ID = %s FOR UPDATE"
DECIDE_SQL = "UPDATE PROTEST SET Outcome = %s, Decided_At = NOW() WHERE Protest_ID = %s"
VOTE_SQL = "INSERT INTO DECIDES (Official_ID, Protest_ID, Vote) VALUES (%s, %s, %s)"
REMOVE_PENALTY_SQL = """
DELETE pe FROM PENALTY pe
JOIN REGISTRATION r ON r.Registration_ID = pe.Registration_ID
WHERE pe.Registration_ID = %s AND pe.Stage = %s AND pe.Penalty_No = %s
  AND r.Edition_Year = %s AND r.Race_No = %s"""
DISQUALIFY_SQL = """
UPDATE RESULT res
JOIN REGISTRATION r ON r.Registration_ID = res.Registration_ID
SET res.Status = 'DQ', res.Raw_Time_s = NULL
WHERE res.Registration_ID = %s AND res.Stage = %s AND r.Edition_Year = %s AND r.Race_No = %s"""


def decide(protest_id, payload):
    """U3: outcome + votes; if upheld, remove the contested penalty or disqualify, then re-assign prizes."""
    outcome = as_choice(payload.get("outcome"), "outcome", {"Upheld", "Rejected"})
    votes = payload.get("votes") or []
    if not isinstance(votes, list):
        raise ApiError(400, "votes must be a list")
    votes = [(as_int(v.get("official_id"), "official_id", minimum=1),
              as_choice(v.get("vote"), "vote", {"Uphold", "Reject"})) for v in votes if isinstance(v, dict)]
    action = payload.get("action")
    if action and outcome != "Upheld":
        raise ApiError(400, "Only an upheld protest changes results")
    sqls = [LOCK_SQL, DECIDE_SQL, VOTE_SQL]
    with db.transaction() as cur:
        cur.execute(LOCK_SQL, (protest_id,))
        protest = cur.fetchone()
        if protest is None:
            raise ApiError(404, "Protest not found")
        if protest["Outcome"] != "Pending":
            raise ApiError(409, "This protest has already been decided")
        year, race_no = protest["Edition_Year"], protest["Race_No"]
        cur.execute(DECIDE_SQL, (outcome, protest_id))
        for official, vote in votes:
            cur.execute(VOTE_SQL, (official, protest_id, vote))
        if action:
            if not isinstance(action, dict):
                raise ApiError(400, "action must be an object")
            if "remove_penalty" in action:
                reg, stage, number = action["remove_penalty"]
                cur.execute(REMOVE_PENALTY_SQL, (as_int(reg, "registration"), as_str(stage, "stage", max_len=10),
                                                 as_int(number, "penalty number"), year, race_no))
                sqls.append(REMOVE_PENALTY_SQL)
            elif "disqualify" in action:
                reg, stage = action["disqualify"]
                cur.execute(DISQUALIFY_SQL, (as_int(reg, "registration"), as_str(stage, "stage", max_len=10),
                                             year, race_no))
                sqls.append(DISQUALIFY_SQL)
            else:
                raise ApiError(400, "action must be remove_penalty or disqualify")
            if cur.rowcount == 0:
                raise ApiError(404, "The penalty or result to change is not in this race")
            prizes.reassign_placements(cur, year, race_no)
            sqls += prizes.REASSIGN_SQLS
    return sqls
