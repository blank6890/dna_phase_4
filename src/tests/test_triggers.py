"""Task 4: business-rule triggers (SIGNAL SQLSTATE '45000' -> PyMySQL error 1644)."""
import pymysql
import pytest

from conftest import load_scripts, q, scalar


def run(conn, sql, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.lastrowid


def rejected(conn, sql, params, text):
    with pytest.raises(pymysql.err.OperationalError) as e:
        run(conn, sql, params)
    assert e.value.args[0] == 1644, e.value
    assert text in e.value.args[1], e.value.args[1]


def reg_id(conn, year, bib):
    return scalar(conn, "SELECT Registration_ID FROM REGISTRATION WHERE Edition_Year=%s AND Bib_No=%s", (year, bib))


def entry_of(conn, year, bib):
    return scalar(conn, "SELECT Entry_ID FROM REGISTRATION WHERE Edition_Year=%s AND Bib_No=%s", (year, bib))


def race_no(conn, year, series):
    return scalar(conn, "SELECT Race_No FROM RACE WHERE Edition_Year=%s AND Series_Code=%s", (year, series))


def new_pair(conn, carrier_dob, carried_dob="1995-05-05"):
    a = run(conn, "INSERT INTO PERSON (First_Name, Last_Name, Date_of_Birth) VALUES ('Test','Carrier',%s)", (carrier_dob,))
    b = run(conn, "INSERT INTO PERSON (First_Name, Last_Name, Date_of_Birth) VALUES ('Test','Carried',%s)", (carried_dob,))
    e = run(conn, "INSERT INTO ENTRY (Entry_Type) VALUES ('Pair')")
    run(conn, "INSERT INTO PARTICIPATES_AS VALUES (%s,'CARRIER_1',%s,NULL),(%s,'CARRIED',%s,55)", (e, a, e, b))
    return e


REG_SQL = ("INSERT INTO REGISTRATION (Bib_No, Registered_At, Payment_Status, Fee_Paid_EUR, Entry_ID, "
           "Edition_Year, Race_No) VALUES (%s, %s, 'Paid', %s, %s, %s, %s)")


def test_populate_loads_with_triggers(fresh_db):
    assert scalar(fresh_db, "SELECT COUNT(*) FROM information_schema.TRIGGERS "
                            "WHERE TRIGGER_SCHEMA='eukonkanto_test'") >= 9
    load_scripts()   # must not raise


def test_registration_after_deadline(fresh_db):
    e = new_pair(fresh_db, "1990-01-01")
    rejected(fresh_db, REG_SQL, (999, "2026-11-13", 55, e, 2026, race_no(fresh_db, 2026, "MAIN")),
             "registration is closed")


def test_underage_carrier(fresh_db):
    e = new_pair(fresh_db, "2010-01-01")
    rejected(fresh_db, REG_SQL, (998, "2026-11-13", 55, e, 2027, race_no(fresh_db, 2027, "MAIN")),
             "Carrier must be at least 18")


def test_underage_carried(fresh_db):
    e = new_pair(fresh_db, "1990-01-01", carried_dob="2011-01-01")
    rejected(fresh_db, REG_SQL, (998, "2026-11-13", 55, e, 2027, race_no(fresh_db, 2027, "MAIN")),
             "Carried person must be at least 17")


def test_m40_carrier_too_young(fresh_db):
    e = new_pair(fresh_db, "1995-01-01")
    rejected(fresh_db, REG_SQL, (997, "2026-11-13", 55, e, 2027, race_no(fresh_db, 2027, "M40")),
             "Carrier must be at least 40")


def test_pair_in_team_series(fresh_db):
    e = new_pair(fresh_db, "1990-01-01")
    rejected(fresh_db, REG_SQL, (996, "2026-11-13", 160, e, 2027, race_no(fresh_db, 2027, "TEAM")),
             "requires 3 carriers")


def test_fee_must_match_race(fresh_db):
    e = new_pair(fresh_db, "1990-01-01")
    rejected(fresh_db, REG_SQL, (995, "2026-11-13", 20, e, 2027, race_no(fresh_db, 2027, "MAIN")),
             "must equal the race entry fee")


def test_valid_registration_accepted(fresh_db):
    e = new_pair(fresh_db, "1990-01-01")
    run(fresh_db, REG_SQL, (994, "2026-11-13", 55, e, 2027, race_no(fresh_db, 2027, "MAIN")))


def test_cancel_after_results(fresh_db):
    rejected(fresh_db, "UPDATE REGISTRATION SET Cancelled_At=NOW(), Bib_No=NULL WHERE Registration_ID=%s",
             (reg_id(fresh_db, 2026, 62),), "already has results")


def test_cancel_releases_bib(fresh_db):
    rid = reg_id(fresh_db, 2027, 20)
    run(fresh_db, "UPDATE REGISTRATION SET Cancelled_At=NOW(), Payment_Status='Refunded' WHERE Registration_ID=%s", (rid,))
    assert scalar(fresh_db, "SELECT Bib_No FROM REGISTRATION WHERE Registration_ID=%s", (rid,)) is None


def test_heat_in_non_heat_series(fresh_db):
    rejected(fresh_db, "INSERT INTO RESULT VALUES (%s,'Heat 1',60,'Finished',NULL)",
             (reg_id(fresh_db, 2026, 62),), "has no heats")


def test_single_in_heat_series(fresh_db):
    rejected(fresh_db, "INSERT INTO RESULT VALUES (%s,'Single',60,'Finished',NULL)",
             (reg_id(fresh_db, 2026, 78),), "heats and a final")


def test_result_for_cancelled(fresh_db):
    rid = reg_id(fresh_db, 2027, 20)
    run(fresh_db, "UPDATE REGISTRATION SET Cancelled_At=NOW(), Bib_No=NULL, Payment_Status='Refunded' "
                  "WHERE Registration_ID=%s", (rid,))
    rejected(fresh_db, "INSERT INTO RESULT VALUES (%s,'Single',70,'Finished',NULL)", (rid,), "is cancelled")


PROTEST_SQL = ("INSERT INTO PROTEST (Filed_At, Reason, Entry_ID, Edition_Year, Race_No) "
               "SELECT Last_Finish_At + INTERVAL %s MINUTE, 'test', %s, Edition_Year, Race_No "
               "FROM RACE WHERE Edition_Year=2026 AND Series_Code=%s")


def test_protest_outside_window(fresh_db):
    rejected(fresh_db, PROTEST_SQL, (16, entry_of(fresh_db, 2026, 22), "MAIN"), "within 15 minutes")


def test_protest_inside_window_accepted(fresh_db):
    run(fresh_db, PROTEST_SQL, (14, entry_of(fresh_db, 2026, 22), "MAIN"))


def test_protest_entry_not_in_race(fresh_db):
    rejected(fresh_db, PROTEST_SQL, (5, entry_of(fresh_db, 2026, 1), "MAIN"), "not registered in this race")


def test_award_not_offered(fresh_db):
    rejected(fresh_db, "INSERT INTO AWARDED VALUES (6, %s, '2026-07-04')", (reg_id(fresh_db, 2026, 78),),
             "does not offer this prize")


def test_award_wrong_rank(fresh_db):
    rejected(fresh_db, "INSERT INTO AWARDED VALUES (3, %s, '2026-07-04')", (reg_id(fresh_db, 2026, 62),),
             "does not match rank")


def test_replace_member_after_results(fresh_db):
    other = scalar(fresh_db, "SELECT Person_ID FROM PERSON WHERE First_Name='Emilia' AND Last_Name='Nurmi'")
    rejected(fresh_db, "UPDATE PARTICIPATES_AS SET Person_ID=%s WHERE Entry_ID=%s AND Role_Code='CARRIED'",
             (other, entry_of(fresh_db, 2026, 62)), "already has results")


def test_pair_cannot_have_second_carrier(fresh_db):
    e = new_pair(fresh_db, "1990-01-01")
    p = run(fresh_db, "INSERT INTO PERSON (First_Name, Last_Name) VALUES ('X','Y')")
    rejected(fresh_db, "INSERT INTO PARTICIPATES_AS VALUES (%s,'CARRIER_2',%s,NULL)", (e, p), "Only team entries")


def test_booth_fee_standard(fresh_db):
    rejected(fresh_db, "INSERT INTO EXHIBITS_AT VALUES (2, 2025, '4x4', 90, FALSE, TRUE)", None, "70 EUR")


def test_food_booth_by_contract_accepted(fresh_db):
    run(fresh_db, "INSERT INTO EXHIBITS_AT VALUES (4, 2025, '4x4', 95, TRUE, TRUE)")
