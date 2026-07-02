"""
booking.py — Seat Booking Module
Matatu Booking and Reservation System (MBRS)
"""

import utils
import data_store
from models import Booking


def calculate_fee(passenger):
    """Determine the booking fee based on the passenger's current penalty tier."""
    base_fee = 10
    if passenger.surcharge_bookings_left > 0:
        return 40  # doubled fee for 2nd-offence surcharge window
    return base_fee


def calculate_deposit(passenger):
    """Return the required deposit amount (0 if not required)."""
    return 100 if passenger.deposit_required else 0


def check_account_restrictions(passenger):
    """
    Check whether a passenger is currently allowed to book.
    Returns (allowed: bool, reason: str)
    """
    if passenger.is_suspended():
        return False, "Your account is SUSPENDED. Please contact an administrator to reinstate it."
    if passenger.is_frozen():
        return False, f"Your account is on a booking freeze until {passenger.cooldown_until}."
    return True, ""


def generate_ref_code(route_id, departure_date, seat_no):
    """
    Generate a unique booking reference code.

    BUG FIX (Assignment 3): route_id values such as 'RT-001' already contain
    a hyphen. The earlier version produced codes like 'MBRS-RT-001-20260617-05',
    which broke any code that tried to split the reference on '-' to extract
    fields, since 'RT-001' contributes two segments instead of one. The
    route_id is now wrapped in square brackets so it can be located
    unambiguously regardless of how many hyphens it contains.
    """
    parts = departure_date.split("/")
    date_compact = parts[2] + parts[1] + parts[0] if len(parts) == 3 else departure_date.replace("/", "")
    return f"MBRS-[{route_id}]-{date_compact}-{int(seat_no):02d}"


def parse_ref_code(ref_code):
    """
    Safely parse a reference code back into its components.
    Returns (route_id, date_compact, seat_no) or None if malformed.
    """
    try:
        _, rest = ref_code.split("-[", 1)
        route_id, remainder = rest.split("]-", 1)
        date_compact, seat_str = remainder.rsplit("-", 1)
        return route_id, date_compact, int(seat_str)
    except (ValueError, IndexError):
        return None


def create_booking(passenger, departure, seat_no):
    """
    Create a new CONFIRMED booking for a passenger on a given departure and seat.
    Returns (success: bool, message: str, ref_code: str or None)
    """
    allowed, reason = check_account_restrictions(passenger)
    if not allowed:
        return False, reason, None

    if departure.seat_map.get(int(seat_no)) != "O":
        return False, "Selected seat is not available.", None

    fee = calculate_fee(passenger)
    deposit = calculate_deposit(passenger)

    ref_code = generate_ref_code(departure.route_id, departure.departure_date, seat_no)

    booking = Booking(ref_code, passenger.passenger_id, departure.departure_id,
                       seat_no, fee, deposit)

    # Update seat map
    departure.seat_map[int(seat_no)] = "X"
    departures = data_store.load_departures()
    departures = [departure if d.departure_id == departure.departure_id else d for d in departures]
    data_store.save_departures(departures)

    # Save booking
    bookings = data_store.load_bookings()
    bookings.append(booking)
    data_store.save_bookings(bookings)

    # Decrement surcharge counter if applicable
    if passenger.surcharge_bookings_left > 0:
        passenger.surcharge_bookings_left -= 1
        passengers = data_store.load_passengers()
        passengers = [passenger if p.passenger_id == passenger.passenger_id else p for p in passengers]
        data_store.save_passengers(passengers)

    # Log transaction(s)
    data_store.log_transaction(ref_code, passenger.passenger_id, fee, "BOOKING_FEE")
    if deposit > 0:
        data_store.log_transaction(ref_code, passenger.passenger_id, deposit, "DEPOSIT")

    return True, "Booking confirmed successfully.", ref_code


def get_passenger_history(phone):
    """Return all bookings made by the passenger with the given phone number."""
    passenger = data_store.get_passenger_by_phone(phone)
    if not passenger:
        return []
    return [b for b in data_store.load_bookings() if b.passenger_id == passenger.passenger_id]
