from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from backend.models import db, User, Event, Ticket

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# ------------------ Dashboard Stats ------------------
@admin_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    try:
        total_users = User.query.count()
        organizers = User.query.filter_by(role="organizer").count()
        total_events = Event.query.count()
        published_events = Event.query.filter_by(status="published").count()
        tickets_sold = db.session.query(db.func.sum(Ticket.quantity)).scalar() or 0
        revenue = db.session.query(db.func.sum(Ticket.price * Ticket.quantity)).scalar() or 0

        return jsonify({
            "ok": True,
            "totals": {
                "users": total_users,
                "organizers": organizers,
                "events": total_events,
                "published": published_events,
                "ticketsSold": tickets_sold,
                "revenue": revenue
            },
            "timeseries": {"labels": [], "signups": [], "bookings": []},
            "categories": {"Music": 0, "Sports": 0, "Tech": 0}
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ------------------ Manage Users ------------------
@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    users = User.query.all()
    items = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "phone": u.phone,
            "role": u.role,
        } for u in users
    ]
    return jsonify(items)

@admin_bp.route("/users/<int:user_id>/role", methods=["PUT"])
@jwt_required()
def update_user_role(user_id):
    data = request.get_json()
    new_role = data.get("role")
    user = User.query.get_or_404(user_id)
    user.role = new_role
    db.session.commit()
    return jsonify({"ok": True, "id": user.id, "role": user.role})

@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"ok": True})


# ------------------ Manage Events ------------------
@admin_bp.route("/events", methods=["GET"])
@jwt_required()
def list_events():
    events = Event.query.all()
    items = [
        {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "category": e.category,
            "date": e.date.isoformat() if e.date else None,
            "time": e.time,
            "location": e.location,
            "ticket_type": e.ticket_type,
            "status": e.status,
        } for e in events
    ]
    return jsonify({"items": items})

@admin_bp.route("/events/<int:event_id>/toggle", methods=["PATCH"])
@jwt_required()
def toggle_event_status(event_id):
    event = Event.query.get_or_404(event_id)
    event.status = "draft" if event.status == "published" else "published"
    db.session.commit()
    return jsonify({"ok": True, "id": event.id, "status": event.status})

@admin_bp.route("/events/<int:event_id>", methods=["DELETE"])
@jwt_required()
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({"ok": True})
