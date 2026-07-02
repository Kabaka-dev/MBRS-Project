"""
main.py — GUI Entry Point
Matatu Booking and Reservation System (MBRS)
CPP 3201 Python Programming — Group 1
KCA University, May-August 2026

A Tkinter-based Graphical User Interface implementing the design
specified in CAT 1: login, route listing, seat booking, cancellation,
no-show penalty engine, marshal manifest, and admin panel.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import data_store
import auth
import booking
import cancellation
import noshow
import manifest
import utils

BRAND = "#1A3C5E"
ACCENT = "#C0392B"
GOLD = "#D4AC0D"
LIGHT = "#EAF1FB"
GREEN = "#1E8449"
WHITE = "#FFFFFF"


class MBRSApp(tk.Tk):
    """Root application window — manages frame switching between screens."""

    def __init__(self):
        super().__init__()
        self.title("MBRS — Matatu Booking and Reservation System")
        self.geometry("960x640")
        self.minsize(900, 600)
        self.configure(bg=LIGHT)

        self.current_user = None  # {"username", "role", "name"}

        data_store.seed_data()

        self.container = tk.Frame(self, bg=LIGHT)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        self.show_frame(LoginFrame)

    def show_frame(self, frame_class, **kwargs):
        for widget in self.container.winfo_children():
            widget.destroy()
        frame = frame_class(self.container, self, **kwargs)
        frame.pack(fill="both", expand=True)


class HeaderBar(tk.Frame):
    """Reusable top header bar shown on every screen after login."""

    def __init__(self, parent, app, title):
        super().__init__(parent, bg=BRAND, height=60)
        self.app = app
        self.pack(fill="x", side="top")

        tk.Label(self, text="MBRS", font=("Arial", 18, "bold"), fg=GOLD, bg=BRAND).pack(
            side="left", padx=20, pady=10)
        tk.Label(self, text=title, font=("Arial", 14, "bold"), fg=WHITE, bg=BRAND).pack(
            side="left", padx=10, pady=10)

        if app.current_user:
            user_label = f"{app.current_user['name']}  ({app.current_user['role']})"
            tk.Label(self, text=user_label, font=("Arial", 10), fg=WHITE, bg=BRAND).pack(
                side="right", padx=10, pady=10)
            tk.Button(self, text="Logout", command=self.logout, bg=ACCENT, fg=WHITE,
                      relief="flat", padx=12).pack(side="right", padx=10, pady=10)

    def logout(self):
        self.app.current_user = None
        self.app.show_frame(LoginFrame)


# ─────────────────────────────────────────────────────────────────────────
# LOGIN / REGISTRATION
# ─────────────────────────────────────────────────────────────────────────
class LoginFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=LIGHT)
        self.app = app

        card = tk.Frame(self, bg=WHITE, padx=40, pady=40, highlightbackground=BRAND,
                         highlightthickness=2)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="MBRS", font=("Arial", 28, "bold"), fg=BRAND, bg=WHITE).pack()
        tk.Label(card, text="Matatu Booking and Reservation System", font=("Arial", 12),
                 fg="#555555", bg=WHITE).pack(pady=(0, 20))

        tk.Label(card, text="Phone Number / Username", font=("Arial", 10), bg=WHITE,
                 anchor="w").pack(fill="x")
        self.username_entry = tk.Entry(card, font=("Arial", 12), width=30)
        self.username_entry.pack(pady=(2, 12))

        tk.Label(card, text="Password", font=("Arial", 10), bg=WHITE, anchor="w").pack(fill="x")
        self.password_entry = tk.Entry(card, font=("Arial", 12), width=30, show="*")
        self.password_entry.pack(pady=(2, 20))

        tk.Button(card, text="Login", font=("Arial", 12, "bold"), bg=BRAND, fg=WHITE,
                  width=25, relief="flat", command=self.handle_login).pack(pady=4)
        tk.Button(card, text="Register New Passenger Account", font=("Arial", 10),
                  bg=LIGHT, fg=BRAND, relief="flat", command=self.show_register).pack(pady=8)

        tk.Label(card, text="Demo logins — Admin: admin/admin123  |  Passenger: 0700000000/pass123",
                 font=("Arial", 8), fg="#888888", bg=WHITE).pack(pady=(10, 0))

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Missing Input", "Please enter both username and password.")
            return
        success, role, name, msg = auth.authenticate(username, password)
        if not success:
            messagebox.showerror("Login Failed", msg)
            return
        self.app.current_user = {"username": username, "role": role, "name": name}
        if role == "Admin":
            self.app.show_frame(AdminDashboardFrame)
        else:
            self.app.show_frame(PassengerDashboardFrame)

    def show_register(self):
        self.app.show_frame(RegisterFrame)


class RegisterFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=LIGHT)
        self.app = app

        card = tk.Frame(self, bg=WHITE, padx=40, pady=30, highlightbackground=BRAND,
                         highlightthickness=2)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="Register New Passenger", font=("Arial", 18, "bold"), fg=BRAND,
                 bg=WHITE).pack(pady=(0, 16))

        self.name_entry = self._field(card, "Full Name")
        self.phone_entry = self._field(card, "Phone Number (07XXXXXXXX)")
        self.password_entry = self._field(card, "Password (min 6 characters)", show="*")

        tk.Button(card, text="Register", font=("Arial", 12, "bold"), bg=GREEN, fg=WHITE,
                  width=25, relief="flat", command=self.handle_register).pack(pady=10)
        tk.Button(card, text="Back to Login", font=("Arial", 10), bg=LIGHT, fg=BRAND,
                  relief="flat", command=lambda: app.show_frame(LoginFrame)).pack()

    def _field(self, parent, label, show=None):
        tk.Label(parent, text=label, font=("Arial", 10), bg=WHITE, anchor="w").pack(fill="x")
        entry = tk.Entry(parent, font=("Arial", 12), width=32, show=show)
        entry.pack(pady=(2, 10))
        return entry

    def handle_register(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        password = self.password_entry.get().strip()
        success, msg = auth.register_passenger_account(name, phone, password)
        if success:
            messagebox.showinfo("Registration Successful", msg)
            self.app.show_frame(LoginFrame)
        else:
            messagebox.showerror("Registration Failed", msg)


# ─────────────────────────────────────────────────────────────────────────
# PASSENGER DASHBOARD
# ─────────────────────────────────────────────────────────────────────────
class PassengerDashboardFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=LIGHT)
        self.app = app
        HeaderBar(self, app, "Passenger Dashboard")

        nav = tk.Frame(self, bg=LIGHT)
        nav.pack(fill="x", pady=10, padx=20)

        buttons = [
            ("View Routes & Book a Seat", BookingFrame, BRAND),
            ("Cancel a Booking", CancellationFrame, ACCENT),
            ("My Booking History", HistoryFrame, GREEN),
        ]
        for text, frame_cls, color in buttons:
            tk.Button(nav, text=text, font=("Arial", 11, "bold"), bg=color, fg=WHITE,
                      relief="flat", width=26, height=2,
                      command=lambda f=frame_cls: app.show_frame(f)).pack(side="left", padx=8)

        # Account status panel
        phone = app.current_user["username"]
        passenger = data_store.get_passenger_by_phone(phone)
        status_frame = tk.Frame(self, bg=WHITE, highlightbackground=BRAND, highlightthickness=1)
        status_frame.pack(fill="x", padx=20, pady=10)
        if passenger:
            tk.Label(status_frame, text=f"Account Status: {passenger.account_status}   |   "
                                          f"No-Show Count: {passenger.flag_count}   |   "
                                          f"Deposit Required: {'Yes' if passenger.deposit_required else 'No'}",
                     font=("Arial", 10, "bold"), bg=WHITE, fg=BRAND, pady=10).pack()
        else:
            tk.Label(status_frame, text="No passenger profile linked to this account yet.",
                     font=("Arial", 10), bg=WHITE, fg="#888888", pady=10).pack()


class BookingFrame(tk.Frame):
    """Route listing -> departure listing -> seat map -> confirm."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=LIGHT)
        self.app = app
        HeaderBar(self, app, "Book a Seat")
        self.selected_route = None
        self.selected_departure = None
        self.build_route_list()

    def clear_body(self):
        for w in self.winfo_children()[1:]:
            w.destroy()

    def build_route_list(self):
        self.clear_body()
        tk.Label(self, text="Available Routes", font=("Arial", 14, "bold"), bg=LIGHT,
                 fg=BRAND).pack(pady=10)

        cols = ("Route ID", "Origin", "Destination", "Fare (KSh)")
        tree = ttk.Treeview(self, columns=cols, show="headings", height=6)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=200, anchor="center")
        tree.pack(padx=20, pady=10, fill="x")

        for route in data_store.load_routes():
            tree.insert("", "end", values=(route.route_id, route.origin, route.destination, route.fare))

        def on_select(event):
            sel = tree.selection()
            if sel:
                route_id = tree.item(sel[0])["values"][0]
                routes = {r.route_id: r for r in data_store.load_routes()}
                self.selected_route = routes[route_id]
                self.build_departure_list()

        tree.bind("<<TreeviewSelect>>", on_select)
        tk.Label(self, text="Select a route above to view departure times.",
                 font=("Arial", 9), bg=LIGHT, fg="#666666").pack()
        tk.Button(self, text="Back to Dashboard", bg=LIGHT, fg=BRAND, relief="flat",
                  command=lambda: self.app.show_frame(PassengerDashboardFrame)).pack(pady=10)

    def build_departure_list(self):
        self.clear_body()
        tk.Label(self, text=f"Departures — {self.selected_route.route_id} "
                             f"({self.selected_route.origin} → {self.selected_route.destination})",
                 font=("Arial", 14, "bold"), bg=LIGHT, fg=BRAND).pack(pady=10)

        cols = ("Departure ID", "Time", "Date", "Seats Available")
        tree = ttk.Treeview(self, columns=cols, show="headings", height=6)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=200, anchor="center")
        tree.pack(padx=20, pady=10, fill="x")

        deps = data_store.get_departures_for_route(self.selected_route.route_id)
        for dep in deps:
            avail = dep.available_count()
            label = "FULL" if avail == 0 else str(avail)
            tree.insert("", "end", values=(dep.departure_id, dep.departure_time,
                                            dep.departure_date, label))

        def on_select(event):
            sel = tree.selection()
            if sel:
                dep_id = tree.item(sel[0])["values"][0]
                for d in deps:
                    if d.departure_id == dep_id:
                        if d.is_full():
                            messagebox.showinfo("Departure Full", "This departure is fully booked. "
                                                                    "Please choose another time slot.")
                            return
                        self.selected_departure = d
                        self.build_seat_map()
                        return

        tree.bind("<<TreeviewSelect>>", on_select)
        tk.Button(self, text="Back to Routes", bg=LIGHT, fg=BRAND, relief="flat",
                  command=self.build_route_list).pack(pady=10)

    def build_seat_map(self):
        self.clear_body()
        dep = self.selected_departure
        tk.Label(self, text=f"Select a Seat — {dep.departure_id}", font=("Arial", 14, "bold"),
                 bg=LIGHT, fg=BRAND).pack(pady=10)
        tk.Label(self, text="O = Open    X = Taken    W = Walk-in buffer (not bookable online)",
                 font=("Arial", 9), bg=LIGHT, fg="#666666").pack()

        grid = tk.Frame(self, bg=LIGHT)
        grid.pack(pady=20)

        for seat_no in range(1, 15):
            status = dep.seat_map.get(seat_no, "O")
            color = {"O": GREEN, "X": "#999999", "W": GOLD}[status]
            state = "normal" if status == "O" else "disabled"
            row, col = divmod(seat_no - 1, 2)
            btn = tk.Button(grid, text=f"{seat_no:02d}\n[{status}]", font=("Arial", 10, "bold"),
                             bg=color, fg=WHITE, width=8, height=3, state=state,
                             command=lambda s=seat_no: self.confirm_booking(s))
            btn.grid(row=row, column=col, padx=8, pady=6)

        tk.Button(self, text="Back to Departures", bg=LIGHT, fg=BRAND, relief="flat",
                  command=self.build_departure_list).pack(pady=10)

    def confirm_booking(self, seat_no):
        phone = self.app.current_user["username"]
        passenger = data_store.get_passenger_by_phone(phone)
        if not passenger:
            messagebox.showerror("Error", "No passenger profile found for this account.")
            return

        confirm = messagebox.askyesno(
            "Confirm Booking",
            f"Book seat {seat_no} on {self.selected_route.route_id} "
            f"({self.selected_departure.departure_time})?\n\nFare: KSh {self.selected_route.fare}"
        )
        if not confirm:
            return

        success, msg, ref_code = booking.create_booking(passenger, self.selected_departure, seat_no)
        if success:
            messagebox.showinfo(
                "Booking Confirmed",
                f"{msg}\n\nReference Code: {ref_code}\n"
                f"Seat: {seat_no}\nRoute: {self.selected_route.route_id}\n"
                f"Departure: {self.selected_departure.departure_time}\n\n"
                f"Present this reference code to the stage marshal at boarding."
            )
            self.app.show_frame(PassengerDashboardFrame)
        else:
            messagebox.showerror("Booking Failed", msg)


class CancellationFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=LIGHT)
        self.app = app
        HeaderBar(self, app, "Cancel a Booking")

        card = tk.Frame(self, bg=WHITE, padx=30, pady=30, highlightbackground=BRAND,
                         highlightthickness=1)
        card.pack(pady=40, padx=200, fill="x")

        tk.Label(card, text="Enter Booking Reference Code", font=("Arial", 12), bg=WHITE).pack(anchor="w")
        self.ref_entry = tk.Entry(card, font=("Arial", 12), width=40)
        self.ref_entry.pack(pady=10)

        tk.Button(card, text="Cancel Booking", font=("Arial", 12, "bold"), bg=ACCENT, fg=WHITE,
                  relief="flat", width=20, command=self.handle_cancel).pack(pady=10)

        tk.Button(self, text="Back to Dashboard", bg=LIGHT, fg=BRAND, relief="flat",
                  command=lambda: app.show_frame(PassengerDashboardFrame)).pack()

    def handle_cancel(self):
        ref_code = self.ref_entry.get().strip()
        if not ref_code:
            messagebox.showwarning("Missing Input", "Please enter a booking reference code.")
            return
        phone = self.app.current_user["username"]
        success, msg = cancellation.cancel_booking(ref_code, requesting_phone=phone)
        if success:
            messagebox.showinfo("Cancelled", msg)
            self.app.show_frame(PassengerDashboardFrame)
        else:
            messagebox.showerror("Cancellation Failed", msg)


class HistoryFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=LIGHT)
        self.app = app
        HeaderBar(self, app, "My Booking History")

        phone = app.current_user["username"]
        bookings = booking.get_passenger_history(phone)

        cols = ("Ref Code", "Departure", "Seat", "Status", "Fee (KSh)")
        tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=160, anchor="center")
        tree.pack(padx=20, pady=20, fill="both", expand=True)

        for b in bookings:
            tree.insert("", "end", values=(b.ref_code, b.departure_id, b.seat_no, b.status, b.booking_fee))

        if not bookings:
            tk.Label(self, text="No bookings yet.", bg=LIGHT, fg="#888888").pack()

        tk.Button(self, text="Back to Dashboard", bg=LIGHT, fg=BRAND, relief="flat",
                  command=lambda: app.show_frame(PassengerDashboardFrame)).pack(pady=10)


# ─────────────────────────────────────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────────────────────────────────────
class AdminDashboardFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=LIGHT)
        self.app = app
        HeaderBar(self, app, "Admin Dashboard")

        nav = tk.Frame(self, bg=LIGHT)
        nav.pack(fill="x", pady=10, padx=20)

        buttons = [
            ("Manage Routes", RouteAdminFrame, BRAND),
            ("View All Bookings", AllBookingsFrame, GREEN),
            ("Boarding Manifest", ManifestFrame, GOLD),
            ("Run No-Show Sweep", None, ACCENT),
        ]
        for text, frame_cls, color in buttons:
            if frame_cls:
                cmd = lambda f=frame_cls: app.show_frame(f)
            else:
                cmd = self.run_noshow_sweep
            tk.Button(nav, text=text, font=("Arial", 11, "bold"), bg=color, fg=WHITE,
                      relief="flat", width=22, height=2, command=cmd).pack(side="left", padx=6)

    def run_noshow_sweep(self):
        deps = data_store.load_departures()
        all_results = []
        for d in deps:
            all_results.extend(noshow.check_noshow_for_departure(d.departure_id))
        if not all_results:
            messagebox.showinfo("No-Show Sweep", "No eligible no-shows found at this time "
                                                   "(grace period not yet elapsed for active departures).")
        else:
            lines = "\n".join(f"{ref} — {name}: {msg}" for ref, name, msg in all_results)
            messagebox.showinfo("No-Show Sweep Complete", lines)


class RouteAdminFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=LIGHT)
        self.app = app
        HeaderBar(self, app, "Manage Routes")

        cols = ("Route ID", "Origin", "Destination", "Stage", "Fare")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=8)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=170, anchor="center")
        self.tree.pack(padx=20, pady=20, fill="both", expand=True)
        self.refresh()

        btns = tk.Frame(self, bg=LIGHT)
        btns.pack(pady=10)
        tk.Button(btns, text="Add Route", bg=GREEN, fg=WHITE, relief="flat", width=15,
                  command=self.add_route).pack(side="left", padx=5)
        tk.Button(btns, text="Back to Admin Dashboard", bg=LIGHT, fg=BRAND, relief="flat",
                  command=lambda: app.show_frame(AdminDashboardFrame)).pack(side="left", padx=5)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in data_store.load_routes():
            self.tree.insert("", "end", values=(r.route_id, r.origin, r.destination, r.stage_name, r.fare))

    def add_route(self):
        route_id = simpledialog.askstring("Route ID", "Enter new Route ID (e.g. RT-005):")
        if not route_id:
            return
        origin = simpledialog.askstring("Origin", "Enter origin point:") or ""
        destination = simpledialog.askstring("Destination", "Enter destination:") or ""
        stage = simpledialog.askstring("Stage Name", "Enter stage name:") or ""
        fare = simpledialog.askinteger("Fare", "Enter fare in KSh:") or 0

        from models import Route
        routes = data_store.load_routes()
        routes.append(Route(route_id, origin, destination, stage, fare))
        data_store.save_routes(routes)
        self.refresh()
        messagebox.showinfo("Route Added", f"Route {route_id} added successfully.")


class AllBookingsFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=LIGHT)
        self.app = app
        HeaderBar(self, app, "All Bookings")

        cols = ("Ref Code", "Passenger ID", "Departure", "Seat", "Status", "Fee")
        tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=150, anchor="center")
        tree.pack(padx=20, pady=20, fill="both", expand=True)

        for b in data_store.load_bookings():
            tree.insert("", "end", values=(b.ref_code, b.passenger_id, b.departure_id,
                                            b.seat_no, b.status, b.booking_fee))

        tk.Button(self, text="Back to Admin Dashboard", bg=LIGHT, fg=BRAND, relief="flat",
                  command=lambda: app.show_frame(AdminDashboardFrame)).pack(pady=10)


class ManifestFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=LIGHT)
        self.app = app
        HeaderBar(self, app, "Boarding Manifest")

        top = tk.Frame(self, bg=LIGHT)
        top.pack(pady=10)
        tk.Label(top, text="Select Departure ID:", bg=LIGHT, font=("Arial", 11)).pack(side="left", padx=5)

        deps = data_store.load_departures()
        dep_ids = [d.departure_id for d in deps]
        self.dep_var = tk.StringVar(value=dep_ids[0] if dep_ids else "")
        dropdown = ttk.Combobox(top, textvariable=self.dep_var, values=dep_ids, width=40, state="readonly")
        dropdown.pack(side="left", padx=5)
        tk.Button(top, text="Load Manifest", bg=BRAND, fg=WHITE, relief="flat",
                  command=self.load_manifest).pack(side="left", padx=5)

        cols = ("Seat", "Name", "Phone", "Ref Code", "Status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=160, anchor="center")
        self.tree.pack(padx=20, pady=10, fill="both", expand=True)

        self.summary_label = tk.Label(self, text="", bg=LIGHT, font=("Arial", 10, "bold"), fg=BRAND)
        self.summary_label.pack(pady=5)

        btns = tk.Frame(self, bg=LIGHT)
        btns.pack(pady=10)
        tk.Button(btns, text="Mark Selected as Boarded", bg=GREEN, fg=WHITE, relief="flat",
                  command=self.mark_boarded).pack(side="left", padx=5)
        tk.Button(btns, text="Back to Admin Dashboard", bg=LIGHT, fg=BRAND, relief="flat",
                  command=lambda: app.show_frame(AdminDashboardFrame)).pack(side="left", padx=5)

    def load_manifest(self):
        dep_id = self.dep_var.get()
        for row in self.tree.get_children():
            self.tree.delete(row)
        mf = manifest.generate_manifest(dep_id)
        for entry in mf:
            self.tree.insert("", "end", values=(entry["seat_no"], entry["name"], entry["phone"],
                                                   entry["ref_code"], entry["status"]))
        summary = manifest.manifest_summary(mf)
        self.summary_label.config(
            text=f"Total Booked: {summary['total']}  |  Boarded: {summary['boarded']}  |  "
                 f"Pending: {summary['pending']}  |  No-Show: {summary['no_show']}"
        )

    def mark_boarded(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a passenger row first.")
            return
        ref_code = self.tree.item(sel[0])["values"][3]
        success, msg = manifest.mark_boarded(ref_code)
        if success:
            messagebox.showinfo("Checked In", msg)
            self.load_manifest()
        else:
            messagebox.showerror("Error", msg)


if __name__ == "__main__":
    app = MBRSApp()
    app.mainloop()
