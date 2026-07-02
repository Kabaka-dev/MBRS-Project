"""
utils.py — Shared Utility Module
Matatu Booking and Reservation System (MBRS)
CPP 3201 Python Programming — Group 1

Provides shared helper functions used across all other modules:
CSV I/O, validation, timestamp formatting.
"""

import csv
import os
import re
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def ensure_data_dir():
    """Create the data directory if it does not already exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def read_csv(filename):
    """
    Read a CSV file from the data directory.
    Returns a list of dictionaries (one per row).
    Returns an empty list if the file does not exist.
    """
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def write_csv(filename, rows, headers):
    """
    Write a list of dictionaries to a CSV file in the data directory.
    Overwrites any existing file.
    """
    ensure_data_dir()
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def append_csv_row(filename, row, headers):
    """Append a single row to a CSV file, creating it with headers if needed."""
    ensure_data_dir()
    filepath = os.path.join(DATA_DIR, filename)
    file_exists = os.path.exists(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def validate_phone(phone):
    """
    Validate a Kenyan phone number.
    Accepts formats: 07XXXXXXXX, 01XXXXXXXX, or +2547XXXXXXXX / +2541XXXXXXXX
    """
    phone = phone.strip().replace(" ", "")
    pattern = r"^(0[71]\d{8}|\+254[71]\d{8})$"
    return bool(re.match(pattern, phone))


def validate_name(name):
    """Validate that a name contains only letters and spaces, 2-60 chars."""
    name = name.strip()
    if not (2 <= len(name) <= 60):
        return False
    return bool(re.match(r"^[A-Za-z ]+$", name))


def validate_date(date_str):
    """Validate a date string in DD/MM/YYYY format."""
    try:
        datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def get_timestamp():
    """Return the current date and time as a formatted string."""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def get_today_date():
    """Return today's date as DD/MM/YYYY."""
    return datetime.now().strftime("%d/%m/%Y")


def parse_datetime(date_str, time_str):
    """Combine a DD/MM/YYYY date string and HH:MM time string into a datetime object."""
    return datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")


def hash_password(password):
    """
    Simple SHA-256 password hash (academic prototype — not for production use).
    """
    import hashlib
    return hashlib.sha256(password.encode("utf-8")).hexdigest()
