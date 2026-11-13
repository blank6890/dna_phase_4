"""Task 8 (and 10): registration create / cancel / replace / delete, booth removal."""
from conftest import q, scalar


def new_person(first, last, dob, email=None, citizenship="FIN"):
    return {"first_name": first, "last_name": last, "dob": dob, "gender": "Other",
            "email": email, "citizenship": citizenship}


def pair_payload(series="MAIN", carrier_dob="1990-03-03", email="test.carried@mail.example"):
    return {"year": 2027, "series": series, "entry_type": "Pair", "countries": ["FIN"],
            "members": [{"role": "CARRIER_1", "new": new_person("Testi", "Kantaja", carrier_dob)},
                        {"role": "CARRIED", "new": new_person("Testi", "Kannettava", "1996-06-06", email),
                         "weight_kg": 52.5}]}


def register(c, payload):
    return c.post("/api/registrations", json=payload)


def reg_id(conn, year, bib):
    return scalar(conn, "SELECT Registration_ID FROM REGISTRATION WHERE Edition_Year=%s AND Bib_No=%s", (year, bib))


def test_i1_register_new_pair_2027(wclient, fresh_db):
    r = register(wclient, pair_payload())
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["ok"] and body["fee"] == 55.0 and body["bib_no"] > 0 and "INSERT INTO REGISTRATION" in body["sql"]
    row = q(fresh_db, "SELECT Fee_Paid_EUR, Bib_No FROM REGISTRATION WHERE Registration_ID=%s",
            (body["registration_id"],))[0]
    assert float(row["Fee_Paid_EUR"]) == 55.0 and row["Bib_No"] == body["bib_no"]


def test_i1_existing_people_reuse_entry(wclient, fresh_db):
    # Andrew Lee / Devon Lee already have a pair entry (2026); registering them for 2027 MAIN reuses it
    lee = scalar(fresh_db, "SELECT Person_ID FROM PERSON WHERE First_Name='Andrew' AND Last_Name='Lee'")
    devon = scalar(fresh_db, "SELECT Person_ID FROM PERSON WHERE First_Name='Devon' AND Last_Name='Lee'")
    entries_before = scalar(fresh_db, "SELECT COUNT(*) FROM ENTRY")
    r = register(wclient, {"year": 2027, "series": "MAIN", "entry_type": "Pair", "countries": ["USA"],
                           "members": [{"role": "CARRIER_1", "person_id": lee},
                                       {"role": "CARRIED", "person_id": devon, "weight_kg": 48}]})
    assert r.status_code == 200, r.get_json()
    assert scalar(fresh_db, "SELECT COUNT(*) FROM ENTRY") == entries_before


def test_i1_rollback_on_underage(wclient, fresh_db):
    before = scalar(fresh_db, "SELECT COUNT(*) FROM PERSON")
    r = register(wclient, pair_payload(carrier_dob="2012-01-01"))
    assert r.status_code == 409 and "at least 18" in r.get_json()["error"]
    assert scalar(fresh_db, "SELECT COUNT(*) FROM PERSON") == before


def test_i1_team_needs_four_members(wclient):
    payload = pair_payload(series="TEAM")
    payload.update(entry_type="Team", team_name="Testitiimi")
    r = register(wclient, payload)
    assert r.status_code == 409 and "requires 3 carriers" in r.get_json()["error"]


def test_i1_duplicate_email(wclient):
    assert register(wclient, pair_payload()).status_code == 200
    second = pair_payload()
    second["members"][0]["new"]["first_name"] = "Toinen"
    r = register(wclient, second)
    assert r.status_code == 409 and "e-mail" in r.get_json()["error"]


def test_i1_invalid_payload_400(wclient):
    payload = pair_payload()
    payload["members"][0]["weight_kg"] = 60          # weight only on the carried person
    assert register(wclient, payload).status_code == 400
    payload = pair_payload()
    payload["countries"] = ["Finland"]
    assert register(wclient, payload).status_code == 400
    assert wclient.post("/api/registrations", json=[1, 2]).status_code == 400


def test_registration_details(wclient, fresh_db):
    r = wclient.get(f"/api/registrations/{reg_id(fresh_db, 2027, 20)}")
    body = r.get_json()
    assert r.status_code == 200 and body["registration"]["Status"] == "Registered"
    assert {m["Role_Code"] for m in body["rows"]} == {"CARRIER_1", "CARRIED"}


def test_u2_cancel_refund(wclient, fresh_db):
    rid = reg_id(fresh_db, 2027, 20)
    r = wclient.post(f"/api/registrations/{rid}/cancel")
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["refund"] == 45.0
    assert scalar(fresh_db, "SELECT Bib_No FROM REGISTRATION WHERE Registration_ID=%s", (rid,)) is None
    again = wclient.post(f"/api/registrations/{rid}/cancel")
    assert again.status_code == 409 and "already cancelled" in again.get_json()["error"]


def test_u2_cancel_2026_refused(wclient, fresh_db):
    r = wclient.post(f"/api/registrations/{reg_id(fresh_db, 2026, 62)}/cancel")
    assert r.status_code == 409 and "already has results" in r.get_json()["error"]


def test_u2_cancel_missing_404(wclient):
    assert wclient.post("/api/registrations/999999/cancel").status_code == 404


def test_u4_replace_member_2027(wclient, fresh_db):
    entry = scalar(fresh_db, "SELECT Entry_ID FROM REGISTRATION WHERE Edition_Year=2027 AND Bib_No=20")
    r = wclient.patch(f"/api/entries/{entry}/roles/CARRIED",
                      json={"new": new_person("Uusi", "Kannettava", "1999-09-09"), "weight_kg": 58})
    assert r.status_code == 200, r.get_json()
    assert scalar(fresh_db, "SELECT p.First_Name FROM PARTICIPATES_AS pa JOIN PERSON p USING (Person_ID) "
                            "WHERE pa.Entry_ID=%s AND pa.Role_Code='CARRIED'", (entry,)) == "Uusi"


def test_u4_replace_member_2026_refused(wclient, fresh_db):
    entry = scalar(fresh_db, "SELECT Entry_ID FROM REGISTRATION WHERE Edition_Year=2026 AND Bib_No=62")
    other = scalar(fresh_db, "SELECT Person_ID FROM PERSON WHERE First_Name='Emilia' AND Last_Name='Nurmi'")
    r = wclient.patch(f"/api/entries/{entry}/roles/CARRIED", json={"person_id": other, "weight_kg": 55})
    assert r.status_code == 409 and "already has results" in r.get_json()["error"]


def test_d1_delete_2027(wclient, fresh_db):
    rid = reg_id(fresh_db, 2027, 20)
    r = wclient.delete(f"/api/registrations/{rid}")
    assert r.status_code == 200, r.get_json()
    assert wclient.get(f"/api/registrations/{rid}").status_code == 404


def test_d1_delete_2026_refused(wclient, fresh_db):
    r = wclient.delete(f"/api/registrations/{reg_id(fresh_db, 2026, 62)}")
    assert r.status_code == 409 and r.get_json()["error"] == "Registration has results"


def test_d2_unregistered_entry(wclient, fresh_db):
    listed = wclient.get("/api/entries/unregistered").get_json()["rows"]
    assert any(e["Display_Name"] == "Ville Korhonen / Emilia Nurmi" for e in listed)
    entry = next(e["Entry_ID"] for e in listed if e["Display_Name"] == "Ville Korhonen / Emilia Nurmi")
    assert wclient.delete(f"/api/entries/{entry}").status_code == 200
    busy = scalar(fresh_db, "SELECT Entry_ID FROM REGISTRATION WHERE Edition_Year=2026 AND Bib_No=62")
    r = wclient.delete(f"/api/entries/{busy}")
    assert r.status_code == 409 and "other records still refer" in r.get_json()["error"]
