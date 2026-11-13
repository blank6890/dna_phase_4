"""Wife-Carrying World Championship web application (Flask JSON API + built React frontend).

Run:  python app.py   then open http://localhost:5000
"""
from flask import Flask

import db
from api import ApiError, parse_choice, parse_int, parse_str, register_error_handlers, respond
from repo import people, protests, registrations, reports, results, vendors


def create_app() -> Flask:
    app = Flask(__name__)
    app.json.sort_keys = False
    register_error_handlers(app)

    @app.get("/api/health")
    def health():
        sql = "SELECT DATABASE() AS db"
        return respond(db.query(sql), sql)

    register_public_routes(app)
    register_desk_routes(app)
    return app


def register_public_routes(app: Flask) -> None:
    @app.get("/api/editions")
    def api_editions():
        rows, sql = results.editions()
        return respond(rows, sql)

    @app.get("/api/results")
    def api_results():                                   # S3 when series=SPR&stage=Final
        year = parse_int("year")
        series = parse_choice("series", results.SERIES)
        stage = parse_choice("stage", results.STAGES, required=False)
        rows, sql = results.results(year, series, stage)
        return respond(rows, sql)

    @app.get("/api/records")
    def api_records():                                   # A1
        rows, sql = results.records()
        return respond(rows, sql)

    @app.get("/api/champions")
    def api_champions():
        rows, sql = results.champions()
        return respond(rows, sql)

    @app.get("/api/grand-prix")
    def api_grand_prix():
        rows, sql = results.grand_prix()
        return respond(rows, sql)

    @app.get("/api/entries")
    def api_entries():                                   # Q3 and Registered Competitors
        year = parse_int("year")
        series = parse_choice("series", results.SERIES)
        country = parse_str("country", max_len=3, required=False)
        rows, sql = people.entries(year, series, country.upper() if country else None)
        return respond(rows, sql)

    @app.get("/api/teams")
    def api_teams():                                     # P2
        rows, sql = people.teams()
        return respond(rows, sql)

    def search_term():
        q = parse_str("q", max_len=60)
        if len(q) < 2:
            raise ApiError(400, "Search term must be at least 2 characters")
        return q

    @app.get("/api/search/persons")
    def api_search_persons():                            # Q1
        rows, sql = people.search_persons(search_term())
        return respond(rows, sql)

    @app.get("/api/search/teams")
    def api_search_teams():                              # Q2
        rows, sql = people.search_teams(search_term())
        return respond(rows, sql)

    @app.get("/api/people/<int:person_id>")
    def api_person(person_id):
        person, rows, sqls = people.person(person_id)
        if person is None:
            raise ApiError(404, "Person not found")
        return respond(rows, *sqls, person=person)

    @app.get("/api/vendors")
    def api_vendors():                                   # Q4
        q = parse_str("q", max_len=60, required=False)
        category = parse_choice("category", vendors.CATEGORIES, required=False)
        rows, sql = vendors.search(q, category)
        return respond(rows, sql)

    @app.get("/api/editions/<int:year>/booths")
    def api_booths(year):                                # P3
        rows, sql = vendors.booths(year)
        return respond(rows, sql)


def register_desk_routes(app: Flask) -> None:
    @app.get("/api/registrations")
    def api_registrations():                             # S1
        year = parse_int("year")
        series = parse_choice("series", results.SERIES)
        rows, sql = registrations.list_for_race(year, series)
        return respond(rows, sql)

    @app.get("/api/protests")
    def api_protests():                                  # S2 with status=Pending
        status = parse_choice("status", protests.OUTCOMES, required=False)
        rows, sql = protests.list_protests(status)
        return respond(rows, sql)

    @app.get("/api/editions/<int:year>/persons")
    def api_edition_persons(year):                       # P1
        rows, sql = registrations.persons_in_edition(year)
        return respond(rows, sql)

    @app.get("/api/editions/<int:year>/heaviest-carried")
    def api_heaviest(year):                              # A5
        rows, sql = registrations.heaviest_carried(year)
        return respond(rows, sql)

    simple_reports = {
        "avg-times": reports.avg_times,                  # A2
        "fees": reports.fees,                            # A3
        "medals": reports.medals,                        # AR1
        "backpacks": reports.backpacks,                  # AR2
        "income": reports.income,                        # AR4
        "protests": reports.protest_outcomes,            # AR5
    }
    year_reports = {
        "registrations-by-country": reports.registrations_by_country,   # A4
        "multi-series": reports.multi_series,                           # AR3
        "above-average": reports.above_average,                         # AR6
    }

    @app.get("/api/reports/<name>")
    def api_report(name):
        if name in simple_reports:
            rows, sql = simple_reports[name]()
        elif name in year_reports:
            rows, sql = year_reports[name](parse_int("year"))
        else:
            raise ApiError(404, "Unknown report")
        return respond(rows, sql)


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
