from extensions import db


class Tender(db.Model):
    __tablename__ = "tender"
    # add extend existing true
    __table_args__ = {"extend_existing": True}  # Allow extending existing table

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    json_data = db.Column(db.Text, nullable=False)  # Store JSON data as text
    metrics = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Tender {self.name}>"
