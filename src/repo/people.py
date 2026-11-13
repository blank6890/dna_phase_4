"""Competitors, entries, teams and person search (read-only)."""
import db

ENTRIES_SQL = """
SELECT r.Registration_ID, r.Bib_No, r.Entry_ID, n.Display_Name, n.Team_Name, n.Countries,
       (SELECT GROUP_CONCAT(CONCAT_WS(' ', p.First_Name, NULLIF(p.Last_Name, ''))
                            ORDER BY ro.Leg_Order SEPARATOR ', ')
          FROM PARTICIPATES_AS pa
          JOIN PERSON p  ON p.Person_ID = pa.Person_ID
          JOIN ROLE ro   ON ro.Role_Code = pa.Role_Code
         WHERE pa.Entry_ID = r.Entry_ID AND pa.Role_Code <> 'CARRIED') AS Carriers,
       (SELECT CONCAT_WS(' ', p.First_Name, NULLIF(p.Last_Name, ''))
          FROM PARTICIPATES_AS pa
          JOIN PERSON p ON p.Person_ID = pa.Person_ID
         WHERE pa.Entry_ID = r.Entry_ID AND pa.Role_Code = 'CARRIED') AS Carried
FROM v_registration r
JOIN v_entry_name n ON n.Entry_ID = r.Entry_ID
WHERE r.Edition_Year = %s AND r.Series_Code = %s AND r.Status = 'Registered'
  AND (%s IS NULL OR EXISTS (SELECT 1 FROM REPRESENTS rp
                              WHERE rp.Entry_ID = r.Entry_ID AND rp.ISO_Code = %s))
ORDER BY r.Bib_No"""


def entries(year, series, country=None):
    return db.query(ENTRIES_SQL, (year, series, country, country)), ENTRIES_SQL


TEAMS_SQL = """
SELECT DISTINCT Team_Name, Represented_Organisation
FROM ENTRY
WHERE Entry_Type = 'Team'
ORDER BY Team_Name"""


def teams():
    return db.query(TEAMS_SQL), TEAMS_SQL


SEARCH_PERSONS_SQL = """
SELECT p.Person_ID, p.First_Name, p.Last_Name,
       GROUP_CONCAT(DISTINCT c.ISO_Code ORDER BY c.ISO_Code SEPARATOR '/') AS Citizenship,
       EXISTS (SELECT 1 FROM OFFICIAL o WHERE o.Person_ID = p.Person_ID) AS Is_Official,
       (SELECT COUNT(*) FROM PARTICIPATES_AS pa
          JOIN REGISTRATION r ON r.Entry_ID = pa.Entry_ID
         WHERE pa.Person_ID = p.Person_ID) AS Registrations
FROM PERSON p
LEFT JOIN PERSON_CITIZENSHIP c ON c.Person_ID = p.Person_ID
WHERE p.First_Name LIKE %s OR p.Last_Name LIKE %s
   OR CONCAT_WS(' ', p.First_Name, p.Last_Name) LIKE %s
GROUP BY p.Person_ID, p.First_Name, p.Last_Name
ORDER BY p.Last_Name, p.First_Name
LIMIT 100"""


def search_persons(q):
    pattern = db.like(q)
    return db.query(SEARCH_PERSONS_SQL, (pattern, pattern, pattern)), SEARCH_PERSONS_SQL


SEARCH_TEAMS_SQL = """
SELECT e.Entry_ID, e.Team_Name, e.Represented_Organisation, n.Display_Name, n.Countries,
       GROUP_CONCAT(DISTINCT r.Edition_Year ORDER BY r.Edition_Year SEPARATOR ', ') AS Years
FROM ENTRY e
JOIN v_entry_name n      ON n.Entry_ID = e.Entry_ID
LEFT JOIN REGISTRATION r ON r.Entry_ID = e.Entry_ID
WHERE e.Entry_Type = 'Team'
  AND (e.Team_Name LIKE %s OR e.Represented_Organisation LIKE %s)
GROUP BY e.Entry_ID, e.Team_Name, e.Represented_Organisation, n.Display_Name, n.Countries
ORDER BY e.Team_Name, Years"""


def search_teams(q):
    pattern = db.like(q)
    return db.query(SEARCH_TEAMS_SQL, (pattern, pattern)), SEARCH_TEAMS_SQL


PERSON_SQL = """
SELECT p.Person_ID, p.First_Name, p.Last_Name, p.Date_of_Birth,
       GROUP_CONCAT(c.Country_Name ORDER BY c.Country_Name SEPARATOR ', ') AS Citizenship
FROM PERSON p
LEFT JOIN PERSON_CITIZENSHIP pc ON pc.Person_ID = p.Person_ID
LEFT JOIN COUNTRY c             ON c.ISO_Code = pc.ISO_Code
WHERE p.Person_ID = %s
GROUP BY p.Person_ID, p.First_Name, p.Last_Name, p.Date_of_Birth"""

HISTORY_SQL = """
SELECT r.Edition_Year, ra.Series_Code, s.Series_Name, ro.Role_Name, n.Display_Name, n.Team_Name,
       r.Bib_No, IF(r.Cancelled_At IS NULL, 'Registered', 'Cancelled') AS Registration_Status,
       v.Stage, v.Status AS Result_Status, v.Net_Time_s, v.Rank_In_Stage
FROM PARTICIPATES_AS pa
JOIN REGISTRATION r ON r.Entry_ID = pa.Entry_ID
JOIN RACE ra        ON ra.Edition_Year = r.Edition_Year AND ra.Race_No = r.Race_No
JOIN SERIES s       ON s.Series_Code = ra.Series_Code
JOIN ROLE ro        ON ro.Role_Code = pa.Role_Code
JOIN v_entry_name n ON n.Entry_ID = pa.Entry_ID
LEFT JOIN v_result v
       ON v.Registration_ID = r.Registration_ID
      AND v.Stage = (SELECT x.Stage FROM RESULT x WHERE x.Registration_ID = r.Registration_ID
                     ORDER BY FIELD(x.Stage, 'Final', 'Single', 'Heat 3', 'Heat 2', 'Heat 1') LIMIT 1)
WHERE pa.Person_ID = %s
ORDER BY r.Edition_Year DESC, ra.Race_No"""


def person(person_id):
    found = db.query(PERSON_SQL, (person_id,))
    if not found:
        return None, [], (PERSON_SQL, HISTORY_SQL)
    return found[0], db.query(HISTORY_SQL, (person_id,)), (PERSON_SQL, HISTORY_SQL)
