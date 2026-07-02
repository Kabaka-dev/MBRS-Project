"""
cancellation.py — Voluntary Booking Cancellation Module
Matatu Booking and Reservation System (MBRS)

IMPORTANT: A voluntary cancellation here is entirely separate from a
no-show (see noshow.py). Cancelling NEVER increments flag_count and
NEVER applies any penalty.
"""

import data_store


def cancel_booking(ref_code, requesting_phone=None):
    """
    Cancel a CONFIRMED booking by reference code.
    Returns (success: bool, message: str)
    """
    booking = data_store.get_booking_by_ref(ref_code)
    if not booking:
        return False, "Booking reference code not found."

    if requesting_phone:
        passenger = data_store.get_passenger_by_id(booking.passenger_id)
        if not passenger or passenger.phone != requesting_phone:
            return False, "This booking does not belong to your account."

    if booking.status != "CONFIRMED":
        return False, f"This booking cannot be cancelled (current status: {booking.status})."

    booking.cancel()  # status -> CANCELLED, no flag_count change

    bookings = data_store.load_bookings()
    bookings = [booking if b.ref_code == ref_code else b for b in bookings]
    data_store.save_bookings(bookings)

    # Release the seat
    departure = data_store.get_departure_by_id(booking.departure_id)
    if departure:
        departure.seat_map[booking.seat_no] = "O"
        departures = data_store.load_departures()
        departures = [departure if d.departure_id == departure.departure_id else d for d in departures]
        data_store.save_departures(departures)

    return True, f"Booking {ref_code} cancelled. Seat {booking.seat_no} released. No penalty applied."
