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
       (SELECT GROUP_CONCAT(CONCAT(pe.Adjustment_Type, ' ', pe.Seconds, ' s: ', pe.Reason)
                            ORDER BY pe.Penalty_No SEPARATOR '; ')
          FROM PENALTY pe
         WHERE pe.Registration_ID = v.Registration_ID AND pe.Stage = v.Stage) AS Adjustments
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
