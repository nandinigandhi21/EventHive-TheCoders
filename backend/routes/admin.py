# backend/routes/admin.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, cast, Date
from backend.models import db, User, Event, Ticket

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# ------------------ Dashboard Metrics ------------------
@admin_bp.route("/metrics", methods=["GET"])
@jwt_required()
def get_metrics():
    try:
        # Totals
        total_users = User.query.count()
        organizers = User.query.filter_by(role="organizer").count()
        total_events = Event.query.count()
        published_events = Event.query.filter_by(status="published").count()
        tickets_sold = db.session.query(func.coalesce(func.sum(Ticket.quantity), 0)).scalar()
        revenue = db.session.query(func.coalesce(func.sum(Ticket.price * Ticket.quantity), 0)).scalar()

        # --- Timeseries (last 7 days signups + bookings) ---
        signup_data = (
            db.session.query(cast(User.created_at, Date), func.count(User.id))
            .group_by(cast(User.created_at, Date))
            .order_by(cast(User.created_at, Date))
            .all()
        )
        booking_data = (
            db.session.query(cast(Ticket.created_at, Date), func.coalesce(func.sum(Ticket.quantity), 0))
            .group_by(cast(Ticket.created_at, Date))
            .order_by(cast(Ticket.created_at, Date))
            .all()
        )

        signup_dict = {str(day): count for day, count in signup_data}
        booking_dict = {str(day): count for day, count in booking_data}

        days = sorted(set(signup_dict.keys()) | set(booking_dict.keys()))
        timeseries = {
            "days": days,
            "signups": [signup_dict.get(d, 0) for d in days],
            "bookings": [booking_dict.get(d, 0) for d in days],
        }

        # --- Categories ---
        category_data = (
            db.session.query(Event.category, func.count(Event.id))
            .group_by(Event.category)
            .all()
        )
        categories = {c or "Uncategorized": count for c, count in category_data}

        return jsonify({
            "ok": True,
            "totals": {
                "users": total_users,
                "organizers": organizers,
                "events": total_events,
                "published": published_events,
                "ticketsSold": tickets_sold,
                "revenue": revenue,
            },
            "timeseries": timeseries,
            "categories": categories,
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
        }
        for u in users
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
        }
        for e in events
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
