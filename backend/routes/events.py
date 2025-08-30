# routes/events.py
from flask import Blueprint, request, jsonify
from models import db, Event

events_bp = Blueprint("events", __name__)

# ---------------- Attendee: Browse All Published Events ---------------- #
@events_bp.route("/all", methods=["GET"])
def get_all_events():
    """Return only published events for attendees"""
    events = Event.query.filter_by(status="Published").all()
    return jsonify([event.to_dict() for event in events]), 200
