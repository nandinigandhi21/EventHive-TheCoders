def normalize_phone(phone: int):
    return (phone or "").strip()

def valid_role(role: str) -> bool:
    return role in ("attendee", "organizer")
