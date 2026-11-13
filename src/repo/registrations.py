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
