"""
noshow.py — No-Show Detection & Penalty Escalation Engine
Matatu Booking and Reservation System (MBRS)

Implements the 5-tier penalty escalation framework:
  1st no-show -> Warning only
  2nd no-show -> Booking fee surcharge (next 3 bookings doubled)
  3rd no-show -> 48-hour booking freeze
  4th no-show -> KSh 100 refundable deposit required per booking
  5th+ no-show -> Account suspended for 14 days
"""

from datetime import datetime, timedelta
import data_store


GRACE_PERIOD_MINUTES = 10


def is_grace_period_elapsed(departure_date, departure_time):
    """Check whether the grace period after a departure's scheduled time has elapsed."""
    dep_dt = datetime.strptime(f"{departure_date} {departure_time}", "%d/%m/%Y %H:%M")
    grace_end = dep_dt + timedelta(minutes=GRACE_PERIOD_MINUTES)
    return datetime.now() >= grace_end


def apply_penalty(passenger):
    """Apply the correct penalty tier based on the passenger's updated flag_count."""
    tier_message = ""
    if passenger.flag_count == 1:
        tier_message = "First no-show recorded. No penalty applied. Account flagged for monitoring."
    elif passenger.flag_count == 2:
        passenger.surcharge_bookings_left = 3
        tier_message = "Second no-show. Booking fee surcharge applied: next 3 bookings cost KSh 40 each."
    elif passenger.flag_count == 3:
        passenger.cooldown_until = (datetime.now() + timedelta(hours=48)).strftime("%d/%m/%Y %H:%M:%S")
        tier_message = "Third no-show. Account frozen from new bookings for 48 hours."
    elif passenger.flag_count == 4:
        passenger.deposit_required = True
        tier_message = "Fourth no-show. A KSh 100 refundable deposit is now required per booking."
    elif passenger.flag_count >= 5:
        passenger.account_status = "SUSPENDED"
        tier_message = "Fifth no-show. Account SUSPENDED for 14 days. Contact admin to reinstate."
    return tier_message


def auto_cancel_booking(booking):
    """Mark a booking as NO-SHOW, release its seat, and apply the penalty escalation."""
    booking.mark_noshow()
    bookings = data_store.load_bookings()
    bookings = [booking if b.ref_code == booking.ref_code else b for b in bookings]
    data_store.save_bookings(bookings)

    departure = data_store.get_departure_by_id(booking.departure_id)
    if departure:
        departure.seat_map[booking.seat_no] = "O"
        departures = data_store.load_departures()
        departures = [departure if d.departure_id == departure.departure_id else d for d in departures]
        data_store.save_departures(departures)

    passenger = data_store.get_passenger_by_id(booking.passenger_id)
    message = ""
    if passenger:
        passenger.flag_count += 1
        message = apply_penalty(passenger)

        # If suspended, cancel all other active bookings for this passenger
        if passenger.is_suspended():
            all_bookings = data_store.load_bookings()
            for b in all_bookings:
                if b.passenger_id == passenger.passenger_id and b.status == "CONFIRMED":
                    b.cancel()
                    dep = data_store.get_departure_by_id(b.departure_id)
                    if dep:
                        dep.seat_map[b.seat_no] = "O"
                        deps = data_store.load_departures()
                        deps = [dep if d.departure_id == dep.departure_id else d for d in deps]
                        data_store.save_departures(deps)
            data_store.save_bookings(all_bookings)

        passengers = data_store.load_passengers()
        passengers = [passenger if p.passenger_id == passenger.passenger_id else p for p in passengers]
        data_store.save_passengers(passengers)

    return message


def check_noshow_for_departure(departure_id):
    """
    Run the no-show sweep for a single departure: find all CONFIRMED bookings
    whose grace period has elapsed and auto-cancel them.
    Returns a list of (ref_code, passenger_name, penalty_message) tuples.
    """
    departure = data_store.get_departure_by_id(departure_id)
    if not departure:
        return []

    if not is_grace_period_elapsed(departure.departure_date, departure.departure_time):
        return []

    results = []
    bookings = data_store.load_bookings()
    for booking in bookings:
        if booking.departure_id == departure_id and booking.status == "CONFIRMED":
            passenger = data_store.get_passenger_by_id(booking.passenger_id)
            name = passenger.name if passenger else "Unknown"
            message = auto_cancel_booking(booking)
            results.append((booking.ref_code, name, message))

    return results


def reinstate_account(passenger_id):
    """Admin action: lift a suspension and reset the passenger's flag_count to 0."""
    passengers = data_store.load_passengers()
    for p in passengers:
        if p.passenger_id == passenger_id:
            p.account_status = "ACTIVE"
            p.flag_count = 0
            p.cooldown_until = ""
            p.deposit_required = False
            p.surcharge_bookings_left = 0
    data_store.save_passengers(passengers)
