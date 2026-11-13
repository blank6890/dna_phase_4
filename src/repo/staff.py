"""Staff Desk accounts: one login per official (password checked against a Werkzeug hash)."""
import db

ACCOUNT_SQL = """
SELECT s.Person_ID, s.Username, s.Password_Hash, p.First_Name, p.Last_Name, o.Duty_Title
FROM STAFF_ACCOUNT s
JOIN OFFICIAL o ON o.Person_ID = s.Person_ID
JOIN PERSON p   ON p.Person_ID = s.Person_ID
WHERE s.Username = %s"""

OFFICIAL_SQL = """
SELECT s.Person_ID, s.Username, p.First_Name, p.Last_Name, o.Duty_Title
FROM STAFF_ACCOUNT s
JOIN OFFICIAL o ON o.Person_ID = s.Person_ID
JOIN PERSON p   ON p.Person_ID = s.Person_ID
WHERE s.Person_ID = %s"""


def account(username):
    rows = db.query(ACCOUNT_SQL, (username,))
    return rows[0] if rows else None


def official(person_id):
    rows = db.query(OFFICIAL_SQL, (person_id,))
    return rows[0] if rows else None
