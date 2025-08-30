from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random, smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from sqlalchemy import func
from textblob import TextBlob   # 🔥 NEW: for sentiment analysis

load_dotenv()

app = Flask(__name__)
CORS(app)

# ---------------- Database ---------------- #
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- Models ---------------- #
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)   # workshop, concert, sports, etc.
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    ticket_type = db.Column(db.String(50), nullable=False) # General, VIP, etc.
    price = db.Column(db.Float, nullable=False)
    max_quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="draft")     # draft or published
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"))

with app.app_context():
    db.create_all()
    # 🔥 Fix existing statuses to lowercase (run once)
    for e in Event.query.all():
        if e.status:
            e.status = e.status.lower()
    db.session.commit()

otp_store = {}

# ---------------- Gmail Config ---------------- #
GMAIL_USER = "teameventhive@gmail.com"
GMAIL_PASS = "mlgi mwdp fnnl jgwi"   # Generated from Google App Passwords

def send_email(receiver, otp):
    """Send OTP via Gmail SMTP"""
    msg = MIMEText(f"Hello ,\n\nYour EventHive OTP is: {otp}\n\nUse this to verify your account.\n\n- EventHive Team")
    msg["Subject"] = "EventHive OTP Verification"
    msg["From"] = GMAIL_USER
    msg["To"] = receiver

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, receiver, msg.as_string())
        server.quit()
        print(f"✅ OTP sent to {receiver}")
    except Exception as e:
        print("❌ Email send failed:", e)


# ---------------- Auth Routes ---------------- #
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")

    # Generate random OTP
    otp = str(random.randint(100000, 999999))
    otp_store[email] = {**data, "otp": otp}

    # Send OTP to email
    send_email(email, otp)

    return jsonify({"message": f"OTP sent to {email}"})


@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    email, otp = data.get("email"), data.get("otp")

    if email in otp_store and otp_store[email]["otp"] == otp:
        new_user = User(
            username=otp_store[email]["username"],
            email=email,
            phone=otp_store[email]["phone"],
            password=otp_store[email]["password"],
            role=otp_store[email]["role"]
        )
        db.session.add(new_user)
        db.session.commit()
        otp_store.pop(email)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid OTP"}), 400


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email, password = data.get("email"), data.get("password")
    user = User.query.filter_by(email=email, password=password).first()

    if user:
        return jsonify({"status": "success", "role": user.role, "user_id": user.id})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401


# ---------------- Event Routes ---------------- #
@app.route("/api/events/create", methods=["POST"])
def create_event():
    try:
        data = request.json

        new_event = Event(
            title=data["title"],
            description=data["description"],
            category=data["category"],
            date=data["date"],
            time=data["time"],
            location=data["location"],
            ticket_type=data["ticket_type"],
            price=float(data["price"]),
            max_quantity=int(data["max_quantity"]),
            status=data.get("status", "draft").lower(),  # 🔥 Always lowercase
            organizer_id=int(data["organizer_id"])
        )

        db.session.add(new_event)
        db.session.commit()

        return jsonify({"message": "Event created successfully!", "event_id": new_event.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/events/my-events/<int:organizer_id>", methods=["GET"])
def get_my_events(organizer_id):
    try:
        events = Event.query.filter_by(organizer_id=organizer_id).all()
        events_list = [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "category": e.category,
                "date": e.date,
                "time": e.time,
                "location": e.location,
                "ticket_type": e.ticket_type,
                "price": e.price,
                "max_quantity": e.max_quantity,
                "status": e.status,
            }
            for e in events
        ]
        return jsonify(events_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/events/delete/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({"error": "Event not found"}), 404

        db.session.delete(event)
        db.session.commit()
        return jsonify({"message": "Event deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- Attendee Routes ---------------- #
@app.route("/api/events", methods=["GET"])
def get_all_events():
    try:
        # 🔥 Case-insensitive filter
        events = Event.query.filter(func.lower(Event.status) == "published").all()
        events_list = [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "category": e.category,
                "date": e.date,
                "time": e.time,
                "location": e.location,
                "ticket_type": e.ticket_type,
                "price": e.price,
                "max_quantity": e.max_quantity,
                "organizer_id": e.organizer_id
            }
            for e in events
        ]
        return jsonify(events_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- Admin Routes (Users) ---------------- #
@app.route("/api/admin/users", methods=["GET"])
def get_all_users():
    try:
        users = User.query.all()
        users_list = [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "phone": u.phone,
                "role": u.role
            }
            for u in users
        ]
        return jsonify(users_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/admin/users/<int:user_id>/role", methods=["PUT"])
def update_role(user_id):
    try:
        data = request.json
        new_role = data.get("role")

        if new_role not in ("attendee", "organizer", "admin"):
            return jsonify({"error": "Invalid role"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.role = new_role
        db.session.commit()
        return jsonify({
            "message": f"Role updated to {new_role}",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/admin/stats", methods=["GET"])
def get_stats():
    try:
        total_users = User.query.count()
        attendees = User.query.filter_by(role="attendee").count()
        organizers = User.query.filter_by(role="organizer").count()
        admins = User.query.filter_by(role="admin").count()

        return jsonify({
            "total_users": total_users,
            "attendees": attendees,
            "organizers": organizers,
            "admins": admins
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- Admin Event Routes ---------------- #
@app.route("/api/admin/events", methods=["GET"])
def admin_get_all_events():
    try:
        events = Event.query.all()
        events_list = [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "category": e.category,
                "date": e.date,
                "time": e.time,
                "location": e.location,
                "ticket_type": e.ticket_type,
                "price": e.price,
                "max_quantity": e.max_quantity,
                "status": e.status,
                "organizer_id": e.organizer_id
            }
            for e in events
        ]
        return jsonify(events_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/admin/events/<int:event_id>/status", methods=["PUT"])
def admin_update_event_status(event_id):
    try:
        data = request.json
        new_status = data.get("status", "").lower()

        if new_status not in ["draft", "published"]:
            return jsonify({"error": "Invalid status"}), 400

        event = Event.query.get(event_id)
        if not event:
            return jsonify({"error": "Event not found"}), 404

        event.status = new_status
        db.session.commit()
        return jsonify({"message": f"Event status updated to {new_status}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/admin/events/<int:event_id>", methods=["DELETE"])
def admin_delete_event(event_id):
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({"error": "Event not found"}), 404

        db.session.delete(event)
        db.session.commit()
        return jsonify({"message": "Event deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- Feedback Sentiment Route (AI/ML) ---------------- #
@app.route("/api/feedback/analyze", methods=["POST"])
def analyze_feedback():
    data = request.get_json()
    feedback_text = data.get("feedback", "")

    if not feedback_text.strip():
        return jsonify({"error": "Feedback text required"}), 400

    analysis = TextBlob(feedback_text)
    polarity = analysis.sentiment.polarity

    # Convert polarity (-1 to 1) into categories
    if polarity > 0.1:
        sentiment = "positive"
    elif polarity < -0.1:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return jsonify({
        "feedback": feedback_text,
        "sentiment": sentiment,
        "polarity": polarity
    })


if __name__ == "__main__":
    app.run(debug=True)
