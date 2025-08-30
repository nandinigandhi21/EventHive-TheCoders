# routes/events.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Event

events_bp = Blueprint("events", __name__)

# ---------------- Attendee: Browse All Published Events ---------------- #
@events_bp.route("/all", methods=["GET"])
def get_all_events():
    """Return only published events for attendees"""
    events = Event.query.filter_by(status="Published").all()
    return jsonify([event.to_dict() for event in events]), 200


# ---------------- Organizer: View My Events ---------------- #
@events_bp.route("/my-events", methods=["GET"])
@jwt_required()
def get_my_events():
    """Return all events created by the logged-in organizer (Draft + Published)"""
    user = get_jwt_identity()
    organizer_id = user["id"]

    events = Event.query.filter_by(organizer_id=organizer_id).all()
    return jsonify([event.to_dict() for event in events]), 200


# ---------------- Organizer: Publish / Unpublish Event ---------------- #
@events_bp.route("/publish/<int:event_id>", methods=["PUT"])
@jwt_required()
def publish_event(event_id):
    """Publish or unpublish an event (only by its organizer)"""
    user = get_jwt_identity()
    organizer_id = user["id"]

    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    # check ownership
    if event.organizer_id != organizer_id:
        return jsonify({"error": "Not authorized"}), 403

    data = request.get_json() or {}
    new_status = data.get("status", "Published")

    if new_status not in ["Published", "Draft"]:
        return jsonify({"error": "Invalid status"}), 400

    event.status = new_status
    db.session.commit()

    return jsonify({"msg": f"Event {new_status}", "event": event.to_dict()}), 200
