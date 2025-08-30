import os, random, smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

# ---------------- App / Config ---------------- #
load_dotenv()  # reads .env if present

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///eventhive.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

db = SQLAlchemy(app)

# ---------------- Models ---------------- #
class User(db.Model):
    __tablename__ = "users"  # keep consistent (plural)

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password = db.Column(db.String(100))  # plain for hackathon; hash later
    role = db.Column(db.String(20), default="attendee")  # attendee | organizer | admin

class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)    # workshop, concert, sports, hackathon
    date = db.Column(db.String(20), nullable=False)        # "YYYY-MM-DD"
    time = db.Column(db.String(20), nullable=False)        # "HH:MM AM/PM"
    location = db.Column(db.String(200), nullable=False)
    ticket_type = db.Column(db.String(50), nullable=False) # General, VIP, Student, Early Bird
    price = db.Column(db.Float, nullable=False)
    max_quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="draft")     # draft | published
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"))

with app.app_context():
    db.create_all()

# ---------------- Email (OTP) ---------------- #
GMAIL_USER = os.getenv("GMAIL_USER", "teameventhive@gmail.com")
GMAIL_PASS = os.getenv("GMAIL_PASS", "")  # set via .env

def send_email(receiver, otp):
    if not GMAIL_USER or not GMAIL_PASS:
        print("⚠️ Skipping email send (GMAIL_USER/GMAIL_PASS not set). OTP:", otp)
        return

    msg = MIMEText(
        f"Hello 👋,\n\nYour EventHive OTP is: {otp}\n\nUse this to verify your account.\n\n- EventHive Team"
    )
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

# in-memory store for signup pre-verification
otp_store = {}

# ---------------- Auth Routes ---------------- #
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json or {}
    required = ["username", "email", "phone", "password", "role"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"ok": False, "message": f"Missing: {', '.join(missing)}"}), 400

    # block duplicate email
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"ok": False, "message": "Email already registered"}), 409

    otp = str(random.randint(100000, 999999))
    otp_store[data["email"]] = {**data, "otp": otp}
    send_email(data["email"], otp)

    return jsonify({"ok": True, "message": f"OTP sent to {data['email']}"}), 200

@app.route("/api/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json or {}
    email = data.get("email")
    otp = data.get("otp")

    if not email or not otp:
        return jsonify({"ok": False, "message": "Email and OTP are required"}), 400

    record = otp_store.get(email)
    if not record or record["otp"] != otp:
        return jsonify({"ok": False, "message": "Invalid or expired OTP"}), 400

    # create user
    user = User(
        username=record["username"],
        email=record["email"],
        phone=record["phone"],
        password=record["password"],  # NOTE: hash later
        role=record["role"],
    )
    db.session.add(user)
    db.session.commit()
    otp_store.pop(email, None)

    return jsonify({"ok": True, "message": "Account verified", "user_id": user.id, "role": user.role}), 201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    email, password = data.get("email"), data.get("password")
    if not email or not password:
        return jsonify({"ok": False, "message": "Email and password required"}), 400

    user = User.query.filter_by(email=email, password=password).first()
    if not user:
        return jsonify({"ok": False, "message": "Invalid credentials"}), 401

    return jsonify({"ok": True, "user_id": user.id, "role": user.role, "username": user.username}), 200

# ---------------- Organizer: Events ---------------- #
def ensure_organizer(user_id: int):
    user = User.query.get(user_id)
    if not user:
        return None, ("User not found", 404)
    if user.role not in ("organizer", "admin"):
        return None, ("Only organizers/admins can perform this action", 403)
    return user, None

@app.route("/api/events/create", methods=["POST"])
def create_event():
    data = request.json or {}
    required = [
        "title","description","category","date","time",
        "location","ticket_type","price","max_quantity","organizer_id"
    ]
    missing = [k for k in required if data.get(k) in (None, "")]
    if missing:
        return jsonify({"ok": False, "message": f"Missing: {', '.join(missing)}"}), 400

    organizer_id = int(data["organizer_id"])
    user, err = ensure_organizer(organizer_id)
    if err: return jsonify({"ok": False, "message": err[0]}), err[1]

    event = Event(
        title=data["title"].strip(),
        description=data["description"].strip(),
        category=data["category"],
        date=data["date"],
        time=data["time"],
        location=data["location"].strip(),
        ticket_type=data["ticket_type"],
        price=float(data["price"]),
        max_quantity=int(data["max_quantity"]),
        status=data.get("status", "draft"),
        organizer_id=organizer_id,
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({"ok": True, "message": "Event created", "event_id": event.id}), 201

@app.route("/api/events/<int:event_id>/edit", methods=["PUT"])
def edit_event(event_id):
    data = request.json or {}
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"ok": False, "message": "Event not found"}), 404

    organizer_id = int(data.get("organizer_id", 0))
    user, err = ensure_organizer(organizer_id)
    if err: return jsonify({"ok": False, "message": err[0]}), err[1]
    if user.role != "admin" and event.organizer_id != organizer_id:
        return jsonify({"ok": False, "message": "Not your event"}), 403

    # Update allowed fields
    for field in ["title","description","category","date","time","location","ticket_type","price","max_quantity","status"]:
        if field in data and data[field] not in (None, ""):
            setattr(event, field, data[field] if field not in ("price","max_quantity") else (float(data[field]) if field=="price" else int(data[field])))

    db.session.commit()
    return jsonify({"ok": True, "message": "Event updated"}), 200

@app.route("/api/events/<int:event_id>/toggle", methods=["PATCH"])
def toggle_event(event_id):
    data = request.json or {}
    organizer_id = int(data.get("organizer_id", 0))
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"ok": False, "message": "Event not found"}), 404

    user, err = ensure_organizer(organizer_id)
    if err: return jsonify({"ok": False, "message": err[0]}), err[1]
    if user.role != "admin" and event.organizer_id != organizer_id:
        return jsonify({"ok": False, "message": "Not your event"}), 403

    event.status = "published" if event.status == "draft" else "draft"
    db.session.commit()
    return jsonify({"ok": True, "new_status": event.status}), 200

@app.route("/api/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    data = request.json or {}
    organizer_id = int(data.get("organizer_id", 0))
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"ok": False, "message": "Event not found"}), 404

    user, err = ensure_organizer(organizer_id)
    if err: return jsonify({"ok": False, "message": err[0]}), err[1]
    if user.role != "admin" and event.organizer_id != organizer_id:
        return jsonify({"ok": False, "message": "Not your event"}), 403

    db.session.delete(event)
    db.session.commit()
    return jsonify({"ok": True, "message": "Event deleted"}), 200

# ---------------- Attendee: Discover ---------------- #
@app.route("/api/events", methods=["GET"])
def list_events():
    """
    Query params:
      status=published|draft (default: published)
      category=<str>
      ticket_type=<str>
      date=YYYY-MM-DD
      organizer_id=<int>   (for organizer dashboard)
      q=<search in title/description>
      page=<int> (1..), limit=<int> (default 12)
    """
    status = request.args.get("status", "published")
    category = request.args.get("category")
    ticket_type = request.args.get("ticket_type")
    date = request.args.get("date")
    organizer_id = request.args.get("organizer_id", type=int)
    q = request.args.get("q", type=str, default="")

    page = max(request.args.get("page", default=1, type=int), 1)
    limit = min(max(request.args.get("limit", default=12, type=int), 1), 50)

    qry = Event.query
    if status:
        qry = qry.filter_by(status=status)
    if category:
        qry = qry.filter_by(category=category)
    if ticket_type:
        qry = qry.filter_by(ticket_type=ticket_type)
    if date:
        qry = qry.filter_by(date=date)
    if organizer_id:
        qry = qry.filter_by(organizer_id=organizer_id)
    if q:
        like = f"%{q}%"
        from sqlalchemy import or_
        qry = qry.filter(or_(Event.title.ilike(like), Event.description.ilike(like)))

    total = qry.count()
    events = qry.order_by(Event.id.desc()).offset((page - 1) * limit).limit(limit).all()

    return jsonify({
        "ok": True,
        "total": total,
        "page": page,
        "limit": limit,
        "items": [{
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
        } for e in events]
    }), 200

@app.route("/api/events/<int:event_id>", methods=["GET"])
def event_detail(event_id):
    e = Event.query.get(event_id)
    if not e:
        return jsonify({"ok": False, "message": "Event not found"}), 404
    return jsonify({
        "ok": True,
        "item": {
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
    }), 200

# ---------------- Main ---------------- #
if __name__ == "__main__":
    app.run(debug=True)
