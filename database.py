from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Tender(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text)


def init_db(app):
    # Set the database to be stored in the same directory with a custom name
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tender.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Avoid unnecessary overhead

    db.init_app(app)
    with app.app_context():
        db.create_all()
