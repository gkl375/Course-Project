"""
Staff tab: CRUD for Staff records (ID from utils.generate_staff_id) and same-day
check-in / check-out. Attendance rows are stored on Store and persisted with other JSON data.
"""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Optional

import utils
from models import Staff

from .center_window import center_toplevel


def create_staff_tab(self):
    """Create staff and attendance tab."""
    frame = ttk.Frame(self.notebook)
    self.notebook.add(frame, text="🧑‍💼 Staff")

    search_bar = ttk.Frame(frame)
    search_bar.pack(fill=tk.X, padx=5, pady=(5, 0))
    ttk.Label(search_bar, text="Search staff:").pack(side=tk.LEFT)
    self.staff_search_entry = ttk.Entry(search_bar, width=30)
    self.staff_search_entry.pack(side=tk.LEFT, padx=5)
    ttk.Button(
        search_bar, text="Search", command=self.search_staff_tab
    ).pack(side=tk.LEFT, padx=2)
    ttk.Button(
        search_bar, text="Clear", command=self.clear_staff_search
    ).pack(side=tk.LEFT, padx=2)

    top = ttk.LabelFrame(frame, text="Staff information", padding=10)
    top.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    self.staff_tree = ttk.Treeview(
        top,
        columns=("ID", "Name", "Role", "Phone", "Email", "In", "Out", "Status"),
        height=9,
        show="headings",
    )
    self.staff_tree.column("ID", width=90)
    self.staff_tree.column("Name", width=130)
    self.staff_tree.column("Role", width=110)
    self.staff_tree.column("Phone", width=100)
    self.staff_tree.column("Email", width=160)
    self.staff_tree.column("In", width=70)
    self.staff_tree.column("Out", width=70)
    self.staff_tree.column("Status", width=100)
    self.staff_tree.heading("ID", text="Staff ID")
    self.staff_tree.heading("Name", text="Name")
    self.staff_tree.heading("Role", text="Role")
    self.staff_tree.heading("Phone", text="Phone")
    self.staff_tree.heading("Email", text="Email")
    self.staff_tree.heading("In", text="Today In")
    self.staff_tree.heading("Out", text="Today Out")
    self.staff_tree.heading("Status", text="Status")
    self.staff_tree.pack(fill=tk.BOTH, expand=True)
    self.staff_tree.bind(
        "<<TreeviewSelect>>",
        lambda e: self.refresh_selected_staff_attendance(),
    )

    btn = ttk.Frame(frame)
    btn.pack(fill=tk.X, padx=5, pady=5)
    ttk.Button(btn, text="➕ Add staff", command=self.add_new_staff).pack(
        side=tk.LEFT, padx=5
    )
    ttk.Button(btn, text="✏️ Edit selected", command=self.modify_staff).pack(
        side=tk.LEFT, padx=5
    )
    self.staff_check_toggle_btn = ttk.Button(
        btn, text="🟢 Check in", command=self.staff_check_toggle
    )
    self.staff_check_toggle_btn.pack(side=tk.LEFT, padx=5)

    logf = ttk.LabelFrame(frame, text="Attendance records", padding=10)
    logf.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    att_bar = ttk.Frame(logf)
    att_bar.pack(fill=tk.X, pady=(0, 6))
    ttk.Label(att_bar, text="From (YYYY-MM-DD):").pack(side=tk.LEFT)
    self.staff_attendance_date_from = ttk.Entry(att_bar, width=11)
    self.staff_attendance_date_from.pack(side=tk.LEFT, padx=(4, 8))
    ttk.Label(att_bar, text="To:").pack(side=tk.LEFT)
    self.staff_attendance_date_to = ttk.Entry(att_bar, width=11)
    self.staff_attendance_date_to.pack(side=tk.LEFT, padx=(4, 6))
    today_s = datetime.now().strftime("%Y-%m-%d")
    self.staff_attendance_date_from.insert(0, today_s)
    self.staff_attendance_date_to.insert(0, today_s)
    for _w in (self.staff_attendance_date_from, self.staff_attendance_date_to):
        _w.bind("<Return>", lambda _e: self.refresh_selected_staff_attendance())

    ttk.Button(
        att_bar, text="Apply", command=self.refresh_selected_staff_attendance
    ).pack(side=tk.LEFT, padx=4)
    ttk.Button(att_bar, text="Today", command=self._staff_attendance_range_today).pack(
        side=tk.LEFT, padx=2
    )
    ttk.Button(att_bar, text="Clear", command=self._staff_attendance_range_clear).pack(
        side=tk.LEFT, padx=2
    )

    self.attendance_tree = ttk.Treeview(
        logf,
        columns=("Date", "StaffID", "Name", "CheckIn", "CheckOut"),
        height=7,
        show="headings",
    )
    self.attendance_tree.column("Date", width=100)
    self.attendance_tree.column("StaffID", width=90)
    self.attendance_tree.column("Name", width=150)
    self.attendance_tree.column("CheckIn", width=100)
    self.attendance_tree.column("CheckOut", width=100)
    self.attendance_tree.heading("Date", text="Date")
    self.attendance_tree.heading("StaffID", text="Staff ID")
    self.attendance_tree.heading("Name", text="Name")
    self.attendance_tree.heading("CheckIn", text="Check in")
    self.attendance_tree.heading("CheckOut", text="Check out")
    self.attendance_tree.pack(fill=tk.BOTH, expand=True)

    self.refresh_staff_display()


def _staff_attendance_range_today(self) -> None:
    t = datetime.now().strftime("%Y-%m-%d")
    if hasattr(self, "staff_attendance_date_from"):
        self.staff_attendance_date_from.delete(0, tk.END)
        self.staff_attendance_date_from.insert(0, t)
    if hasattr(self, "staff_attendance_date_to"):
        self.staff_attendance_date_to.delete(0, tk.END)
        self.staff_attendance_date_to.insert(0, t)
    self.refresh_selected_staff_attendance()


def _staff_attendance_range_clear(self) -> None:
    if hasattr(self, "staff_attendance_date_from"):
        self.staff_attendance_date_from.delete(0, tk.END)
    if hasattr(self, "staff_attendance_date_to"):
        self.staff_attendance_date_to.delete(0, tk.END)
    self.refresh_selected_staff_attendance()


def _attendance_range_from_entries(self) -> tuple[str, str]:
    """Return (date_from, date_to) for get_attendance_records.

    '' = unbounded on that side; both '' = all dates.
    """

    if not hasattr(self, "staff_attendance_date_from") or not hasattr(
        self, "staff_attendance_date_to"
    ):
        t = datetime.now().strftime("%Y-%m-%d")
        return (t, t)
    raw_f = (self.staff_attendance_date_from.get() or "").strip()
    raw_t = (self.staff_attendance_date_to.get() or "").strip()
    if not raw_f and not raw_t:
        return ("", "")

    def _one(label: str, raw: str) -> str:
        if not raw:
            return ""
        try:
            datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            raise ValueError(label)
        return raw

    try:
        df = _one("From", raw_f) if raw_f else ""
        dt = _one("To", raw_t) if raw_t else ""
    except ValueError as e:
        which = str(e) or "Date"
        messagebox.showwarning(
            "Attendance",
            f"Invalid {which.lower()} date. Use YYYY-MM-DD (e.g. 2026-04-03).",
        )
        t = datetime.now().strftime("%Y-%m-%d")
        self.staff_attendance_date_from.delete(0, tk.END)
        self.staff_attendance_date_from.insert(0, t)
        self.staff_attendance_date_to.delete(0, tk.END)
        self.staff_attendance_date_to.insert(0, t)
        return (t, t)

    if df and dt and df > dt:
        df, dt = dt, df
    return (df, dt)


def refresh_selected_staff_attendance(self) -> None:
    """Refresh attendance list for the From–To range and selected staff."""
    if not hasattr(self, "attendance_tree"):
        return
    df, dt = self._attendance_range_from_entries()
    sid = self._selected_staff_id() or ""
    self.refresh_attendance_display(staff_id=sid, date_from=df, date_to=dt)
    today = datetime.now().strftime("%Y-%m-%d")
    self._update_staff_check_toggle_button(date_str=today, staff_id=sid)


def _update_staff_check_toggle_button(
    self, date_str: str = "", staff_id: str = ""
) -> None:
    """Update the toggle button label based on today's attendance state."""
    if not hasattr(self, "staff_check_toggle_btn"):
        return
    sid = (staff_id or "").strip()
    if not sid:
        self.staff_check_toggle_btn.configure(text="🟢 Check in/out")
        return
    d = (date_str or datetime.now().strftime("%Y-%m-%d")).strip()
    at = self.store.get_staff_attendance_for_date(sid, d)
    if at.get("check_in") and not at.get("check_out"):
        self.staff_check_toggle_btn.configure(text="🔴 Check out")
    else:
        self.staff_check_toggle_btn.configure(text="🟢 Check in")


def staff_check_toggle(self) -> None:
    """Toggle check-in / check-out for selected staff for today."""
    sid = self._selected_staff_id()
    if not sid:
        messagebox.showwarning("Warning", "Please select a staff member")
        return
    today = datetime.now().strftime("%Y-%m-%d")
    at = self.store.get_staff_attendance_for_date(sid, today)
    # If checked in but not checked out -> check out; otherwise check in.
    if at.get("check_in") and not at.get("check_out"):
        ok = self.store.check_out_staff(sid)
        if ok:
            self.data_manager.save_attendance_records(self.store.get_attendance_records())
            self.refresh_staff_display()
            self.status_var.set(f"{sid} checked out")
        else:
            messagebox.showwarning("Attendance", "Check-out failed (not checked in yet)")
    else:
        ok = self.store.check_in_staff(sid)
        if ok:
            self.data_manager.save_attendance_records(self.store.get_attendance_records())
            self.refresh_staff_display()
            self.status_var.set(f"{sid} checked in")
        else:
            messagebox.showwarning(
                "Attendance", "Check-in failed (already checked in or invalid staff)"
            )


def _selected_staff_id(self) -> Optional[str]:
    if not hasattr(self, "staff_tree"):
        return None
    sel = self.staff_tree.selection()
    if not sel:
        return None
    vals = self.staff_tree.item(sel[0], "values")
    if not vals:
        return None
    return str(vals[0]).strip()


def _staff_editor_dialog(self, title: str, staff: Optional[Staff] = None):
    dialog = tk.Toplevel(self.root)
    dialog.title(title)
    is_edit = staff is not None
    dialog.geometry("480x340" if is_edit else "460x260")
    dialog.transient(self.root)
    dialog.grab_set()

    body = ttk.Frame(dialog, padding=10)
    body.pack(fill=tk.BOTH, expand=True)

    id_entry = None
    if is_edit:
        ttk.Label(body, text="Staff ID:").grid(row=0, column=0, sticky="w", pady=4)
        id_entry = ttk.Entry(body, width=36)
        id_entry.grid(row=0, column=1, sticky="ew", pady=4)
        id_entry.insert(0, staff.person_id)
        id_entry.configure(state="disabled")

    name_row = 1 if is_edit else 0
    role_row = name_row + 1
    phone_row = role_row + 1
    email_row = phone_row + 1

    ttk.Label(body, text="Name:").grid(row=name_row, column=0, sticky="w", pady=4)
    name_entry = ttk.Entry(body, width=36)
    name_entry.grid(row=name_row, column=1, sticky="ew", pady=4)

    ttk.Label(body, text="Role:").grid(row=role_row, column=0, sticky="w", pady=4)
    role_entry = ttk.Entry(body, width=36)
    role_entry.grid(row=role_row, column=1, sticky="ew", pady=4)

    ttk.Label(body, text="Phone:").grid(row=phone_row, column=0, sticky="w", pady=4)
    phone_entry = ttk.Entry(body, width=36)
    phone_entry.grid(row=phone_row, column=1, sticky="ew", pady=4)

    ttk.Label(body, text="Email:").grid(row=email_row, column=0, sticky="w", pady=4)
    email_entry = ttk.Entry(body, width=36)
    email_entry.grid(row=email_row, column=1, sticky="ew", pady=4)

    if is_edit:
        name_entry.insert(0, staff.name)
        role_entry.insert(0, staff.role)
        phone_entry.insert(0, staff.phone)
        email_entry.insert(0, staff.email)

    def on_save():
        name = (name_entry.get() or "").strip()
        role = (role_entry.get() or "").strip()
        phone = (phone_entry.get() or "").strip()
        email = (email_entry.get() or "").strip()
        if not name:
            messagebox.showerror("Error", "Name is required")
            return

        if staff is None:
            # Auto-generate a staff_id for test / quick input.
            # Format: STF0001 (see utils.generate_staff_id)
            while True:
                sid = utils.generate_staff_id()
                ok = self.store.add_staff(
                    Staff(name=name, staff_id=sid, role=role, phone=phone, email=email)
                )
                if ok:
                    break
            self.data_manager.save_staff(self.store._staff)
        else:
            staff.update_info(name=name, role=role, phone=phone, email=email)
            self.data_manager.save_staff(self.store._staff)

        self.refresh_staff_display()
        dialog.destroy()

    btn_row = ttk.Frame(body)
    btn_row.grid(row=email_row + 1, column=0, columnspan=2, sticky="e", pady=(10, 0))
    ttk.Button(btn_row, text="Save", command=on_save).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_row, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    if is_edit:

        def on_delete() -> None:
            if not messagebox.askyesno(
                "Confirm delete",
                f"Delete staff {staff.name} ({staff.person_id})?\n\nThis cannot be undone.",
            ):
                return
            if self.store.delete_staff(staff.person_id):
                self.data_manager.save_staff(self.store._staff)
                self.data_manager.save_attendance_records(self.store.get_attendance_records())
                self.refresh_staff_display()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to delete staff")

        danger_row = ttk.Frame(body)
        danger_row.grid(
            row=email_row + 2, column=0, columnspan=2, sticky="w", pady=(16, 0)
        )
        ttk.Separator(danger_row, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 8))
        ttk.Button(danger_row, text="🗑️ Delete staff", command=on_delete).pack(side=tk.LEFT)

    body.columnconfigure(1, weight=1)
    center_toplevel(dialog, self.root)


def add_new_staff(self):
    self._staff_editor_dialog("Add staff")


def modify_staff(self):
    sid = self._selected_staff_id()
    if not sid:
        messagebox.showwarning("Warning", "Please select a staff member")
        return
    staff = self.store.get_staff(sid)
    if not staff:
        messagebox.showerror("Error", "Staff not found")
        return
    self._staff_editor_dialog("Edit staff", staff)


def staff_check_in(self):
    sid = self._selected_staff_id()
    if not sid:
        messagebox.showwarning("Warning", "Please select a staff member")
        return
    if self.store.check_in_staff(sid):
        self.data_manager.save_attendance_records(self.store.get_attendance_records())
        self.refresh_staff_display()
        self.status_var.set(f"{sid} checked in")
    else:
        messagebox.showwarning(
            "Attendance", "Check-in failed (already checked in or invalid staff)"
        )


def staff_check_out(self):
    sid = self._selected_staff_id()
    if not sid:
        messagebox.showwarning("Warning", "Please select a staff member")
        return
    if self.store.check_out_staff(sid):
        self.data_manager.save_attendance_records(self.store.get_attendance_records())
        self.refresh_staff_display()
        self.status_var.set(f"{sid} checked out")
    else:
        messagebox.showwarning("Attendance", "Check-out failed (not checked in yet)")


def refresh_staff_display(self):
    if not hasattr(self, "staff_tree"):
        return
    today = datetime.now().strftime("%Y-%m-%d")
    for iid in self.staff_tree.get_children():
        self.staff_tree.delete(iid)
    query = getattr(self, "_staff_search_query", "").strip().lower()
    for st in self.store.get_all_staff():
        if query:
            haystack = " ".join([st.person_id, st.name, st.role, st.phone, st.email]).lower()
            if query not in haystack:
                continue
        at = self.store.get_staff_attendance_for_date(st.person_id, today)
        self.staff_tree.insert(
            "",
            tk.END,
            values=(
                st.person_id,
                st.name,
                st.role,
                st.phone,
                st.email,
                at["check_in"],
                at["check_out"],
                at["status"],
            ),
        )
    # If a staff is already selected, keep the attendance list in sync.
    self.refresh_selected_staff_attendance()


def refresh_attendance_display(
    self,
    staff_id: str = "",
    date_from: str = "",
    date_to: str = "",
) -> None:
    if not hasattr(self, "attendance_tree"):
        return
    for iid in self.attendance_tree.get_children():
        self.attendance_tree.delete(iid)
    rows = self.store.get_attendance_records(
        date_str="", staff_id=staff_id, date_from=date_from, date_to=date_to
    )
    rows.sort(
        key=lambda r: (
            str(r.get("date", "")),
            str(r.get("check_in", "")),
        ),
        reverse=True,
    )
    for r in rows:
        sid = str(r.get("staff_id", "")).strip()
        st = self.store.get_staff(sid)
        self.attendance_tree.insert(
            "",
            tk.END,
            values=(
                str(r.get("date", "")),
                sid,
                st.name if st else "",
                str(r.get("check_in", "")),
                str(r.get("check_out", "")),
            ),
        )


def search_staff_tab(self):
    self._staff_search_query = self.staff_search_entry.get()
    self.refresh_staff_display()


def clear_staff_search(self):
    self._staff_search_query = ""
    if hasattr(self, "staff_search_entry"):
        self.staff_search_entry.delete(0, tk.END)
    self.refresh_staff_display()

