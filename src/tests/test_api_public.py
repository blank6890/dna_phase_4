"""Task 6: public read endpoints (S3, A1, Q1-Q4, P2, P3, champions, competitors, GP, person)."""


def rows(client, url):
    r = client.get(url)
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert "SELECT" in body["sql"]
    return body["rows"]


def test_editions(client):
    years = [r["Edition_Year"] for r in rows(client, "/api/editions")]
    assert years[0] == 2027 and 1992 in years and 2020 not in years


def test_s3_sprint_final(client):
    names = [r["Display_Name"] for r in rows(client, "/api/results?year=2026&series=SPR&stage=Final")]
    assert names == ["Teemu Tuovinen / Jatta Leinonen", "Jonatan Wasenius / Lotta Lindroos",
                     "Edward Nash / Kathryn Knight", "Andrew Lee / Devon Lee"]


def test_results_main_has_dns_last_and_ranks(client):
    data = rows(client, "/api/results?year=2026&series=MAIN")
    assert len(data) == 45
    assert data[0]["Rank_In_Stage"] == 1 and data[0]["Bib_No"] == 62
    assert [r["Status"] for r in data[-2:]] == ["DNS", "DNS"]


def test_results_team_shows_penalty_and_team(client):
    row = next(r for r in rows(client, "/api/results?year=2026&series=TEAM") if r["Bib_No"] == 105)
    assert row["Team_Name"] == "Team 2 SPOLK" and row["Penalty_s"] == 15.0 and row["Net_Time_s"] == 154.9
    assert row["Penalty_Nos"] == "1"


def test_a1_records(client):
    data = {r["Series_Code"]: (r["Best_Time_s"], r["Edition_Year"]) for r in rows(client, "/api/records")}
    assert data == {"MAIN": (56.9, 2006), "TEAM": (84.6, 2008), "SPR": (31.34, 2012),
                    "M40": (73.49, 2026), "WOMEN": (99.51, 2025)}


def test_champions_2026_main(client):
    data = rows(client, "/api/champions")
    main = [r for r in data if r["Edition_Year"] == 2026 and r["Series_Code"] == "MAIN"]
    assert [r["Display_Name"] for r in main] == ["Taisto Miettinen / Katja Kovanen"]
    sprint_2007 = [r for r in data if r["Edition_Year"] == 2007 and r["Series_Code"] == "SPR"]
    assert len(sprint_2007) == 2          # shared win


def test_q1_partial(client):
    names = [f'{r["First_Name"]} {r["Last_Name"]}' for r in rows(client, "/api/search/persons?q=kirk")]
    assert "Vytautas Kirkliauskas" in names
    names = [f'{r["First_Name"]} {r["Last_Name"]}' for r in rows(client, "/api/search/persons?q=föhr")]
    assert "Timo Föhr" in names
    assert rows(client, "/api/search/persons?q=%25%25") == []
    assert rows(client, "/api/search/persons?q=__") == []


def test_q1_full_name(client):
    names = [f'{r["First_Name"]} {r["Last_Name"]}' for r in rows(client, "/api/search/persons?q=taisto%20miet")]
    assert names == ["Taisto Miettinen"]


def test_q2(client):
    data = rows(client, "/api/search/teams?q=sonkaj")
    assert any(r["Team_Name"] == "Sonkajärven kunta" for r in data)
    assert any("Sonkajärven" in (r["Represented_Organisation"] or "") for r in data)


def test_q3_country_series(client):
    data = rows(client, "/api/entries?year=2026&series=MAIN&country=GBR")
    assert sorted(r["Bib_No"] for r in data) == [44, 51, 63]


def test_q3_without_country(client):
    assert len(rows(client, "/api/entries?year=2027&series=MAIN")) == 4


def test_q4_category(client):
    data = rows(client, "/api/vendors?category=Food")
    assert data and all("Food" in r["Categories"] for r in data)
    assert [r["Business_Name"] for r in rows(client, "/api/vendors?q=hunaja")] == ["Ylä-Savon Hunaja"]


def test_p2_projection_columns(client):
    data = rows(client, "/api/teams")
    assert data and set(data[0]) == {"Team_Name", "Represented_Organisation"}


def test_p3_booths_2027(client):
    data = rows(client, "/api/editions/2027/booths")
    assert any(r["Paid"] == 0 for r in data)
    assert set(data[0]) >= {"Business_Name", "Booth_Size", "Booth_Fee_EUR", "Paid"}


def test_grand_prix(client):
    data = rows(client, "/api/grand-prix")
    assert any(r["City"] == "Kirkcudbright" and r["Continent"] == "Europe" for r in data)


def test_person_history(client):
    pid = rows(client, "/api/search/persons?q=andrew%20lee")[0]["Person_ID"]
    r = client.get(f"/api/people/{pid}")
    assert r.status_code == 200
    body = r.get_json()
    assert body["person"]["Last_Name"] == "Lee"
    series_2026 = {h["Series_Code"] for h in body["rows"] if h["Edition_Year"] == 2026}
    assert series_2026 == {"SPR", "M40", "TEAM"}


def test_bad_year_400(client):
    r = client.get("/api/results?year=abc&series=MAIN")
    assert r.status_code == 400 and "year" in r.get_json()["error"]


def test_bad_series_400(client):
    assert client.get("/api/results?year=2026&series=XYZ").status_code == 400


def test_search_too_short_400(client):
    assert client.get("/api/search/persons?q=a").status_code == 400


def test_person_404(client):
    assert client.get("/api/people/999999").status_code == 404


def test_q1_ascii_apostrophe_finds_typographic(client):
    names = [f'{r["First_Name"]} {r["Last_Name"]}' for r in rows(client, "/api/search/persons?q=O'Call")]
    assert "Donncha O’Callaghan" in names
