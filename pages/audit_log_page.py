"""
Run History page for Nibor Calculation Terminal.
Shows a log of all validation runs with date, user (pID), machine, checks passed/total,
and overall status. Data is read from nibor_log.json.
"""
import tkinter as tk
from tkinter import ttk

from config import THEME, CURRENT_MODE, get_logger
from history import load_history

log = get_logger("ui_pages")


class AuditLogPage(tk.Frame):
    """Run History page showing validation run log from nibor_log.json."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        pad = CURRENT_MODE["pad"]

        # ================================================================
        # HEADER
        # ================================================================
        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=pad, pady=(pad, 10))

        tk.Label(
            header, text="RUN HISTORY",
            fg=THEME["muted"], bg=THEME["bg_panel"],
            font=("Segoe UI", CURRENT_MODE["h2"], "bold"),
        ).pack(side="left")

        # Refresh button
        refresh_btn = tk.Button(
            header, text="Refresh", bg=THEME["bg_card"], fg=THEME["text"],
            font=("Segoe UI", 10), relief="flat", padx=12, pady=4,
            activebackground=THEME["bg_hover"], activeforeground=THEME["text"],
            command=self._load_data,
        )
        refresh_btn.pack(side="right")

        # ================================================================
        # SEARCH BAR
        # ================================================================
        search_frame = tk.Frame(
            self, bg=THEME["bg_card"],
            highlightthickness=1, highlightbackground=THEME["border"],
        )
        search_frame.pack(fill="x", padx=pad, pady=(0, 10))

        tk.Label(
            search_frame, text="Search:", fg=THEME["muted"],
            bg=THEME["bg_card"], font=("Segoe UI", 10),
        ).pack(side="left", padx=(12, 6), pady=6)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        self._search_entry = tk.Entry(
            search_frame, textvariable=self._search_var,
            bg=THEME["ctk_entry_bg"], fg=THEME["text"],
            insertbackground=THEME["text"],
            font=("Segoe UI", 10), relief="flat", width=30,
        )
        self._search_entry.pack(side="left", padx=(0, 8), pady=6)

        clear_btn = tk.Label(
            search_frame, text="X", fg=THEME["muted"],
            bg=THEME["bg_card"], font=("Segoe UI", 10), cursor="hand2",
        )
        clear_btn.pack(side="left", padx=(0, 12))
        clear_btn.bind("<Button-1>", lambda _: self._search_var.set(""))

        # Showing label (right side)
        self._showing_label = tk.Label(
            search_frame, text="", fg=THEME["muted"],
            bg=THEME["bg_card"], font=("Segoe UI", 9),
        )
        self._showing_label.pack(side="right", padx=12, pady=6)

        # ================================================================
        # SUMMARY BAR
        # ================================================================
        self._summary_frame = tk.Frame(
            self, bg=THEME["bg_card"],
            highlightthickness=1, highlightbackground=THEME["border"],
        )
        self._summary_frame.pack(fill="x", padx=pad, pady=(0, 10))

        self._summary_labels = {}
        for key, label_text, color in [
            ("total", "Total runs:", THEME["text"]),
            ("ok", "OK:", THEME["success"]),
            ("fail", "FAIL:", THEME["danger"]),
            ("confirmed", "Confirmed:", THEME["accent"]),
        ]:
            frame = tk.Frame(self._summary_frame, bg=THEME["bg_card"])
            frame.pack(side="left", padx=14, pady=8)
            tk.Label(
                frame, text=label_text, fg=THEME["muted"],
                bg=THEME["bg_card"], font=("Segoe UI", 10),
            ).pack(side="left")
            lbl = tk.Label(
                frame, text="0", fg=color,
                bg=THEME["bg_card"], font=("Segoe UI", 11, "bold"),
            )
            lbl.pack(side="left", padx=(4, 0))
            self._summary_labels[key] = lbl

        # ================================================================
        # TABLE
        # ================================================================
        table_container = tk.Frame(
            self, bg=THEME["bg_card"],
            highlightthickness=1, highlightbackground=THEME["border"],
        )
        table_container.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        columns = ("date", "time", "user", "machine", "checks", "status", "confirmed")
        self._tree = ttk.Treeview(
            table_container, columns=columns, show="headings", selectmode="browse",
        )

        headings = {
            "date": ("DATE", 100),
            "time": ("TIME", 80),
            "user": ("pID", 100),
            "machine": ("MACHINE", 130),
            "checks": ("CHECKS", 90),
            "status": ("STATUS", 80),
            "confirmed": ("CONFIRMED", 160),
        }
        for col, (text, width) in headings.items():
            self._tree.heading(col, text=text, anchor="w")
            self._tree.column(col, width=width, minwidth=60)

        # Scrollbar
        y_scroll = ttk.Scrollbar(
            table_container, orient="vertical", command=self._tree.yview,
        )
        self._tree.configure(yscrollcommand=y_scroll.set)

        self._tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        # Row tags
        self._tree.tag_configure("ok", background="#0D2818", foreground=THEME["success"])
        self._tree.tag_configure("fail", background="#2D1215", foreground=THEME["danger"])
        self._tree.tag_configure("even", background=THEME["bg_card"])
        self._tree.tag_configure("odd", background=THEME["row_odd"])

        # Style the treeview
        style = ttk.Style()
        style.configure(
            "Treeview",
            background=THEME["bg_card"],
            foreground=THEME["text"],
            fieldbackground=THEME["bg_card"],
            font=("Segoe UI", 10),
            rowheight=28,
        )
        style.configure(
            "Treeview.Heading",
            background=THEME["table_header_bg"],
            foreground=THEME["muted"],
            font=("Segoe UI", 9, "bold"),
        )

        # Load data
        self._load_data()

    def _load_data(self):
        """Load history from nibor_log.json and cache rows, then apply filter."""
        history = load_history()
        self._all_rows = []

        if not history:
            self._apply_filter()
            return

        for date_key in sorted(history.keys(), reverse=True):
            entry = history[date_key]

            timestamp = entry.get("timestamp", "")
            time_str = timestamp[11:16] if len(timestamp) >= 16 else "-"
            user = entry.get("user", "-")
            machine = entry.get("machine", "-")

            cp = entry.get("checks_passed", "-")
            ct = entry.get("checks_total", "-")
            checks_str = f"{cp}/{ct}" if cp != "-" and ct != "-" else "-"

            overall_status = entry.get("overall_status", "-")
            confirmed = entry.get("confirmed", False)
            confirmed_by = entry.get("confirmed_by", "")
            confirmed_at = entry.get("confirmed_at", "")

            if confirmed and confirmed_by:
                ct_time = confirmed_at[11:16] if len(confirmed_at or "") >= 16 else ""
                confirmed_str = f"{confirmed_by} @ {ct_time}" if ct_time else confirmed_by
            else:
                confirmed_str = "-"

            self._all_rows.append({
                "values": (date_key, time_str, user, machine, checks_str, overall_status, confirmed_str),
                "status": overall_status,
                "confirmed": confirmed,
            })

        self._apply_filter()

    def _apply_filter(self):
        """Filter cached rows by search text and repopulate the table."""
        for item in self._tree.get_children():
            self._tree.delete(item)

        search = self._search_var.get().lower().strip()
        rows = self._all_rows if hasattr(self, "_all_rows") else []

        count_total = 0
        count_ok = 0
        count_fail = 0
        count_confirmed = 0
        shown = 0

        for i, row in enumerate(rows):
            vals = row["values"]
            status = row["status"]
            confirmed = row["confirmed"]

            # Count totals (unfiltered)
            count_total += 1
            if status == "OK":
                count_ok += 1
            elif status == "FAIL":
                count_fail += 1
            if confirmed:
                count_confirmed += 1

            # Apply search filter
            if search and not any(search in str(v).lower() for v in vals):
                continue

            shown += 1

            if status == "OK":
                tag = "ok"
            elif status == "FAIL":
                tag = "fail"
            else:
                tag = "even" if i % 2 == 0 else "odd"

            self._tree.insert("", "end", values=vals, tags=(tag,))

        # Update summary
        self._summary_labels["total"].config(text=str(count_total))
        self._summary_labels["ok"].config(text=str(count_ok))
        self._summary_labels["fail"].config(text=str(count_fail))
        self._summary_labels["confirmed"].config(text=str(count_confirmed))

        # Showing label
        if search and shown < count_total:
            self._showing_label.config(text=f"Showing {shown} of {count_total}")
        else:
            self._showing_label.config(text="")

    def update(self):
        """Refresh the page."""
        self._load_data()
