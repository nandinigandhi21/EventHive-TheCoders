from datetime import datetime, timedelta
from flask import current_app

_otp_cache = {}  # { phone: {otp, expires, attempts} }

def save_otp(phone: str, otp: str):
    _otp_cache[phone] = {
        "otp": otp,
        "expires": datetime.utcnow() + timedelta(minutes=current_app.config["OTP_EXP_MINUTES"]),
        "attempts": 0
    }

def fetch_otp(phone: str):
    return _otp_cache.get(phone)

def delete_otp(phone: str):
    _otp_cache.pop(phone, None)

def increment_attempt(phone: str):
    if phone in _otp_cache:
        _otp_cache[phone]["attempts"] += 1
        return _otp_cache[phone]["attempts"]
    return 0
