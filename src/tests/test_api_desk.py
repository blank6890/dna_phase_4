"""Task 7: Staff Desk reads and analysis reports (S1, S2, P1, A2-A5, AR1-AR6)."""
from conftest import scalar


def rows(client, url):
    r = client.get(url)
    assert r.status_code == 200, r.get_json()
    assert "SELECT" in r.get_json()["sql"]
    return r.get_json()["rows"]


def test_s1_registrations(client):
    data = rows(client, "/api/registrations?year=2026&series=MAIN")
    assert len(data) == 45
    assert {"Registration_ID", "Bib_No", "Status", "Refund_EUR", "Display_Name", "Fee_Paid_EUR"} <= set(data[0])


def test_s2_pending_protests(client):
    data = rows(client, "/api/protests?status=Pending")
    assert len(data) == 2 and all(r["Outcome"] == "Pending" for r in data)
    assert {"Protest_ID", "Filed_At", "Reason", "Series_Code", "Display_Name"} <= set(data[0])


def test_s2_bad_status_400(client):
    assert client.get("/api/protests?status=Maybe").status_code == 400


def test_p1_projection(client):
    data = rows(client, "/api/editions/2026/persons")
    assert data and set(data[0]) == {"First_Name", "Last_Name", "Date_of_Birth"}


def test_a5_heaviest_carried(client, db_conn):
    expected = scalar(db_conn, """
        SELECT MAX(pa.Measured_Weight_kg) FROM PARTICIPATES_AS pa
        JOIN REGISTRATION r ON r.Entry_ID = pa.Entry_ID
        WHERE r.Edition_Year = 2026 AND r.Cancelled_At IS NULL AND pa.Role_Code = 'CARRIED'""")
    data = rows(client, "/api/editions/2026/heaviest-carried")
    assert data and all(r["Measured_Weight_kg"] == float(expected) for r in data)


def test_a2_avg_times(client):
    data = rows(client, "/api/reports/avg-times")
    main26 = next(r for r in data if r["Edition_Year"] == 2026 and r["Series_Code"] == "MAIN")
    assert main26["Finishers"] == 43 and 60 < main26["Avg_Net_Time_s"] < 120


def test_a3_fees(client):
    data = {r["Edition_Year"]: r["Total_Fees_EUR"] for r in rows(client, "/api/reports/fees")}
    assert data[2027] == 9 * 55.0


def test_a4_registrations_by_country(client):
    data = rows(client, "/api/reports/registrations-by-country?year=2026")
    assert data[0]["ISO_Code"] == "FIN"


def test_ar1_medals(client):
    data = rows(client, "/api/reports/medals")
    assert data[0]["ISO_Code"] == "FIN" and data[0]["Gold"] >= 15
    est = next(r for r in data if r["ISO_Code"] == "EST")
    assert est["Gold"] >= 9


def test_ar2_backpacks(client):
    data = rows(client, "/api/reports/backpacks")
    assert data and all(r["Required_Backpack_kg"] > 0 for r in data)


def test_ar3_multi_series(client):
    data = rows(client, "/api/reports/multi-series?year=2026")
    lee = {r["Series_Code"] for r in data if r["First_Name"] == "Andrew" and r["Last_Name"] == "Lee"}
    assert lee == {"SPR", "M40", "TEAM"}


def test_ar4_income(client):
    row = next(r for r in rows(client, "/api/reports/income") if r["Edition_Year"] == 2026)
    assert row["Protest_Fees_EUR"] == 4 * 150
    assert row["Booth_Fees_EUR"] == 160 + 70 + 70 + 220 + 140 + 85 + 70
    assert row["Registration_Fees_Net_EUR"] > 0


def test_ar5_protest_outcomes(client):
    data = rows(client, "/api/reports/protests")
    main = next(r for r in data if r["Edition_Year"] == 2026 and r["Series_Code"] == "MAIN")
    assert main["Filed"] == 2 and main["Upheld"] == 0 and "Hyvönen" in main["Voters"]


def test_ar6_above_average(client):
    data = rows(client, "/api/reports/above-average?year=2026")
    assert data and all(r["Country_Avg_s"] < r["Edition_Avg_s"] for r in data)
