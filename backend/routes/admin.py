from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User

admin_bp = Blueprint("admin", __name__)

# ---------------- Middleware ---------------- #
def admin_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if not identity or identity.get("role") != "admin":
            return {"error": "Admin access required"}, 403
        return func(*args, **kwargs)
    return wrapper

# ---------------- Routes ---------------- #

@admin_bp.get("/users")
@jwt_required()
@admin_required
def get_all_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200


@admin_bp.delete("/users/<int:user_id>")
@jwt_required()
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404
    db.session.delete(user)
    db.session.commit()
    return {"msg": "User deleted"}, 200


@admin_bp.put("/users/<int:user_id>/role")
@jwt_required()
@admin_required
def update_role(user_id):
    data = request.get_json() or {}
    new_role = data.get("role")

    if new_role not in ("attendee", "organizer", "admin"):
        return {"error": "Invalid role"}, 400

    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    user.role = new_role
    db.session.commit()
    return {"msg": f"Role updated to {new_role}", "user": user.to_dict()}, 200


@admin_bp.get("/stats")
@jwt_required()
@admin_required
def get_stats():
    total_users = User.query.count()
    attendees = User.query.filter_by(role="attendee").count()
    organizers = User.query.filter_by(role="organizer").count()
    admins = User.query.filter_by(role="admin").count()

    return {
        "total_users": total_users,
        "attendees": attendees,
        "organizers": organizers,
        "admins": admins
    }, 200
