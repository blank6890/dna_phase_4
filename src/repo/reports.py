"""Committee reports: aggregates A2-A4 and analysis reports AR1-AR6."""
import db

AVG_TIMES_SQL = """
SELECT v.Edition_Year, v.Series_Code, s.Series_Name,
       ROUND(AVG(v.Net_Time_s), 2) AS Avg_Net_Time_s, COUNT(*) AS Finishers
FROM v_result v
JOIN SERIES s ON s.Series_Code = v.Series_Code
WHERE v.Status = 'Finished' AND v.Stage = IF(s.Has_Heats, 'Final', 'Single')
GROUP BY v.Edition_Year, v.Series_Code, s.Series_Name
ORDER BY v.Edition_Year DESC, FIELD(v.Series_Code, 'MAIN', 'WOMEN', 'M40', 'TEAM', 'SPR')"""

FEES_SQL = """
SELECT r.Edition_Year, SUM(r.Fee_Paid_EUR) AS Total_Fees_EUR, COUNT(*) AS Registrations
FROM REGISTRATION r
WHERE r.Payment_Status IN ('Paid', 'Refunded')
GROUP BY r.Edition_Year
ORDER BY r.Edition_Year DESC"""

BY_COUNTRY_SQL = """
SELECT c.ISO_Code, c.Country_Name, COUNT(*) AS Registrations
FROM REGISTRATION r
JOIN REPRESENTS rp ON rp.Entry_ID = r.Entry_ID
JOIN COUNTRY c     ON c.ISO_Code = rp.ISO_Code
WHERE r.Edition_Year = %s AND r.Cancelled_At IS NULL
GROUP BY c.ISO_Code, c.Country_Name
ORDER BY Registrations DESC, c.Country_Name"""

MEDALS_SQL = """
SELECT c.ISO_Code, c.Country_Name,
       SUM(v.Rank_In_Stage = 1) AS Gold,
       SUM(v.Rank_In_Stage = 2) AS Silver,
       SUM(v.Rank_In_Stage = 3) AS Bronze
FROM v_result v
JOIN REPRESENTS rp ON rp.Entry_ID = v.Entry_ID
JOIN COUNTRY c     ON c.ISO_Code = rp.ISO_Code
WHERE v.Series_Code = 'MAIN' AND v.Stage = 'Single' AND v.Rank_In_Stage <= 3
GROUP BY c.ISO_Code, c.Country_Name
ORDER BY Gold DESC, Silver DESC, Bronze DESC, c.Country_Name"""

BACKPACKS_SQL = """
SELECT r.Edition_Year, r.Series_Code, r.Bib_No, p.First_Name, p.Last_Name,
       r.Carried_Weight_kg, r.Required_Backpack_kg, n.Display_Name
FROM v_registration r
JOIN PARTICIPATES_AS pa ON pa.Entry_ID = r.Entry_ID AND pa.Role_Code = 'CARRIED'
JOIN PERSON p           ON p.Person_ID = pa.Person_ID
JOIN v_entry_name n     ON n.Entry_ID = r.Entry_ID
WHERE r.Status = 'Registered' AND r.Required_Backpack_kg > 0
ORDER BY r.Edition_Year DESC, r.Series_Code, r.Bib_No"""

MULTI_SERIES_SQL = """
WITH ps AS (
    SELECT pa.Person_ID, pa.Role_Code, r.Registration_ID, ra.Series_Code, s.Has_Heats
    FROM PARTICIPATES_AS pa
    JOIN REGISTRATION r ON r.Entry_ID = pa.Entry_ID
    JOIN RACE ra        ON ra.Edition_Year = r.Edition_Year AND ra.Race_No = r.Race_No
    JOIN SERIES s       ON s.Series_Code = ra.Series_Code
    WHERE r.Edition_Year = %s AND r.Cancelled_At IS NULL
), multi AS (
    SELECT Person_ID FROM ps GROUP BY Person_ID HAVING COUNT(DISTINCT Series_Code) > 1
)
SELECT p.Person_ID, p.First_Name, p.Last_Name, ps.Series_Code, ro.Role_Name,
       v.Stage, v.Status, v.Net_Time_s, v.Rank_In_Stage
FROM ps
JOIN multi     ON multi.Person_ID = ps.Person_ID
JOIN PERSON p  ON p.Person_ID = ps.Person_ID
JOIN ROLE ro   ON ro.Role_Code = ps.Role_Code
LEFT JOIN v_result v
       ON v.Registration_ID = ps.Registration_ID
      AND v.Stage = (SELECT x.Stage FROM RESULT x WHERE x.Registration_ID = ps.Registration_ID
                     ORDER BY FIELD(x.Stage, 'Final', 'Single', 'Heat 3', 'Heat 2', 'Heat 1') LIMIT 1)
ORDER BY p.Last_Name, p.First_Name, FIELD(ps.Series_Code, 'MAIN', 'WOMEN', 'M40', 'TEAM', 'SPR')"""

INCOME_SQL = """
SELECT e.Edition_Year,
       COALESCE((SELECT SUM(r.Fee_Paid_EUR - r.Refund_EUR) FROM v_registration r
                  WHERE r.Edition_Year = e.Edition_Year), 0)        AS Registration_Fees_Net_EUR,
       150 * (SELECT COUNT(*) FROM PROTEST pr
               WHERE pr.Edition_Year = e.Edition_Year)              AS Protest_Fees_EUR,
       COALESCE((SELECT SUM(x.Booth_Fee_EUR) FROM EXHIBITS_AT x
                  WHERE x.Edition_Year = e.Edition_Year AND x.Paid), 0) AS Booth_Fees_EUR
FROM EDITION e
ORDER BY e.Edition_Year DESC"""

PROTEST_OUTCOMES_SQL = """
SELECT pr.Edition_Year, pr.Race_No, ra.Series_Code, s.Series_Name,
       COUNT(DISTINCT pr.Protest_ID) AS Filed,
       COUNT(DISTINCT CASE WHEN pr.Outcome = 'Upheld' THEN pr.Protest_ID END) AS Upheld,
       COUNT(DISTINCT CASE WHEN pr.Outcome = 'Pending' THEN pr.Protest_ID END) AS Pending,
       GROUP_CONCAT(DISTINCT CONCAT(p.First_Name, ' ', p.Last_Name)
                    ORDER BY p.Last_Name SEPARATOR ', ') AS Voters
FROM PROTEST pr
JOIN RACE ra        ON ra.Edition_Year = pr.Edition_Year AND ra.Race_No = pr.Race_No
JOIN SERIES s       ON s.Series_Code = ra.Series_Code
LEFT JOIN DECIDES d ON d.Protest_ID = pr.Protest_ID
LEFT JOIN PERSON p  ON p.Person_ID = d.Official_ID
GROUP BY pr.Edition_Year, pr.Race_No, ra.Series_Code, s.Series_Name
ORDER BY pr.Edition_Year DESC, pr.Race_No"""

ABOVE_AVERAGE_SQL = """
SELECT c.ISO_Code, c.Country_Name,
       ROUND(AVG(v.Net_Time_s), 2) AS Country_Avg_s,
       (SELECT ROUND(AVG(v2.Net_Time_s), 2) FROM v_result v2
         WHERE v2.Edition_Year = %s AND v2.Series_Code = 'MAIN'
           AND v2.Status = 'Finished')                    AS Edition_Avg_s,
       COUNT(*) AS Finishers
FROM v_result v
JOIN REPRESENTS rp ON rp.Entry_ID = v.Entry_ID
JOIN COUNTRY c     ON c.ISO_Code = rp.ISO_Code
WHERE v.Edition_Year = %s AND v.Series_Code = 'MAIN' AND v.Status = 'Finished'
GROUP BY c.ISO_Code, c.Country_Name
HAVING AVG(v.Net_Time_s) < (SELECT AVG(v3.Net_Time_s) FROM v_result v3
                             WHERE v3.Edition_Year = %s AND v3.Series_Code = 'MAIN'
                               AND v3.Status = 'Finished')
ORDER BY Country_Avg_s"""


def avg_times():
    return db.query(AVG_TIMES_SQL), AVG_TIMES_SQL


def fees():
    return db.query(FEES_SQL), FEES_SQL


def registrations_by_country(year):
    return db.query(BY_COUNTRY_SQL, (year,)), BY_COUNTRY_SQL


def medals():
    return db.query(MEDALS_SQL), MEDALS_SQL


def backpacks():
    return db.query(BACKPACKS_SQL), BACKPACKS_SQL


def multi_series(year):
    return db.query(MULTI_SERIES_SQL, (year,)), MULTI_SERIES_SQL


def income():
    return db.query(INCOME_SQL), INCOME_SQL


def protest_outcomes():
    return db.query(PROTEST_OUTCOMES_SQL), PROTEST_OUTCOMES_SQL


def above_average(year):
    return db.query(ABOVE_AVERAGE_SQL, (year, year, year)), ABOVE_AVERAGE_SQL
