"""Task 9: results, penalties, protests and prizes (I2, U1, I3, U3, I4)."""
from conftest import q, scalar
from test_api_writes import pair_payload, register


def official(c, title="Timekeeper"):
    return next(o["Person_ID"] for o in c.get("/api/officials").get_json()["rows"] if o["Duty_Title"] == title)


def reg_id(conn, year, bib):
    return scalar(conn, "SELECT Registration_ID FROM REGISTRATION WHERE Edition_Year=%s AND Bib_No=%s", (year, bib))


def rank(conn, year, bib, stage):
    return scalar(conn, "SELECT Rank_In_Stage FROM v_result WHERE Edition_Year=%s AND Bib_No=%s AND Stage=%s",
                  (year, bib, stage))


def winner_bib(conn, year, prize_id):
    return scalar(conn, "SELECT r.Bib_No FROM AWARDED a JOIN REGISTRATION r USING (Registration_ID) "
                        "WHERE a.Prize_ID=%s AND r.Edition_Year=%s", (prize_id, year))


def test_officials_list(client):
    data = client.get("/api/officials").get_json()["rows"]
    assert len(data) == 8 and any(o["Duty_Title"] == "Chief Judge" for o in data)


def test_i2_record_2027_result(wclient, fresh_db):
    rid = register(wclient, pair_payload()).get_json()["registration_id"]
    r = wclient.post("/api/results", json={"registration_id": rid, "stage": "Single", "status": "Finished",
                                           "raw_time_s": 75.3, "official_id": official(wclient)})
    assert r.status_code == 200, r.get_json()
    assert scalar(fresh_db, "SELECT Rank_In_Stage FROM v_result WHERE Registration_ID=%s", (rid,)) == 1


def test_i2_dns_with_time_rejected(wclient, fresh_db):
    rid = register(wclient, pair_payload()).get_json()["registration_id"]
    r = wclient.post("/api/results", json={"registration_id": rid, "stage": "Single", "status": "DNS",
                                           "raw_time_s": 70, "official_id": official(wclient)})
    assert r.status_code == 400


def test_i2_heat_in_main_refused(wclient, fresh_db):
    r = wclient.post("/api/results", json={"registration_id": reg_id(fresh_db, 2026, 62), "stage": "Heat 1",
                                           "status": "Finished", "raw_time_s": 60, "official_id": official(wclient)})
    assert r.status_code == 409 and "has no heats" in r.get_json()["error"]


def test_i2_duplicate_stage_refused(wclient, fresh_db):
    r = wclient.post("/api/results", json={"registration_id": reg_id(fresh_db, 2026, 62), "stage": "Single",
                                           "status": "Finished", "raw_time_s": 60, "official_id": official(wclient)})
    assert r.status_code == 409


def test_u1_correct_time_reranks_and_reawards(wclient, fresh_db):
    rid = reg_id(fresh_db, 2026, 49)
    r = wclient.patch(f"/api/results/{rid}/Single", json={"raw_time_s": 60.0})
    assert r.status_code == 200, r.get_json()
    assert rank(fresh_db, 2026, 49, "Single") == 1 and rank(fresh_db, 2026, 62, "Single") == 2
    assert winner_bib(fresh_db, 2026, 1) == 49
    matti = scalar(fresh_db, "SELECT Person_ID FROM STAFF_ACCOUNT WHERE Username='matti'")   # logged-in official
    assert scalar(fresh_db, "SELECT Recorded_By_Official_ID FROM RESULT WHERE Registration_ID=%s", (rid,)) == matti


def test_u1_penalty_changes_net(wclient, fresh_db):
    rid = reg_id(fresh_db, 2026, 78)
    r = wclient.post("/api/penalties", json={"registration_id": rid, "stage": "Final", "type": "Penalty",
                                             "seconds": 10, "reason": "Obstruction", "official_id": official(wclient)})
    assert r.status_code == 200, r.get_json()
    assert float(scalar(fresh_db, "SELECT Net_Time_s FROM v_result WHERE Registration_ID=%s AND Stage='Final'",
                        (rid,))) == 43.77
    assert rank(fresh_db, 2026, 70, "Final") == 1
    assert winner_bib(fresh_db, 2026, 2) == 70 or 70 in [
        r["Bib_No"] for r in q(fresh_db, "SELECT r.Bib_No FROM AWARDED a JOIN REGISTRATION r USING (Registration_ID) "
                                         "WHERE a.Prize_ID=2 AND r.Edition_Year=2026")]


def _protest(c, conn, minutes):
    race = scalar(conn, "SELECT Race_No FROM RACE WHERE Edition_Year=2026 AND Series_Code='MAIN'")
    last = scalar(conn, "SELECT DATE_FORMAT(Last_Finish_At + INTERVAL %s MINUTE, '%%Y-%%m-%%d %%H:%%i:%%s') "
                        "FROM RACE WHERE Edition_Year=2026 AND Race_No=%s", (minutes, race))
    entry = scalar(conn, "SELECT Entry_ID FROM REGISTRATION WHERE Edition_Year=2026 AND Bib_No=22")
    return c.post("/api/protests", json={"entry_id": entry, "year": 2026, "race_no": race,
                                         "reason": "Obstruction at the water obstacle", "filed_at": last})


def test_i3_protest_in_window(wclient, fresh_db):
    assert _protest(wclient, fresh_db, 5).status_code == 200
    late = _protest(wclient, fresh_db, 20)
    assert late.status_code == 409 and "within 15 minutes" in late.get_json()["error"]


def _jury(c):
    return [o["Person_ID"] for o in c.get("/api/officials").get_json()["rows"] if o["Duty_Title"] in
            ("Chief Judge", "Jury Member")]


def test_u3_uphold_removes_penalty(wclient, fresh_db):
    pid = scalar(fresh_db, "SELECT Protest_ID FROM PROTEST p JOIN RACE r USING (Edition_Year, Race_No) "
                           "WHERE p.Outcome='Pending' AND r.Series_Code='TEAM'")
    team_reg = reg_id(fresh_db, 2026, 105)
    r = wclient.post(f"/api/protests/{pid}/decide", json={
        "outcome": "Upheld", "votes": [{"official_id": o, "vote": "Uphold"} for o in _jury(wclient)],
        "action": {"remove_penalty": [team_reg, "Single", 1]}})
    assert r.status_code == 200, r.get_json()
    assert float(scalar(fresh_db, "SELECT Net_Time_s FROM v_result WHERE Registration_ID=%s", (team_reg,))) == 139.9
    row = q(fresh_db, "SELECT Outcome, Decided_At FROM PROTEST WHERE Protest_ID=%s", (pid,))[0]
    assert row["Outcome"] == "Upheld" and row["Decided_At"] is not None
    assert scalar(fresh_db, "SELECT COUNT(*) FROM DECIDES WHERE Protest_ID=%s", (pid,)) == 3
    again = wclient.post(f"/api/protests/{pid}/decide", json={"outcome": "Rejected", "votes": []})
    assert again.status_code == 409


def test_u3_disqualify_reranks(wclient, fresh_db):
    pid = scalar(fresh_db, "SELECT Protest_ID FROM PROTEST p JOIN RACE r USING (Edition_Year, Race_No) "
                           "WHERE p.Outcome='Pending' AND r.Series_Code='MAIN'")
    r = wclient.post(f"/api/protests/{pid}/decide", json={
        "outcome": "Upheld", "votes": [{"official_id": o, "vote": "Uphold"} for o in _jury(wclient)],
        "action": {"disqualify": [reg_id(fresh_db, 2026, 62), "Single"]}})
    assert r.status_code == 200, r.get_json()
    assert rank(fresh_db, 2026, 49, "Single") == 1 and winner_bib(fresh_db, 2026, 1) == 49


def test_u3_reject(wclient, fresh_db):
    pid = scalar(fresh_db, "SELECT Protest_ID FROM PROTEST p JOIN RACE r USING (Edition_Year, Race_No) "
                           "WHERE p.Outcome='Pending' AND r.Series_Code='MAIN'")
    before = q(fresh_db, "SELECT Registration_ID, Net_Time_s FROM v_result WHERE Edition_Year=2026 ORDER BY 1, 2")
    r = wclient.post(f"/api/protests/{pid}/decide", json={
        "outcome": "Rejected", "votes": [{"official_id": o, "vote": "Reject"} for o in _jury(wclient)]})
    assert r.status_code == 200
    assert scalar(fresh_db, "SELECT Outcome FROM PROTEST WHERE Protest_ID=%s", (pid,)) == "Rejected"
    assert q(fresh_db, "SELECT Registration_ID, Net_Time_s FROM v_result WHERE Edition_Year=2026 ORDER BY 1, 2") == before


def test_i4_award_not_offered(wclient, fresh_db):
    r = wclient.post("/api/awards", json={"prize_id": 6, "registration_id": reg_id(fresh_db, 2026, 78)})
    assert r.status_code == 409 and "does not offer" in r.get_json()["error"]


def test_i4_award_special(wclient, fresh_db):
    r = wclient.post("/api/awards", json={"prize_id": 6, "registration_id": reg_id(fresh_db, 2026, 62)})
    assert r.status_code == 200, r.get_json()


def test_prizes_for_series(client):
    names = [p["Prize_Name"] for p in client.get("/api/prizes?series=SPR").get_json()["rows"]]
    assert "Best costume" not in names and "Second place product prize" in names
