"""Wife-Carrying World Championship web application (Flask JSON API + built React frontend).

Run:  python app.py   then open http://localhost:5000
"""
from flask import Flask

import db
from api import register_error_handlers, respond


def create_app() -> Flask:
    app = Flask(__name__)
    app.json.sort_keys = False
    register_error_handlers(app)

    @app.get("/api/health")
    def health():
        sql = "SELECT DATABASE() AS db"
        return respond(db.query(sql), sql)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
