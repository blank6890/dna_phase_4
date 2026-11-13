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


def test_one_staff_account_per_official(db_conn):
    assert scalar(db_conn, "SELECT COUNT(*) FROM STAFF_ACCOUNT") == 8
    assert scalar(db_conn, "SELECT COUNT(*) FROM OFFICIAL o LEFT JOIN STAFF_ACCOUNT s USING (Person_ID) "
                           "WHERE s.Person_ID IS NULL") == 0


def test_staff_passwords_hashed(db_conn):
    from werkzeug.security import check_password_hash
    rows = q(db_conn, "SELECT Username, Password_Hash FROM STAFF_ACCOUNT ORDER BY Person_ID")
    assert [r["Username"] for r in rows] == ["matti", "riitta", "juha", "anne", "pekka", "jari", "sari", "minna"]
    assert all(check_password_hash(r["Password_Hash"], "staff2027") for r in rows)
    assert not any("staff2027" in r["Password_Hash"] for r in rows)
