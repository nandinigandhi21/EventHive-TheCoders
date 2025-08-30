from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models import db
from models import User
from utils.otp_store import fetch_otp, delete_otp, increment_attempt

otp_bp = Blueprint("otp", __name__)

@otp_bp.post("/verify-otp")
def verify_otp():
    data = request.get_json() or {}
    phone = (data.get("phone") or "").strip()
    otp = (data.get("otp") or "").strip()

    if not phone or not otp:
        return {"error": "phone and otp required"}, 400

    rec = fetch_otp(phone)
    if not rec:
        return {"error": "otp not found"}, 404

    if increment_attempt(phone) > 5:
        delete_otp(phone)
        return {"error": "too many attempts"}, 429

    from datetime import datetime
    if datetime.utcnow() > rec["expires"]:
        delete_otp(phone)
        return {"error": "otp expired"}, 400

    if rec["otp"] != otp:
        return {"error": "invalid otp"}, 401

    # success → mark verified
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return {"error": "user not found"}, 404

    user.is_verified = True
    db.session.commit()

    token = create_access_token(identity={"id": user.id, "role": user.role})
    delete_otp(phone)

    return {"msg": "OTP verified", "access_token": token, "user": user.to_dict()}, 200
