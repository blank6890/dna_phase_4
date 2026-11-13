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
