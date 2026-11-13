"""Wife-Carrying World Championship web application (Flask JSON API + built React frontend).

Run:  python app.py   then open http://localhost:5000
"""
from flask import Flask

import db
from api import ApiError, body, done, parse_choice, parse_int, parse_str, register_error_handlers, respond
from repo import people, prizes, protests, registrations, reports, results, vendors


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
    register_registration_routes(app)
    register_jury_routes(app)
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


def register_registration_routes(app: Flask) -> None:
    @app.post("/api/registrations")
    def api_register():                                  # I1
        result, sqls = registrations.register(body(), results.SERIES)
        return done(f"Registered with bib {result['bib_no']}", *sqls, **result)

    @app.get("/api/registrations/<int:reg_id>")
    def api_registration(reg_id):
        registration, members, sqls = registrations.details(reg_id)
        return respond(members, *sqls, registration=registration)

    @app.post("/api/registrations/<int:reg_id>/cancel")
    def api_cancel(reg_id):                              # U2
        refund, sqls = registrations.cancel(reg_id)
        return done(f"Registration cancelled; refund {refund:.2f} EUR", *sqls, refund=refund)

    @app.patch("/api/entries/<int:entry_id>/roles/<role>")
    def api_replace_member(entry_id, role):              # U4
        person_id, sqls = registrations.replace_member(entry_id, role, body())
        return done("Member replaced", *sqls, person_id=person_id)

    @app.delete("/api/registrations/<int:reg_id>")
    def api_delete_registration(reg_id):                 # D1
        sqls = registrations.delete(reg_id)
        return done("Registration deleted", *sqls)

    @app.get("/api/entries/unregistered")
    def api_unregistered():
        rows, sql = registrations.unregistered_entries()
        return respond(rows, sql)

    @app.delete("/api/entries/<int:entry_id>")
    def api_delete_entry(entry_id):                      # D2
        sql = registrations.delete_entry(entry_id)
        return done("Entry deleted", sql)


def register_jury_routes(app: Flask) -> None:
    @app.get("/api/officials")
    def api_officials():
        rows, sql = results.officials()
        return respond(rows, sql)

    @app.post("/api/results")
    def api_record_result():                             # I2
        return done("Result recorded", *results.record_result(body()))

    @app.patch("/api/results/<int:reg_id>/<stage>")
    def api_correct_result(reg_id, stage):               # U1
        return done("Result corrected; ranks and placement prizes updated",
                    *results.correct_result(reg_id, stage, body()))

    @app.post("/api/penalties")
    def api_add_penalty():                               # U1
        return done("Penalty added; ranks and placement prizes updated", *results.add_penalty(body()))

    @app.post("/api/protests")
    def api_file_protest():                              # I3
        protest_id, sql = protests.file_protest(body())
        return done(f"Protest {protest_id} filed", sql, protest_id=protest_id)

    @app.post("/api/protests/<int:protest_id>/decide")
    def api_decide_protest(protest_id):                  # U3
        return done("Protest decided", *protests.decide(protest_id, body()))

    @app.get("/api/prizes")
    def api_prizes():
        rows, sql = prizes.for_series(parse_choice("series", results.SERIES))
        return respond(rows, sql)

    @app.post("/api/awards")
    def api_award():                                     # I4
        return done("Prize awarded", prizes.award(body()))


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
