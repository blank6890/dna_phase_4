"""Task 3: derived-value views."""
from conftest import q, scalar


def test_sprint_final_2026_order(db_conn):  # S3 source
    rows = q(db_conn, "SELECT Bib_No, Net_Time_s, Rank_In_Stage FROM v_result WHERE Edition_Year=2026 "
                      "AND Series_Code='SPR' AND Stage='Final' ORDER BY Rank_In_Stage")
    assert [(r["Bib_No"], float(r["Net_Time_s"])) for r in rows] == [(78, 33.77), (70, 34.38), (76, 35.61), (80, 42.37)]
    assert [r["Rank_In_Stage"] for r in rows] == [1, 2, 3, 4]


def test_team_penalty_in_net_time(db_conn):   # raw 139.9 + 15 = 154.9 (site shows 2:34.9)
    row = q(db_conn, "SELECT Net_Time_s, Penalty_s, Rank_In_Stage FROM v_result WHERE Edition_Year=2026 AND Bib_No=105")[0]
    assert float(row["Net_Time_s"]) == 154.9 and float(row["Penalty_s"]) == 15 and row["Rank_In_Stage"] == 3


def test_gap_to_leader(db_conn):
    assert float(scalar(db_conn, "SELECT Gap_To_Leader_s FROM v_result WHERE Edition_Year=2026 AND Bib_No=106")) == 17.9


def test_ties_share_rank(db_conn):
    rows = q(db_conn, "SELECT Rank_In_Stage, Gap_To_Leader_s FROM v_result WHERE Edition_Year=2026 AND Bib_No IN (41,34,40)")
    assert {r["Rank_In_Stage"] for r in rows} == {17}
    assert len({r["Gap_To_Leader_s"] for r in rows}) == 1


def test_dns_has_no_rank(db_conn):
    row = q(db_conn, "SELECT Rank_In_Stage, Net_Time_s FROM v_result WHERE Edition_Year=2026 AND Bib_No=33")[0]
    assert row["Rank_In_Stage"] is None and row["Net_Time_s"] is None


def test_display_name_pair(db_conn):
    assert scalar(db_conn, "SELECT Display_Name FROM v_entry_name e JOIN REGISTRATION r USING (Entry_ID) "
                           "WHERE r.Edition_Year=2026 AND r.Bib_No=62") == "Taisto Miettinen / Katja Kovanen"


def test_display_name_team_and_countries(db_conn):
    row = q(db_conn, "SELECT Display_Name, Countries FROM v_entry_name e JOIN REGISTRATION r USING (Entry_ID) "
                     "WHERE r.Edition_Year=2026 AND r.Bib_No=104")[0]
    assert row["Display_Name"] == "Andrew Lee, Joshua Crafter, Vytautas Kirkliauskas / Devon Lee"
    assert row["Countries"] == "LTU/USA"


def test_single_name_display(db_conn):
    assert scalar(db_conn, "SELECT Display_Name FROM v_entry_name e JOIN REGISTRATION r USING (Entry_ID) "
                           "WHERE r.Edition_Year=2026 AND r.Bib_No=20") == "Francois / Mathilde"


def test_refund_rule(fresh_db):
    reg = q(fresh_db, "SELECT Registration_ID FROM REGISTRATION WHERE Edition_Year=2027 AND Bib_No=20")[0]["Registration_ID"]
    with fresh_db.cursor() as cur:
        cur.execute("UPDATE REGISTRATION SET Cancelled_At=NOW(), Bib_No=NULL, Payment_Status='Refunded' "
                    "WHERE Registration_ID=%s", (reg,))
    row = q(fresh_db, "SELECT Status, Refund_EUR FROM v_registration WHERE Registration_ID=%s", (reg,))[0]
    assert row["Status"] == "Cancelled" and float(row["Refund_EUR"]) == 45.0


def test_backpack_required(db_conn):
    assert float(scalar(db_conn, "SELECT Required_Backpack_kg FROM v_registration WHERE Edition_Year=2026 AND Bib_No=70")) == 3.0
