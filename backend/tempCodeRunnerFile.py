from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random, smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
CORS(app)

# ---------------- Database ---------------- #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eventhive.db'
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
    db.drop_all()   # delete all existing tables (and data)
    db.create_all() # recreate tables with new schema


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
        print(f"OTP sent to {receiver}")
    except Exception as e:
        print("Email send failed:", e)

# ---------------- Routes ---------------- #
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
        return jsonify({"status": "success", "role": user.role})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

if __name__ == "__main__":
    app.run(debug=True)
