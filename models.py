"""
models.py — Core Data Model Classes
Matatu Booking and Reservation System (MBRS)
CPP 3201 Python Programming — Group 1

Defines the five core classes used throughout the system:
Passenger, Booking, Route, Departure, MatatuVehicle.
"""

import utils


class Passenger:
    """Represents a registered passenger, including penalty-tracking fields."""

    def __init__(self, passenger_id, name, phone, flag_count=0,
                 account_status="ACTIVE", cooldown_until="", deposit_required=False,
                 surcharge_bookings_left=0, registration_date=None):
        self.passenger_id = passenger_id
        self.name = name
        self.phone = phone
        self.flag_count = int(flag_count)
        self.account_status = account_status          # ACTIVE | FROZEN | SUSPENDED
        self.cooldown_until = cooldown_until           # datetime string or ""
        self.deposit_required = self._to_bool(deposit_required)
        self.surcharge_bookings_left = int(surcharge_bookings_left)
        self.registration_date = registration_date or utils.get_timestamp()

    @staticmethod
    def _to_bool(value):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("true", "1", "yes")

    def is_suspended(self):
        return self.account_status == "SUSPENDED"

    def is_frozen(self):
        if not self.cooldown_until:
            return False
        try:
            from datetime import datetime
            return datetime.now() < datetime.strptime(self.cooldown_until, "%d/%m/%Y %H:%M:%S")
        except ValueError:
            return False

    def to_dict(self):
        return {
            "passenger_id": self.passenger_id,
            "name": self.name,
            "phone": self.phone,
            "flag_count": self.flag_count,
            "account_status": self.account_status,
            "cooldown_until": self.cooldown_until,
            "deposit_required": self.deposit_required,
            "surcharge_bookings_left": self.surcharge_bookings_left,
            "registration_date": self.registration_date,
        }

    @staticmethod
    def from_dict(row):
        return Passenger(
            passenger_id=row["passenger_id"],
            name=row["name"],
            phone=row["phone"],
            flag_count=row.get("flag_count", 0),
            account_status=row.get("account_status", "ACTIVE"),
            cooldown_until=row.get("cooldown_until", ""),
            deposit_required=row.get("deposit_required", False),
            surcharge_bookings_left=row.get("surcharge_bookings_left", 0),
            registration_date=row.get("registration_date"),
        )


class Booking:
    """Represents a single seat booking transaction."""

    STATUSES = ["CONFIRMED", "CANCELLED", "NO-SHOW", "BOARDED"]

    def __init__(self, ref_code, passenger_id, departure_id, seat_no,
                 booking_fee, deposit_paid=0, status="CONFIRMED", created_at=None):
        self.ref_code = ref_code
        self.passenger_id = passenger_id
        self.departure_id = departure_id
        self.seat_no = int(seat_no)
        self.status = status
        self.booking_fee = int(booking_fee)
        self.deposit_paid = int(deposit_paid)
        self.created_at = created_at or utils.get_timestamp()

    def cancel(self):
        """Voluntary cancellation — never touches passenger flag_count."""
        self.status = "CANCELLED"

    def mark_noshow(self):
        """Used only by the automated no-show engine."""
        self.status = "NO-SHOW"

    def mark_boarded(self):
        self.status = "BOARDED"

    def to_dict(self):
        return {
            "ref_code": self.ref_code,
            "passenger_id": self.passenger_id,
            "departure_id": self.departure_id,
            "seat_no": self.seat_no,
            "status": self.status,
            "booking_fee": self.booking_fee,
            "deposit_paid": self.deposit_paid,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(row):
        return Booking(
            ref_code=row["ref_code"],
            passenger_id=row["passenger_id"],
            departure_id=row["departure_id"],
            seat_no=row["seat_no"],
            booking_fee=row["booking_fee"],
            deposit_paid=row.get("deposit_paid", 0),
            status=row.get("status", "CONFIRMED"),
            created_at=row.get("created_at"),
        )


class Route:
    """Represents a matatu route / corridor."""

    def __init__(self, route_id, origin, destination, stage_name, fare, active=True):
        self.route_id = route_id
        self.origin = origin
        self.destination = destination
        self.stage_name = stage_name
        self.fare = int(fare)
        self.active = active if isinstance(active, bool) else str(active).lower() == "true"

    def to_dict(self):
        return {
            "route_id": self.route_id,
            "origin": self.origin,
            "destination": self.destination,
            "stage_name": self.stage_name,
            "fare": self.fare,
            "active": self.active,
        }

    @staticmethod
    def from_dict(row):
        return Route(
            route_id=row["route_id"],
            origin=row["origin"],
            destination=row["destination"],
            stage_name=row["stage_name"],
            fare=row["fare"],
            active=row.get("active", True),
        )


class Departure:
    """Represents one scheduled departure slot for a route, including its seat map."""

    TOTAL_SEATS = 14
    WALK_IN_BUFFER = 2

    def __init__(self, departure_id, route_id, departure_time, departure_date, seat_map=None):
        self.departure_id = departure_id
        self.route_id = route_id
        self.departure_time = departure_time
        self.departure_date = departure_date
        self.total_seats = self.TOTAL_SEATS
        self.walk_in_seats = self.WALK_IN_BUFFER

        if seat_map:
            self.seat_map = seat_map
        else:
            self.seat_map = {i: "O" for i in range(1, self.TOTAL_SEATS + 1)}
            # Reserve the last two seats as walk-in buffer
            self.seat_map[self.TOTAL_SEATS - 1] = "W"
            self.seat_map[self.TOTAL_SEATS] = "W"

    def available_count(self):
        return sum(1 for s in self.seat_map.values() if s == "O")

    def is_full(self):
        return self.available_count() == 0

    def seat_map_to_str(self):
        """Serialise the seat map dict to a compact string for CSV storage, e.g. '1:O,2:X,3:O'."""
        return ",".join(f"{seat}:{status}" for seat, status in sorted(self.seat_map.items()))

    @staticmethod
    def seat_map_from_str(s):
        result = {}
        if not s:
            return result
        for pair in s.split(","):
            seat, status = pair.split(":")
            result[int(seat)] = status
        return result

    def to_dict(self):
        return {
            "departure_id": self.departure_id,
            "route_id": self.route_id,
            "departure_time": self.departure_time,
            "departure_date": self.departure_date,
            "seat_map": self.seat_map_to_str(),
        }

    @staticmethod
    def from_dict(row):
        seat_map = Departure.seat_map_from_str(row.get("seat_map", ""))
        return Departure(
            departure_id=row["departure_id"],
            route_id=row["route_id"],
            departure_time=row["departure_time"],
            departure_date=row["departure_date"],
            seat_map=seat_map if seat_map else None,
        )


class MatatuVehicle:
    """Represents a physical matatu vehicle assigned to a route."""

    def __init__(self, vehicle_id, route_id, sacco_name, capacity=14, active=True):
        self.vehicle_id = vehicle_id
        self.route_id = route_id
        self.sacco_name = sacco_name
        self.capacity = int(capacity)
        self.active = active if isinstance(active, bool) else str(active).lower() == "true"

    def to_dict(self):
        return {
            "vehicle_id": self.vehicle_id,
            "route_id": self.route_id,
            "sacco_name": self.sacco_name,
            "capacity": self.capacity,
            "active": self.active,
        }

    @staticmethod
    def from_dict(row):
        return MatatuVehicle(
            vehicle_id=row["vehicle_id"],
            route_id=row["route_id"],
            sacco_name=row["sacco_name"],
            capacity=row.get("capacity", 14),
            active=row.get("active", True),
        )
