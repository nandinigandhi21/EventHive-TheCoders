from flask import Blueprint, request, jsonify
from models import db, Event

event_bp = Blueprint("event", __name__)

# ------------------ CREATE EVENT ------------------
@event_bp.route("/api/events/create", methods=["POST"])
def create_event():
    try:
        data = request.get_json()

        new_event = Event(
            title=data["title"],
            description=data.get("description"),
            category=data["category"],
            date=data["date"],
            time=data["time"],
            location=data["location"],
            ticket_type=data["ticket_type"],
            price=float(data["price"]),
            max_quantity=int(data["max_quantity"]),
            status=data["status"],
            organizer_id=int(data["organizer_id"])
        )

        db.session.add(new_event)
        db.session.commit()

        return jsonify({"message": "Event created successfully!", "event": new_event.to_dict()}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ------------------ FETCH MY EVENTS ------------------
@event_bp.route("/api/events/my-events/<int:organizer_id>", methods=["GET"])
def get_my_events(organizer_id):
    try:
        events = Event.query.filter_by(organizer_id=organizer_id).all()
        return jsonify([event.to_dict() for event in events]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ------------------ DELETE EVENT ------------------
@event_bp.route("/api/events/delete/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({"error": "Event not found"}), 404

        db.session.delete(event)
        db.session.commit()
        return jsonify({"message": "Event deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
