# backend/routes/admin.py
from flask import Blueprint, jsonify
from models import db, User, Event
from sqlalchemy import func

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

@admin_bp.route("/stats", methods=["GET"])
def get_stats():
    # Users
    total_users = User.query.count()
    organizers = User.query.filter_by(role="organizer").count()
    attendees = User.query.filter_by(role="attendee").count()
    admins = User.query.filter_by(role="admin").count()

    # Events
    total_events = Event.query.count()
    published_events = Event.query.filter_by(status="published").count()

    # Tickets + Revenue (using Event table for now)
    tickets_sold = db.session.query(func.sum(Event.max_quantity)).scalar() or 0
    revenue = db.session.query(func.sum(Event.price * Event.max_quantity)).scalar() or 0

    # Categories distribution
    category_counts = db.session.query(Event.category, func.count(Event.id)).group_by(Event.category).all()
    categories = {cat: count for cat, count in category_counts}

    # Fake timeseries (replace with real analytics later)
    timeseries = {
        "days": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
        "signups": [12, 25, 18, 30, 22, 40, 28],
        "bookings": [10, 15, 12, 18, 20, 25, 30]
    }

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
        "timeseries": timeseries,
        "categories": categories
    })
