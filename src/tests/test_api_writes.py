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


def _pids(conn, *names):
    return [scalar(conn, "SELECT Person_ID FROM PERSON WHERE CONCAT(First_Name,' ',Last_Name)=%s", (n,)) for n in names]


def test_i1_reuses_entry_without_results(wclient, fresh_db):
    # Shane Williams / Lauren Williams have a 2027 entry with no results: a third series reuses it
    shane, lauren = _pids(fresh_db, "Shane Williams", "Lauren Williams")
    entries_before = scalar(fresh_db, "SELECT COUNT(*) FROM ENTRY")
    r = register(wclient, {"year": 2027, "series": "WOMEN", "entry_type": "Pair", "countries": ["USA"],
                           "members": [{"role": "CARRIER_1", "person_id": shane},
                                       {"role": "CARRIED", "person_id": lauren, "weight_kg": 58}]})
    assert r.status_code == 200, r.get_json()
    assert scalar(fresh_db, "SELECT COUNT(*) FROM ENTRY") == entries_before


def test_i1_raced_entry_gets_fresh_entry_with_new_weight(wclient, fresh_db):
    # Taisto Miettinen / Katja Kovanen's entry has results (frozen); a new registration gets a new entry
    taisto, katja = _pids(fresh_db, "Taisto Miettinen", "Katja Kovanen")
    r = register(wclient, {"year": 2027, "series": "MAIN", "entry_type": "Pair", "countries": ["FIN"],
                           "members": [{"role": "CARRIER_1", "person_id": taisto},
                                       {"role": "CARRIED", "person_id": katja, "weight_kg": 61.5}]})
    assert r.status_code == 200, r.get_json()
    entry = r.get_json()["entry_id"]
    assert scalar(fresh_db, "SELECT COUNT(*) FROM RESULT x JOIN REGISTRATION g USING (Registration_ID) "
                            "WHERE g.Entry_ID=%s", (entry,)) == 0
    assert float(scalar(fresh_db, "SELECT Measured_Weight_kg FROM PARTICIPATES_AS WHERE Entry_ID=%s "
                                  "AND Role_Code='CARRIED'", (entry,))) == 61.5


def test_seeded_returning_pair_can_replace_member(wclient, fresh_db):
    # 2027 registrations of Andrew/Devon Lee (who raced in 2026) must not be locked by 2026 results
    rid = scalar(fresh_db, "SELECT Registration_ID FROM REGISTRATION WHERE Edition_Year=2027 AND Bib_No=9")
    details = wclient.get(f"/api/registrations/{rid}").get_json()
    assert details["registration"]["Has_Results"] == 0
    entry = details["registration"]["Entry_ID"]
    r = wclient.patch(f"/api/entries/{entry}/roles/CARRIED",
                      json={"new": new_person("Uusi", "Kannettava", "1990-01-01"), "weight_kg": 55})
    assert r.status_code == 200, r.get_json()


def test_has_results_is_entry_level(wclient, fresh_db):
    # a registration whose entry raced elsewhere must report Has_Results so the UI hides Replace
    taisto, katja = _pids(fresh_db, "Taisto Miettinen", "Katja Kovanen")
    entry = scalar(fresh_db, "SELECT Entry_ID FROM REGISTRATION WHERE Edition_Year=2026 AND Bib_No=62")
    with fresh_db.cursor() as cur:
        cur.execute("INSERT INTO REGISTRATION (Bib_No, Registered_At, Payment_Status, Fee_Paid_EUR, Entry_ID, "
                    "Edition_Year, Race_No) VALUES (99, NOW(), 'Paid', 55, %s, 2027, 5)", (entry,))
        rid = cur.lastrowid
    assert wclient.get(f"/api/registrations/{rid}").get_json()["registration"]["Has_Results"] == 1


def test_out_of_range_numbers_400(wclient):
    payload = pair_payload()
    payload["members"][1]["weight_kg"] = 123456
    r = register(wclient, payload)
    assert r.status_code == 400 and "weight" in r.get_json()["error"]
    payload["members"][1]["weight_kg"] = "inf"
    assert register(wclient, payload).status_code == 400
    r = wclient.post("/api/results", json={"registration_id": 1, "stage": "Single", "status": "Finished",
                                           "raw_time_s": 1000000, "official_id": 1})
    assert r.status_code == 400
    r = wclient.post("/api/awards", json={"prize_id": 99999999999, "registration_id": 1})
    assert r.status_code == 400


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


# ---------------------------------------------------------------- Task 10: D3 remove unpaid booth booking
def test_d3_remove_only_booking_deletes_vendor(wclient, fresh_db):
    r = wclient.delete("/api/booths/8/2027")            # Retkeilijän Grilli: unpaid, only booking
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["vendor_deleted"] is True
    assert scalar(fresh_db, "SELECT COUNT(*) FROM VENDOR WHERE Vendor_ID=8") == 0


def test_d3_vendor_with_other_bookings_kept(wclient, fresh_db):
    r = wclient.delete("/api/booths/2/2027")            # Savon Käsityöpaja also booked 2026
    assert r.status_code == 200 and r.get_json()["vendor_deleted"] is False
    assert scalar(fresh_db, "SELECT COUNT(*) FROM VENDOR WHERE Vendor_ID=2") == 1
    assert scalar(fresh_db, "SELECT COUNT(*) FROM EXHIBITS_AT WHERE Vendor_ID=2 AND Edition_Year=2027") == 0


def test_d3_paid_booking_refused(wclient):
    r = wclient.delete("/api/booths/1/2026")
    assert r.status_code == 409 and r.get_json()["error"] == "Booking is already paid"


def test_d3_started_edition_refused(wclient, fresh_db):
    with fresh_db.cursor() as cur:
        cur.execute("UPDATE EXHIBITS_AT SET Paid = FALSE WHERE Vendor_ID = 3 AND Edition_Year = 2026")
    r = wclient.delete("/api/booths/3/2026")
    assert r.status_code == 409 and r.get_json()["error"] == "Edition has already started"


def test_d3_missing_booking_404(wclient):
    assert wclient.delete("/api/booths/9/2027").status_code == 404
