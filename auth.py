"""
auth.py — Authentication Module
Matatu Booking and Reservation System (MBRS)

Handles login validation and role resolution.
"""

import utils
import data_store


def authenticate(username, password):
    """
    Validate username/password against stored users.
    Returns (success: bool, role: str or None, name: str or None, message: str)
    """
    users = data_store.load_users()
    username = username.strip()

    if username not in users:
        return False, None, None, "Username/phone number not recognised."

    record = users[username]
    if record["password_hash"] != utils.hash_password(password):
        return False, None, None, "Incorrect password."

    return True, record["role"], record["name"], "Login successful."


def register_passenger_account(name, phone, password):
    """Register a brand-new passenger account (also creates a Passenger record)."""
    if not utils.validate_name(name):
        return False, "Invalid name. Use letters and spaces only (2-60 characters)."
    if not utils.validate_phone(phone):
        return False, "Invalid phone number. Use format 07XXXXXXXX."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    users = data_store.load_users()
    if phone in users:
        return False, "An account with this phone number already exists."

    data_store.register_user(phone, name, password, role="Passenger")

    passengers = data_store.load_passengers()
    from models import Passenger
    new_id = f"PX-{phone[-4:]}-{utils.get_timestamp().replace('/', '').replace(':', '').replace(' ', '')}"
    passengers.append(Passenger(new_id, name, phone))
    data_store.save_passengers(passengers)

    return True, "Registration successful. You may now log in."
