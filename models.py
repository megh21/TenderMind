from extensions import db  # Import db from extensions.py


class Tender(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    json_data = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Tender {self.name}>"
