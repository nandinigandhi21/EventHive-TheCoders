from flask import Blueprint, request, jsonify
from models import db, Event, User

# Create Blueprint
create_event_bp = Blueprint("create_event", __name__)

# ========================
# 1️⃣ Create Event
# ========================
@create_event_bp.route("/events/create", methods=["POST"])
def create_event():
    data = request.json

    try:
        # Required fields
        title = data.get("title")
        category = data.get("category")
        date = data.get("date")
        time = data.get("time")
        location = data.get("location")
        ticket_type = data.get("ticket_type")
        price = data.get("price")
        max_quantity = data.get("max_quantity")
        organizer_id = data.get("organizer_id")

        if not all([title, category, date, time, location, ticket_type, price, max_quantity, organizer_id]):
            return jsonify({"error": "Missing required fields"}), 400

        # Check if organizer exists
        organizer = User.query.get(organizer_id)
        if not organizer or organizer.role != "organizer":
            return jsonify({"error": "Invalid organizer"}), 400

        # Create event
        new_event = Event(
            title=title,
            description=data.get("description", ""),
            category=category,
            date=date,
            time=time,
            location=location,
            ticket_type=ticket_type,
            price=float(price),
            max_quantity=int(max_quantity),
            organizer_id=organizer_id,
            status="draft"
        )

        db.session.add(new_event)
        db.session.commit()

        return jsonify({"message": "Event created successfully", "event": new_event.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ========================
# 2️⃣ Get Events by Organizer
# ========================
@create_event_bp.route("/events/<int:organizer_id>", methods=["GET"])
def get_events_by_organizer(organizer_id):
    try:
        events = Event.query.filter_by(organizer_id=organizer_id).all()
        return jsonify([event.to_dict() for event in events]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
