"""Task 2: tables, keys and single-row CHECK constraints."""
import pymysql
import pytest

TABLES = {
    "COUNTRY", "PERSON", "PERSON_PHONE", "PERSON_CITIZENSHIP", "COMPETITOR", "OFFICIAL", "STAFF_ACCOUNT",
    "EDITION", "VENUE", "VENUE_FACILITY", "SERIES", "RACE", "ROLE", "ENTRY",
    "PARTICIPATES_AS", "REPRESENTS", "REGISTRATION", "RESULT", "PENALTY", "PROTEST",
    "DECIDES", "OFFICIATES_IN", "GRAND_PRIX_EVENT", "PRIZE", "AWARDED", "OFFERS",
    "SPONSOR", "SPONSORS", "VENDOR", "VENDOR_PRODUCT_CATEGORY", "EXHIBITS_AT",
}


def run(conn, sql, params=()):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.lastrowid


def seed(conn):
    """Minimal parent rows: one edition, series, venue, race and two pair entries.
    Uses explicit IDs so it works whether or not populate.sql has loaded data."""
    run(conn, "INSERT INTO EDITION VALUES (2090,'World','2090-07-01','2090-07-02',"
              "'2089-11-01','2090-06-28 22:00:00')")
    run(conn, "INSERT INTO SERIES VALUES ('ZZ','Test series',253.5,1,2,18,17,49,1,FALSE)")
    run(conn, "INSERT INTO VENUE (Venue_ID,Venue_Name,Street,Postal_Code,City) "
              "VALUES (9001,'Arena','Urheilutie 1','74300','Sonkajärvi')")
    run(conn, "INSERT INTO RACE (Edition_Year,Race_No,Scheduled_Start,Entry_Fee_EUR,Series_Code,Venue_ID) "
              "VALUES (2090,1,'2090-07-02 15:00:00',55,'ZZ',9001)")
    run(conn, "INSERT INTO ENTRY (Entry_ID,Entry_Type) VALUES (9001,'Pair'),(9002,'Pair')")
    run(conn, "INSERT IGNORE INTO ROLE VALUES ('CARRIER_1','Carrier (leg 1)',1),('CARRIED','Carried person',NULL)")
    run(conn, "INSERT INTO PERSON (Person_ID,First_Name,Last_Name) VALUES "
              "(9001,'Seed','A'),(9002,'Seed','B'),(9003,'Seed','C'),(9004,'Seed','D')")
    run(conn, "INSERT INTO PARTICIPATES_AS VALUES (9001,'CARRIER_1',9001,NULL),(9001,'CARRIED',9002,55),"
              "(9002,'CARRIER_1',9003,NULL),(9002,'CARRIED',9004,55)")


def code_of(excinfo):
    return excinfo.value.args[0]


def test_all_tables_exist(fresh_db):
    with fresh_db.cursor() as cur:
        cur.execute("SELECT TABLE_NAME FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA='eukonkanto_test' AND TABLE_TYPE='BASE TABLE'")
        assert {r["TABLE_NAME"] for r in cur.fetchall()} == TABLES


def test_iso_code_check(fresh_db):
    with pytest.raises(pymysql.err.OperationalError) as e:
        run(fresh_db, "INSERT INTO COUNTRY VALUES ('fi','Finland2','Europe')")
    assert code_of(e) == 4025


def test_series_age_check(fresh_db):
    with pytest.raises(pymysql.err.OperationalError) as e:
        run(fresh_db, "INSERT INTO SERIES VALUES ('YY','Bad',253.5,1,2,17,17,49,1,FALSE)")
    assert code_of(e) == 4025


def test_result_time_status_check(fresh_db):
    seed(fresh_db)
    rid = run(fresh_db, "INSERT INTO REGISTRATION (Bib_No,Registered_At,Payment_Status,Fee_Paid_EUR,"
                        "Entry_ID,Edition_Year,Race_No) VALUES (1,'2090-01-01','Paid',55,9001,2090,1)")
    with pytest.raises(pymysql.err.OperationalError) as e:
        run(fresh_db, "INSERT INTO RESULT (Registration_ID,Stage,Raw_Time_s,Status) "
                      "VALUES (%s,'Single',60,'DNS')", (rid,))
    assert code_of(e) == 4025


def test_weight_only_on_carried(fresh_db):
    seed(fresh_db)
    eid = run(fresh_db, "INSERT INTO ENTRY (Entry_Type) VALUES ('Pair')")
    pid = run(fresh_db, "INSERT INTO PERSON (First_Name,Last_Name) VALUES ('A','B')")
    with pytest.raises(pymysql.err.OperationalError) as e:
        run(fresh_db, "INSERT INTO PARTICIPATES_AS VALUES (%s,'CARRIER_1',%s,50)", (eid, pid))
    assert code_of(e) == 4025


def test_bib_unique_per_edition(fresh_db):
    seed(fresh_db)
    ins = ("INSERT INTO REGISTRATION (Bib_No,Registered_At,Payment_Status,Fee_Paid_EUR,"
           "Entry_ID,Edition_Year,Race_No) VALUES (7,'2090-01-01','Paid',55,%s,2090,1)")
    run(fresh_db, ins, (9001,))
    with pytest.raises(pymysql.err.IntegrityError) as e:
        run(fresh_db, ins, (9002,))
    assert code_of(e) == 1062 and "uq_reg_bib" in str(e.value)


def test_cancel_requires_null_bib(fresh_db):
    seed(fresh_db)
    with pytest.raises(pymysql.err.OperationalError) as e:
        run(fresh_db, "INSERT INTO REGISTRATION (Bib_No,Registered_At,Cancelled_At,Payment_Status,"
                      "Fee_Paid_EUR,Entry_ID,Edition_Year,Race_No) "
                      "VALUES (3,'2090-01-01','2090-02-01','Refunded',55,9001,2090,1)")
    assert code_of(e) == 4025


def test_race_series_unique(fresh_db):
    seed(fresh_db)
    with pytest.raises(pymysql.err.IntegrityError) as e:
        run(fresh_db, "INSERT INTO RACE (Edition_Year,Race_No,Scheduled_Start,Entry_Fee_EUR,Series_Code,Venue_ID) "
                      "VALUES (2090,2,'2090-07-02 16:00:00',55,'ZZ',9001)")
    assert code_of(e) == 1062


def test_fk_restrict_series(fresh_db):
    seed(fresh_db)
    with pytest.raises(pymysql.err.IntegrityError) as e:
        run(fresh_db, "DELETE FROM SERIES WHERE Series_Code='ZZ'")
    assert code_of(e) == 1451
