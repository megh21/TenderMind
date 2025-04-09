from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    with app.app_context():
        # Import models here to ensure they are registered with SQLAlchemy
        db.create_all()
