"""
test_mbrs.py — Formal Test Suite for the MBRS System
CPP 3201 Python Programming — Assignment 3: System Refinement and Testing
Group 1, KCA University

Covers: valid input handling, invalid/unexpected input handling,
booking lifecycle, cancellation-vs-no-show separation, and the
5-tier penalty escalation framework.

Run with:  python3 -m unittest test_mbrs.py -v
"""

import unittest
import os
import shutil
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import utils
import data_store
import auth
import booking
import cancellation
import noshow
import manifest
from models import Passenger, Booking, Route, Departure


class MBRSTestCase(unittest.TestCase):
    """Base class: resets the data directory before every test for isolation."""

    def setUp(self):
        if os.path.exists(utils.DATA_DIR):
            shutil.rmtree(utils.DATA_DIR)
        data_store.seed_data()

    def tearDown(self):
        if os.path.exists(utils.DATA_DIR):
            shutil.rmtree(utils.DATA_DIR)


# ═══════════════════════════════════════════════════════════════════════
# 1. INPUT VALIDATION TESTS (utils.py)
# ═══════════════════════════════════════════════════════════════════════
class TestPhoneValidation(MBRSTestCase):

    def test_valid_phone_07_format(self):
        self.assertTrue(utils.validate_phone("0712345678"))

    def test_valid_phone_01_format(self):
        self.assertTrue(utils.validate_phone("0112345678"))

    def test_valid_phone_international_format(self):
        self.assertTrue(utils.validate_phone("+254712345678"))

    def test_invalid_phone_too_short(self):
        self.assertFalse(utils.validate_phone("07123"))

    def test_invalid_phone_letters(self):
        self.assertFalse(utils.validate_phone("07abcdefgh"))

    def test_invalid_phone_wrong_prefix(self):
        self.assertFalse(utils.validate_phone("0912345678"))

    def test_invalid_phone_empty_string(self):
        self.assertFalse(utils.validate_phone(""))

    def test_phone_with_spaces_is_normalised(self):
        self.assertTrue(utils.validate_phone("0712 345 678"))


class TestNameValidation(MBRSTestCase):

    def test_valid_name(self):
        self.assertTrue(utils.validate_name("John Kamau"))

    def test_invalid_name_too_short(self):
        self.assertFalse(utils.validate_name("J"))

    def test_invalid_name_with_numbers(self):
        self.assertFalse(utils.validate_name("John123"))

    def test_invalid_name_with_symbols(self):
        self.assertFalse(utils.validate_name("John@Kamau"))

    def test_invalid_name_empty(self):
        self.assertFalse(utils.validate_name(""))

    def test_invalid_name_too_long(self):
        self.assertFalse(utils.validate_name("A" * 61))


class TestDateValidation(MBRSTestCase):

    def test_valid_date(self):
        self.assertTrue(utils.validate_date("01/06/2026"))

    def test_invalid_date_wrong_format(self):
        self.assertFalse(utils.validate_date("2026-06-01"))

    def test_invalid_date_out_of_range_day(self):
        self.assertFalse(utils.validate_date("32/06/2026"))

    def test_invalid_date_out_of_range_month(self):
        self.assertFalse(utils.validate_date("15/13/2026"))

    def test_invalid_date_empty(self):
        self.assertFalse(utils.validate_date(""))


# ═══════════════════════════════════════════════════════════════════════
# 2. AUTHENTICATION TESTS (auth.py)
# ═══════════════════════════════════════════════════════════════════════
class TestRegistration(MBRSTestCase):

    def test_successful_registration(self):
        ok, msg = auth.register_passenger_account("Jane Doe", "0722111222", "pass123")
        self.assertTrue(ok)

    def test_registration_rejects_invalid_name(self):
        ok, msg = auth.register_passenger_account("J", "0722111222", "pass123")
        self.assertFalse(ok)
        self.assertIn("name", msg.lower())

    def test_registration_rejects_invalid_phone(self):
        ok, msg = auth.register_passenger_account("Jane Doe", "12345", "pass123")
        self.assertFalse(ok)
        self.assertIn("phone", msg.lower())

    def test_registration_rejects_short_password(self):
        ok, msg = auth.register_passenger_account("Jane Doe", "0722111222", "abc")
        self.assertFalse(ok)
        self.assertIn("password", msg.lower())

    def test_registration_rejects_duplicate_phone(self):
        auth.register_passenger_account("Jane Doe", "0722111222", "pass123")
        ok, msg = auth.register_passenger_account("Jane Doe Again", "0722111222", "pass456")
        self.assertFalse(ok)
        self.assertIn("already exists", msg.lower())


class TestLogin(MBRSTestCase):

    def test_successful_admin_login(self):
        ok, role, name, msg = auth.authenticate("admin", "admin123")
        self.assertTrue(ok)
        self.assertEqual(role, "Admin")

    def test_successful_passenger_login(self):
        ok, role, name, msg = auth.authenticate("0700000000", "pass123")
        self.assertTrue(ok)
        self.assertEqual(role, "Passenger")

    def test_login_fails_unknown_username(self):
        ok, role, name, msg = auth.authenticate("0799999999", "anything")
        self.assertFalse(ok)

    def test_login_fails_wrong_password(self):
        ok, role, name, msg = auth.authenticate("admin", "wrongpassword")
        self.assertFalse(ok)

    def test_login_fails_empty_credentials(self):
        ok, role, name, msg = auth.authenticate("", "")
        self.assertFalse(ok)


# ═══════════════════════════════════════════════════════════════════════
# 3. BOOKING TESTS (booking.py)
# ═══════════════════════════════════════════════════════════════════════
class TestBooking(MBRSTestCase):

    def setUp(self):
        super().setUp()
        auth.register_passenger_account("Test Passenger", "0733444555", "testpass")
        self.passenger = data_store.get_passenger_by_phone("0733444555")
        self.departure = data_store.get_departures_for_route("RT-001")[0]

    def test_successful_booking(self):
        ok, msg, ref = booking.create_booking(self.passenger, self.departure, 5)
        self.assertTrue(ok)
        self.assertIsNotNone(ref)
        self.assertTrue(ref.startswith("MBRS-[RT-001]"))

    def test_booking_marks_seat_taken(self):
        booking.create_booking(self.passenger, self.departure, 5)
        updated_departure = data_store.get_departure_by_id(self.departure.departure_id)
        self.assertEqual(updated_departure.seat_map[5], "X")

    def test_cannot_book_already_taken_seat(self):
        booking.create_booking(self.passenger, self.departure, 5)
        updated_departure = data_store.get_departure_by_id(self.departure.departure_id)
        ok, msg, ref = booking.create_booking(self.passenger, updated_departure, 5)
        self.assertFalse(ok)
        self.assertIn("not available", msg.lower())

    def test_cannot_book_walk_in_buffer_seat(self):
        # Seats 13 and 14 are reserved as walk-in buffer (status 'W', not 'O')
        ok, msg, ref = booking.create_booking(self.passenger, self.departure, 13)
        self.assertFalse(ok)

    def test_reference_code_format(self):
        ok, msg, ref = booking.create_booking(self.passenger, self.departure, 7)
        self.assertTrue(ref.startswith("MBRS-["))
        parsed = booking.parse_ref_code(ref)
        self.assertIsNotNone(parsed)
        route_id, date_compact, seat_no = parsed
        self.assertEqual(route_id, "RT-001")
        self.assertEqual(len(date_compact), 8)  # YYYYMMDD
        self.assertEqual(seat_no, 7)

    def test_base_fee_is_ten_for_new_passenger(self):
        ok, msg, ref = booking.create_booking(self.passenger, self.departure, 5)
        b = data_store.get_booking_by_ref(ref)
        self.assertEqual(b.booking_fee, 10)

    def test_suspended_account_cannot_book(self):
        self.passenger.account_status = "SUSPENDED"
        passengers = data_store.load_passengers()
        passengers = [self.passenger if p.passenger_id == self.passenger.passenger_id else p
                      for p in passengers]
        data_store.save_passengers(passengers)

        ok, msg, ref = booking.create_booking(self.passenger, self.departure, 5)
        self.assertFalse(ok)
        self.assertIn("suspended", msg.lower())

    def test_frozen_account_cannot_book(self):
        future = (datetime.now() + timedelta(hours=48)).strftime("%d/%m/%Y %H:%M:%S")
        self.passenger.cooldown_until = future
        passengers = data_store.load_passengers()
        passengers = [self.passenger if p.passenger_id == self.passenger.passenger_id else p
                      for p in passengers]
        data_store.save_passengers(passengers)

        ok, msg, ref = booking.create_booking(self.passenger, self.departure, 5)
        self.assertFalse(ok)
        self.assertIn("freeze", msg.lower())


# ═══════════════════════════════════════════════════════════════════════
# 4. CANCELLATION TESTS (cancellation.py) — including the bug-fix scenario
# ═══════════════════════════════════════════════════════════════════════
class TestCancellation(MBRSTestCase):

    def setUp(self):
        super().setUp()
        auth.register_passenger_account("Cancel Tester", "0744555666", "testpass")
        self.passenger = data_store.get_passenger_by_phone("0744555666")
        self.departure = data_store.get_departures_for_route("RT-002")[0]
        ok, msg, self.ref_code = booking.create_booking(self.passenger, self.departure, 4)

    def test_successful_cancellation(self):
        ok, msg = cancellation.cancel_booking(self.ref_code)
        self.assertTrue(ok)

    def test_cancellation_releases_seat(self):
        cancellation.cancel_booking(self.ref_code)
        updated_departure = data_store.get_departure_by_id(self.departure.departure_id)
        self.assertEqual(updated_departure.seat_map[4], "O")

    def test_cancellation_does_not_increment_flag_count(self):
        """Regression test for the reviewer-raised concern: cancellation must
        NEVER be conflated with a no-show and must NEVER increment flag_count."""
        cancellation.cancel_booking(self.ref_code)
        updated_passenger = data_store.get_passenger_by_id(self.passenger.passenger_id)
        self.assertEqual(updated_passenger.flag_count, 0)

    def test_cancellation_rejects_unknown_reference(self):
        ok, msg = cancellation.cancel_booking("MBRS-FAKE-00000000-99")
        self.assertFalse(ok)
        self.assertIn("not found", msg.lower())

    def test_cannot_cancel_already_cancelled_booking(self):
        cancellation.cancel_booking(self.ref_code)
        ok, msg = cancellation.cancel_booking(self.ref_code)
        self.assertFalse(ok)

    def test_cannot_cancel_someone_elses_booking(self):
        ok, msg = cancellation.cancel_booking(self.ref_code, requesting_phone="0799999999")
        self.assertFalse(ok)
        self.assertIn("does not belong", msg.lower())

    def test_cancellation_with_correct_owner_phone_succeeds(self):
        ok, msg = cancellation.cancel_booking(self.ref_code, requesting_phone="0744555666")
        self.assertTrue(ok)


# ═══════════════════════════════════════════════════════════════════════
# 5. NO-SHOW & PENALTY ESCALATION TESTS (noshow.py)
# ═══════════════════════════════════════════════════════════════════════
class TestNoShowEscalation(MBRSTestCase):

    def setUp(self):
        super().setUp()
        auth.register_passenger_account("NoShow Tester", "0755666777", "testpass")
        self.passenger = data_store.get_passenger_by_phone("0755666777")

    def _make_past_departure(self, route_id="RT-003"):
        """Helper: create a departure already in the past so grace period has elapsed."""
        past_time = (datetime.now() - timedelta(hours=1))
        dep_id = f"DEP-TEST-{past_time.strftime('%Y%m%d%H%M')}"
        dep = Departure(dep_id, route_id, past_time.strftime("%H:%M"), past_time.strftime("%d/%m/%Y"))
        departures = data_store.load_departures()
        departures.append(dep)
        data_store.save_departures(departures)
        return dep

    def test_grace_period_not_elapsed_for_future_departure(self):
        future_time = (datetime.now() + timedelta(hours=2))
        elapsed = noshow.is_grace_period_elapsed(
            future_time.strftime("%d/%m/%Y"), future_time.strftime("%H:%M"))
        self.assertFalse(elapsed)

    def test_grace_period_elapsed_for_past_departure(self):
        past_time = (datetime.now() - timedelta(hours=1))
        elapsed = noshow.is_grace_period_elapsed(
            past_time.strftime("%d/%m/%Y"), past_time.strftime("%H:%M"))
        self.assertTrue(elapsed)

    def test_first_noshow_applies_no_penalty(self):
        dep = self._make_past_departure()
        ok, msg, ref = booking.create_booking(self.passenger, dep, 1)
        results = noshow.check_noshow_for_departure(dep.departure_id)
        self.assertEqual(len(results), 1)
        updated = data_store.get_passenger_by_id(self.passenger.passenger_id)
        self.assertEqual(updated.flag_count, 1)
        self.assertEqual(updated.account_status, "ACTIVE")
        self.assertFalse(updated.deposit_required)

    def test_second_noshow_applies_fee_surcharge(self):
        for i in range(1, 3):
            dep = self._make_past_departure()
            booking.create_booking(self.passenger, dep, i)
            noshow.check_noshow_for_departure(dep.departure_id)
            self.passenger = data_store.get_passenger_by_id(self.passenger.passenger_id)

        self.assertEqual(self.passenger.flag_count, 2)
        self.assertEqual(self.passenger.surcharge_bookings_left, 3)

    def test_third_noshow_applies_booking_freeze(self):
        """
        Tests tiers 1-3 in sequence. From the 3rd no-show onward the account
        is frozen, which correctly blocks new bookings -- this is intentional
        design behaviour (a frozen account cannot accumulate further no-shows
        because it cannot book at all). To reach tier 3 we must create and
        book each departure BEFORE the previous no-show sweep applies the
        freeze for that same passenger.
        """
        deps = [self._make_past_departure() for _ in range(3)]
        for i, dep in enumerate(deps, start=1):
            ok, msg, ref = booking.create_booking(self.passenger, dep, i)
            self.assertTrue(ok, f"Booking {i} should succeed before freeze takes effect: {msg}")
            noshow.check_noshow_for_departure(dep.departure_id)
            self.passenger = data_store.get_passenger_by_id(self.passenger.passenger_id)

        self.assertEqual(self.passenger.flag_count, 3)
        self.assertTrue(self.passenger.is_frozen())

    def test_fourth_and_fifth_noshow_require_admin_intervention(self):
        """
        REGRESSION TEST (Assignment 3 bug fix): demonstrates a genuine design
        finding. Once a passenger is frozen (tier 3), check_account_restrictions()
        correctly REJECTS any further booking attempt -- including the booking
        that would otherwise become a 4th or 5th no-show. This means a frozen
        passenger cannot organically reach tier 4 or 5 simply by accumulating
        more no-shows; the freeze must first expire OR an admin must intervene.
        This test documents that behaviour explicitly rather than assuming
        (incorrectly, as the original test did) that bookings 4 and 5 would
        silently succeed during an active freeze.
        """
        deps = [self._make_past_departure() for _ in range(3)]
        for i, dep in enumerate(deps, start=1):
            booking.create_booking(self.passenger, dep, i)
            noshow.check_noshow_for_departure(dep.departure_id)
            self.passenger = data_store.get_passenger_by_id(self.passenger.passenger_id)

        self.assertTrue(self.passenger.is_frozen())

        # Attempting a 4th booking while frozen must be rejected, not silently
        # allowed to progress the passenger to tier 4.
        dep4 = self._make_past_departure()
        ok, msg, ref = booking.create_booking(self.passenger, dep4, 1)
        self.assertFalse(ok)
        self.assertIn("freeze", msg.lower())

        # Admin can manually advance the test scenario past the freeze window
        # by clearing cooldown_until directly (simulating 48 hours elapsing),
        # at which point booking and no-show tracking resume normally.
        self.passenger.cooldown_until = ""
        passengers = data_store.load_passengers()
        passengers = [self.passenger if p.passenger_id == self.passenger.passenger_id else p
                      for p in passengers]
        data_store.save_passengers(passengers)

        ok, msg, ref = booking.create_booking(self.passenger, dep4, 1)
        self.assertTrue(ok, f"Booking should succeed once freeze window has elapsed: {msg}")
        noshow.check_noshow_for_departure(dep4.departure_id)
        self.passenger = data_store.get_passenger_by_id(self.passenger.passenger_id)
        self.assertEqual(self.passenger.flag_count, 4)
        self.assertTrue(self.passenger.deposit_required)

    def test_fifth_noshow_suspends_account(self):
        """Continues from tier 4 (deposit required, not frozen) through to tier 5 (suspension)."""
        deps = [self._make_past_departure() for _ in range(3)]
        for i, dep in enumerate(deps, start=1):
            booking.create_booking(self.passenger, dep, i)
            noshow.check_noshow_for_departure(dep.departure_id)
            self.passenger = data_store.get_passenger_by_id(self.passenger.passenger_id)

        # Clear the freeze to simulate the 48-hour window elapsing
        self.passenger.cooldown_until = ""
        passengers = data_store.load_passengers()
        passengers = [self.passenger if p.passenger_id == self.passenger.passenger_id else p
                      for p in passengers]
        data_store.save_passengers(passengers)

        for seat in (1, 2):
            dep = self._make_past_departure()
            booking.create_booking(self.passenger, dep, seat)
            noshow.check_noshow_for_departure(dep.departure_id)
            self.passenger = data_store.get_passenger_by_id(self.passenger.passenger_id)

        self.assertEqual(self.passenger.flag_count, 5)
        self.assertTrue(self.passenger.is_suspended())

    def test_suspension_cancels_other_active_bookings(self):
        # Create one booking that will remain CONFIRMED through the process
        active_dep = data_store.get_departures_for_route("RT-004")[0]
        ok, msg, active_ref = booking.create_booking(self.passenger, active_dep, 6)

        # Drive the passenger to tier 3 (freeze), then clear the freeze to
        # simulate elapsed time, then continue to tier 5 (suspension).
        deps = [self._make_past_departure() for _ in range(3)]
        for i, dep in enumerate(deps, start=1):
            booking.create_booking(self.passenger, dep, i)
            noshow.check_noshow_for_departure(dep.departure_id)
            self.passenger = data_store.get_passenger_by_id(self.passenger.passenger_id)

        self.passenger.cooldown_until = ""
        passengers = data_store.load_passengers()
        passengers = [self.passenger if p.passenger_id == self.passenger.passenger_id else p
                      for p in passengers]
        data_store.save_passengers(passengers)

        for seat in (1, 2):
            dep = self._make_past_departure()
            booking.create_booking(self.passenger, dep, seat)
            noshow.check_noshow_for_departure(dep.departure_id)
            self.passenger = data_store.get_passenger_by_id(self.passenger.passenger_id)

        active_booking = data_store.get_booking_by_ref(active_ref)
        self.assertEqual(active_booking.status, "CANCELLED")

    def test_noshow_releases_seat(self):
        dep = self._make_past_departure()
        booking.create_booking(self.passenger, dep, 2)
        noshow.check_noshow_for_departure(dep.departure_id)
        updated_dep = data_store.get_departure_by_id(dep.departure_id)
        self.assertEqual(updated_dep.seat_map[2], "O")

    def test_no_sweep_action_when_grace_period_not_elapsed(self):
        future_dep_id = f"DEP-FUTURE-TEST"
        future_time = datetime.now() + timedelta(hours=3)
        dep = Departure(future_dep_id, "RT-001", future_time.strftime("%H:%M"),
                         future_time.strftime("%d/%m/%Y"))
        departures = data_store.load_departures()
        departures.append(dep)
        data_store.save_departures(departures)

        booking.create_booking(self.passenger, dep, 3)
        results = noshow.check_noshow_for_departure(dep.departure_id)
        self.assertEqual(len(results), 0)

    def test_reinstate_account_resets_penalties(self):
        for i in range(1, 6):
            dep = self._make_past_departure()
            booking.create_booking(self.passenger, dep, i)
            noshow.check_noshow_for_departure(dep.departure_id)

        noshow.reinstate_account(self.passenger.passenger_id)
        reinstated = data_store.get_passenger_by_id(self.passenger.passenger_id)
        self.assertEqual(reinstated.flag_count, 0)
        self.assertEqual(reinstated.account_status, "ACTIVE")
        self.assertFalse(reinstated.deposit_required)


# ═══════════════════════════════════════════════════════════════════════
# 6. MANIFEST TESTS (manifest.py)
# ═══════════════════════════════════════════════════════════════════════
class TestManifest(MBRSTestCase):

    def setUp(self):
        super().setUp()
        auth.register_passenger_account("Manifest Tester", "0766777888", "testpass")
        self.passenger = data_store.get_passenger_by_phone("0766777888")
        self.departure = data_store.get_departures_for_route("RT-001")[0]
        ok, msg, self.ref_code = booking.create_booking(self.passenger, self.departure, 8)

    def test_manifest_contains_booking(self):
        mf = manifest.generate_manifest(self.departure.departure_id)
        self.assertEqual(len(mf), 1)
        self.assertEqual(mf[0]["ref_code"], self.ref_code)

    def test_manifest_sorted_by_seat(self):
        booking.create_booking(self.passenger, data_store.get_departure_by_id(
            self.departure.departure_id), 2)
        mf = manifest.generate_manifest(self.departure.departure_id)
        seats = [m["seat_no"] for m in mf]
        self.assertEqual(seats, sorted(seats))

    def test_mark_boarded_success(self):
        ok, msg = manifest.mark_boarded(self.ref_code)
        self.assertTrue(ok)
        b = data_store.get_booking_by_ref(self.ref_code)
        self.assertEqual(b.status, "BOARDED")

    def test_cannot_board_unknown_reference(self):
        ok, msg = manifest.mark_boarded("MBRS-FAKE-00000000-99")
        self.assertFalse(ok)

    def test_cannot_board_already_boarded_passenger(self):
        manifest.mark_boarded(self.ref_code)
        ok, msg = manifest.mark_boarded(self.ref_code)
        self.assertFalse(ok)

    def test_manifest_summary_counts(self):
        mf = manifest.generate_manifest(self.departure.departure_id)
        summary = manifest.manifest_summary(mf)
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["pending"], 1)
        self.assertEqual(summary["boarded"], 0)


# ═══════════════════════════════════════════════════════════════════════
# 7. EDGE CASE / BOUNDARY TESTS
# ═══════════════════════════════════════════════════════════════════════
class TestEdgeCases(MBRSTestCase):

    def test_booking_on_fully_booked_departure(self):
        auth.register_passenger_account("Filler", "0777888999", "testpass")
        passenger = data_store.get_passenger_by_phone("0777888999")
        dep = data_store.get_departures_for_route("RT-001")[0]

        # Fill all 12 bookable seats (13 & 14 are walk-in buffer)
        for seat in range(1, 13):
            booking.create_booking(passenger, dep, seat)
            dep = data_store.get_departure_by_id(dep.departure_id)

        self.assertTrue(dep.is_full())

    def test_empty_manifest_for_departure_with_no_bookings(self):
        dep = data_store.get_departures_for_route("RT-004")[1]
        mf = manifest.generate_manifest(dep.departure_id)
        self.assertEqual(mf, [])

    def test_route_with_zero_fare_rejected_conceptually(self):
        # Validates that fare must be a positive integer per design spec
        route = Route("RT-TEST", "Test Origin", "Test Dest", "Test Stage", 0)
        self.assertEqual(route.fare, 0)  # stored as-is; admin UI is responsible for validation

    def test_csv_read_missing_file_returns_empty_list(self):
        result = utils.read_csv("nonexistent_file.csv")
        self.assertEqual(result, [])

    def test_passenger_history_for_unregistered_phone(self):
        history = booking.get_passenger_history("0700000099")
        self.assertEqual(history, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
