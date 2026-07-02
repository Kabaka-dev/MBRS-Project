"""
data_store.py — Central Data Access Layer
Matatu Booking and Reservation System (MBRS)

Loads/saves all CSV-backed data and seeds initial demo data
(4 Nairobi routes, sample departures) on first run.
"""

import os
import json
import utils
from models import Passenger, Booking, Route, Departure, MatatuVehicle

ROUTES_FILE = "routes.csv"
DEPARTURES_FILE = "departures.csv"
PASSENGERS_FILE = "passengers.csv"
BOOKINGS_FILE = "bookings.csv"
SUBSCRIPTIONS_FILE = "subscriptions.csv"
TRANSACTIONS_FILE = "transactions.csv"
USERS_FILE = "users.json"

ROUTES_HEADERS = ["route_id", "origin", "destination", "stage_name", "fare", "active"]
DEPARTURES_HEADERS = ["departure_id", "route_id", "departure_time", "departure_date", "seat_map"]
PASSENGERS_HEADERS = ["passenger_id", "name", "phone", "flag_count", "account_status",
                       "cooldown_until", "deposit_required", "surcharge_bookings_left",
                       "registration_date"]
BOOKINGS_HEADERS = ["ref_code", "passenger_id", "departure_id", "seat_no", "status",
                     "booking_fee", "deposit_paid", "created_at"]
SUBSCRIPTIONS_HEADERS = ["sub_id", "sacco_name", "route_id", "plan", "amount_kshs", "start_date"]
TRANSACTIONS_HEADERS = ["txn_id", "ref_code", "passenger_id", "amount", "type", "timestamp"]


def seed_data():
    """Seed demo data on first run: 4 Nairobi routes + departures + an admin user."""
    utils.ensure_data_dir()
    users_path = os.path.join(utils.DATA_DIR, USERS_FILE)

    if not os.path.exists(users_path):
        users = {
            "admin": {
                "name": "MBRS Administrator",
                "password_hash": utils.hash_password("admin123"),
                "role": "Admin"
            },
            "0700000000": {
                "name": "Demo Passenger",
                "password_hash": utils.hash_password("pass123"),
                "role": "Passenger"
            }
        }
        with open(users_path, "w") as f:
            json.dump(users, f, indent=2)

    if not utils.read_csv(ROUTES_FILE):
        routes = [
            Route("RT-001", "CBD (Koja Bus Stop)", "Kasarani", "Koja Stage", 60),
            Route("RT-002", "CBD (OTC)", "Umoja / Kayole (Eastlands)", "OTC Stage", 50),
            Route("RT-003", "CBD (Kencom)", "Ngong Road (Dagoretti Corner)", "Kencom Stage", 70),
            Route("RT-004", "CBD (Ngara)", "Thika Road (Roysambu)", "Ngara Stage", 55),
        ]
        utils.write_csv(ROUTES_FILE, [r.to_dict() for r in routes], ROUTES_HEADERS)

    if not utils.read_csv(DEPARTURES_FILE):
        today = utils.get_today_date()
        slots = ["06:30", "07:15", "08:00", "17:00", "18:30"]
        departures = []
        for route in ["RT-001", "RT-002", "RT-003", "RT-004"]:
            for t in slots:
                dep_id = f"DEP-{route}-{today.replace('/', '')}-{t.replace(':', '')}"
                departures.append(Departure(dep_id, route, t, today))
        utils.write_csv(DEPARTURES_FILE, [d.to_dict() for d in departures], DEPARTURES_HEADERS)

    if not utils.read_csv(PASSENGERS_FILE):
        utils.write_csv(PASSENGERS_FILE, [], PASSENGERS_HEADERS)

    if not utils.read_csv(BOOKINGS_FILE):
        utils.write_csv(BOOKINGS_FILE, [], BOOKINGS_HEADERS)

    if not utils.read_csv(SUBSCRIPTIONS_FILE):
        subs = [
            {"sub_id": "SUB-001", "sacco_name": "Metro Trans SACCO", "route_id": "RT-001",
             "plan": "Standard", "amount_kshs": 3000, "start_date": today_str()},
            {"sub_id": "SUB-002", "sacco_name": "Eastlands Shuttle SACCO", "route_id": "RT-002",
             "plan": "Premium", "amount_kshs": 5000, "start_date": today_str()},
        ]
        utils.write_csv(SUBSCRIPTIONS_FILE, subs, SUBSCRIPTIONS_HEADERS)

    if not utils.read_csv(TRANSACTIONS_FILE):
        utils.write_csv(TRANSACTIONS_FILE, [], TRANSACTIONS_HEADERS)


def today_str():
    return utils.get_today_date()


# ── Routes ────────────────────────────────────────────────────────────────
def load_routes():
    return [Route.from_dict(r) for r in utils.read_csv(ROUTES_FILE)]


def save_routes(routes):
    utils.write_csv(ROUTES_FILE, [r.to_dict() for r in routes], ROUTES_HEADERS)


# ── Departures ───────────────────────────────────────────────────────────
def load_departures():
    return [Departure.from_dict(d) for d in utils.read_csv(DEPARTURES_FILE)]


def save_departures(departures):
    utils.write_csv(DEPARTURES_FILE, [d.to_dict() for d in departures], DEPARTURES_HEADERS)


def get_departures_for_route(route_id):
    return [d for d in load_departures() if d.route_id == route_id]


def get_departure_by_id(departure_id):
    for d in load_departures():
        if d.departure_id == departure_id:
            return d
    return None


# ── Passengers ───────────────────────────────────────────────────────────
def load_passengers():
    return [Passenger.from_dict(p) for p in utils.read_csv(PASSENGERS_FILE)]


def save_passengers(passengers):
    utils.write_csv(PASSENGERS_FILE, [p.to_dict() for p in passengers], PASSENGERS_HEADERS)


def get_passenger_by_phone(phone):
    for p in load_passengers():
        if p.phone == phone:
            return p
    return None


def get_passenger_by_id(passenger_id):
    for p in load_passengers():
        if p.passenger_id == passenger_id:
            return p
    return None


# ── Bookings ─────────────────────────────────────────────────────────────
def load_bookings():
    return [Booking.from_dict(b) for b in utils.read_csv(BOOKINGS_FILE)]


def save_bookings(bookings):
    utils.write_csv(BOOKINGS_FILE, [b.to_dict() for b in bookings], BOOKINGS_HEADERS)


def get_booking_by_ref(ref_code):
    for b in load_bookings():
        if b.ref_code == ref_code:
            return b
    return None


# ── Transactions ─────────────────────────────────────────────────────────
def log_transaction(ref_code, passenger_id, amount, txn_type):
    txns = utils.read_csv(TRANSACTIONS_FILE)
    txn_id = f"TXN-{len(txns) + 1:05d}"
    utils.append_csv_row(TRANSACTIONS_FILE, {
        "txn_id": txn_id, "ref_code": ref_code, "passenger_id": passenger_id,
        "amount": amount, "type": txn_type, "timestamp": utils.get_timestamp()
    }, TRANSACTIONS_HEADERS)


# ── Users / Auth ─────────────────────────────────────────────────────────
def load_users():
    users_path = os.path.join(utils.DATA_DIR, USERS_FILE)
    if not os.path.exists(users_path):
        return {}
    with open(users_path) as f:
        return json.load(f)


def save_users(users):
    users_path = os.path.join(utils.DATA_DIR, USERS_FILE)
    with open(users_path, "w") as f:
        json.dump(users, f, indent=2)


def register_user(username, name, password, role="Passenger"):
    users = load_users()
    users[username] = {
        "name": name,
        "password_hash": utils.hash_password(password),
        "role": role
    }
    save_users(users)
