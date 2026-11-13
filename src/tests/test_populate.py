"""Task 3: population data."""
from conftest import SRC, q, scalar


def test_core_counts(db_conn):
    assert scalar(db_conn, "SELECT COUNT(*) FROM EDITION") == 34          # 1992-2027 minus 2020, 2021
    assert scalar(db_conn, "SELECT COUNT(*) FROM REGISTRATION JOIN RACE USING (Edition_Year, Race_No) "
                           "WHERE Edition_Year=2026 AND Series_Code='MAIN'") == 45


def test_one_person_row_for_andrew_lee(db_conn):
    assert scalar(db_conn, "SELECT COUNT(*) FROM PERSON WHERE First_Name='Andrew' AND Last_Name='Lee'") == 1


def test_unicode_roundtrip(db_conn):
    assert scalar(db_conn, "SELECT Last_Name FROM PERSON WHERE First_Name='Timo' AND Last_Name LIKE 'F%hr'") == "Föhr"
    assert scalar(db_conn, "SELECT COUNT(*) FROM PERSON WHERE Last_Name='O’Callaghan'") == 1


def test_generated_rows_marked():
    assert "-- GENERATED:" in (SRC / "populate.sql").read_text(encoding="utf8")


def test_every_person_has_citizenship(db_conn):
    assert scalar(db_conn, "SELECT COUNT(*) FROM PERSON p WHERE NOT EXISTS "
                           "(SELECT 1 FROM PERSON_CITIZENSHIP c WHERE c.Person_ID = p.Person_ID)") == 0


def test_unmatched_rows_exist(db_conn):
    # an entry never registered, a vendor with no booking, a race with no registrations
    assert scalar(db_conn, "SELECT COUNT(*) FROM ENTRY e WHERE NOT EXISTS "
                           "(SELECT 1 FROM REGISTRATION r WHERE r.Entry_ID = e.Entry_ID)") >= 1
    assert scalar(db_conn, "SELECT COUNT(*) FROM VENDOR v WHERE NOT EXISTS "
                           "(SELECT 1 FROM EXHIBITS_AT x WHERE x.Vendor_ID = v.Vendor_ID)") >= 1
    assert scalar(db_conn, "SELECT COUNT(*) FROM RACE ra WHERE NOT EXISTS (SELECT 1 FROM REGISTRATION r "
                           "WHERE r.Edition_Year = ra.Edition_Year AND r.Race_No = ra.Race_No)") >= 1
