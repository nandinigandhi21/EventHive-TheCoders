from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models import db
from models import User
from utils.validators import normalize_phone, valid_role
from utils.otp_store import save_otp
import random

auth_bp = Blueprint("auth", __name__)

# ----------------- SIGNUP -----------------
@auth_bp.post("/signup")
def signup():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = normalize_phone(data.get("phone"))
    password = (data.get("password") or "").strip()
    role = data.get("role", "attendee")

    if not all([username, email, phone, password]):
        return {"error": "All fields required"}, 400
    if not valid_role(role):
        role = "attendee"

    # check duplicates
    if User.query.filter((User.email == email) | (User.phone == phone)).first():
        return {"error": "User already exists"}, 400

    # create unverified user
    user = User(username=username, email=email, phone=phone, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # generate OTP
    otp = str(random.randint(100000, 999999))
    save_otp(phone, otp)
    print(f"[OTP MOCK] Signup OTP for {phone}: {otp}")

    return {"msg": "User registered, verify OTP", "phone": phone, "debug_otp": otp}, 201


# ----------------- LOGIN -----------------
@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    identifier = (data.get("username") or data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    role = data.get("role")

    if not identifier or not password or not role:
        return {"error": "username/email, password, and role required"}, 400

    # lookup user
    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    if not user:
        return {"error": "User not found"}, 404
    if not user.check_password(password):
        return {"error": "Invalid password"}, 401
    if user.role != role:
        return {"error": "Role mismatch"}, 403
    if not user.is_verified:
        return {"error": "User not verified, complete OTP first"}, 403

    token = create_access_token(identity={"id": user.id, "role": user.role})
    return {"access_token": token, "user": user.to_dict()}, 200
