"""
manifest.py — Marshal Boarding Manifest Module
Matatu Booking and Reservation System (MBRS)
"""

import data_store


def generate_manifest(departure_id):
    """
    Build the boarding manifest for a given departure: all bookings
    (CONFIRMED, BOARDED, NO-SHOW), sorted by seat number.
    Returns a list of dicts with passenger and booking details.
    """
    bookings = [b for b in data_store.load_bookings() if b.departure_id == departure_id]
    bookings.sort(key=lambda b: b.seat_no)

    manifest = []
    for b in bookings:
        passenger = data_store.get_passenger_by_id(b.passenger_id)
        manifest.append({
            "seat_no": b.seat_no,
            "name": passenger.name if passenger else "Unknown",
            "phone": passenger.phone if passenger else "Unknown",
            "ref_code": b.ref_code,
            "status": b.status,
        })
    return manifest


def mark_boarded(ref_code):
    """Update a booking's status from CONFIRMED to BOARDED (marshal check-in)."""
    booking = data_store.get_booking_by_ref(ref_code)
    if not booking:
        return False, "Booking not found."
    if booking.status != "CONFIRMED":
        return False, f"Cannot board — booking status is {booking.status}."
    booking.mark_boarded()
    bookings = data_store.load_bookings()
    bookings = [booking if b.ref_code == ref_code else b for b in bookings]
    data_store.save_bookings(bookings)
    return True, f"Passenger checked in for seat {booking.seat_no}."


def manifest_summary(manifest):
    """Compute summary counts for a manifest list."""
    total = len(manifest)
    boarded = sum(1 for m in manifest if m["status"] == "BOARDED")
    confirmed = sum(1 for m in manifest if m["status"] == "CONFIRMED")
    noshow = sum(1 for m in manifest if m["status"] == "NO-SHOW")
    return {"total": total, "boarded": boarded, "pending": confirmed, "no_show": noshow}
