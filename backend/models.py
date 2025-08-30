from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="attendee")  # attendee, organizer, admin
    is_verified = db.Column(db.Boolean, default=False)   # verified after OTP

    # Relationship: one user (organizer) can have many events
    events = db.relationship("Event", backref="organizer", lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "is_verified": self.is_verified
        }


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)   # workshop, concert, sports, hackathon
    date = db.Column(db.String(20), nullable=False)       # YYYY-MM-DD
    time = db.Column(db.String(10), nullable=False)       # HH:MM
    location = db.Column(db.String(200), nullable=False)
    ticket_type = db.Column(db.String(50), nullable=False)  # General, VIP, etc.
    price = db.Column(db.Float, nullable=False)
    max_quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="draft")    # draft / published / unpublished

    # Link to organizer
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "date": self.date,
            "time": self.time,
            "location": self.location,
            "ticket_type": self.ticket_type,
            "price": self.price,
            "max_quantity": self.max_quantity,
            "status": self.status,
            "organizer_id": self.organizer_id
        }
