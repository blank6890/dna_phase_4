def test_test_db_exists(db_conn):
    with db_conn.cursor() as cur:
        cur.execute("SELECT DATABASE() AS db")
        assert cur.fetchone()["db"] == "eukonkanto_test"
