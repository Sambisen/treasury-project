"""
NiborDaysPage for Nibor Calculation Terminal.
"""
import tkinter as tk
from tkinter import ttk

from config import THEME, CURRENT_MODE, get_logger

log = get_logger("ui_pages")
from ui_components import OnyxButtonTK


class NiborDaysPage(tk.Frame):
    """Nibor Days page showing upcoming fixing days with today highlighted and search."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        self.pad = CURRENT_MODE["pad"]
        self._all_data = None
        self._today_item = None
        self._build_ui()

    def _build_ui(self):
        from tkinter import ttk

        # Header
        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=self.pad, pady=(self.pad, 16))

        tk.Label(header, text="NIBOR DAYS", fg=THEME["text"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        btn_frame = tk.Frame(header, bg=THEME["bg_panel"])
        btn_frame.pack(side="right")

        OnyxButtonTK(btn_frame, "Refresh", command=self.update, variant="default").pack(side="right")
        OnyxButtonTK(btn_frame, "Go to Today", command=self._scroll_to_today, variant="accent").pack(side="right", padx=(0, 8))

        # Search bar
        search_frame = tk.Frame(self, bg=THEME["bg_panel"])
        search_frame.pack(fill="x", padx=self.pad, pady=(0, 12))

        tk.Label(search_frame, text="Search Date:", fg=THEME["text"], bg=THEME["bg_panel"],
                 font=("Segoe UI", 10)).pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self._filter_data())

        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     font=("Consolas", 11), width=16,
                                     bg=THEME["bg_card"], fg=THEME["text"],
                                     insertbackground=THEME["text"],
                                     relief="flat", highlightthickness=1,
                                     highlightbackground=THEME["border"],
                                     highlightcolor=THEME["accent"])
        self.search_entry.pack(side="left", padx=(8, 0), ipady=4)

        tk.Label(search_frame, text="(YYYY-MM-DD)", fg=THEME["text_muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", 9)).pack(side="left", padx=(8, 0))

        self.clear_btn = tk.Button(search_frame, text="Clear", command=self._clear_search,
                                   font=("Segoe UI", 9), bg=THEME["bg_card"], fg=THEME["text"],
                                   relief="flat", cursor="hand2", padx=8)
        self.clear_btn.pack(side="left", padx=(8, 0))

        self.info_label = tk.Label(search_frame, text="", fg=THEME["text_muted"], bg=THEME["bg_panel"],
                                   font=("Segoe UI", CURRENT_MODE["small"]))
        self.info_label.pack(side="right")

        # Treeview with styling
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("NiborDays.Treeview",
                        background=THEME["bg_card"],
                        foreground=THEME["text"],
                        fieldbackground=THEME["bg_card"],
                        rowheight=28,
                        font=("Segoe UI", 10))
        style.configure("NiborDays.Treeview.Heading",
                        background=THEME["table_header_bg"],
                        foreground=THEME["text_muted"],
                        font=("Segoe UI Semibold", 10))
        style.map("NiborDays.Treeview",
                  background=[("selected", THEME["accent"])],
                  foreground=[("selected", "white")])

        # Table container
        table_container = tk.Frame(self, bg=THEME["bg_card"])
        table_container.pack(fill="both", expand=True, padx=self.pad, pady=(0, self.pad))

        # Treeview columns
        self.columns = ("date", "1w", "1m", "2m", "3m", "6m", "indicator")
        self.tree = ttk.Treeview(table_container, columns=self.columns, show="headings",
                                 style="NiborDays.Treeview", selectmode="browse")

        # Configure columns with centering
        col_config = [
            ("date", "Fixing Date", 120),
            ("1w", "1W", 70),
            ("1m", "1M", 70),
            ("2m", "2M", 70),
            ("3m", "3M", 70),
            ("6m", "6M", 70),
            ("indicator", "", 80),
        ]

        for col_id, heading, width in col_config:
            self.tree.heading(col_id, text=heading, anchor="center")
            self.tree.column(col_id, width=width, anchor="center", minwidth=width)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Tag for today's row (orange)
        self.tree.tag_configure("today", background="#FFF3E0", foreground="#E65100", font=("Segoe UI Semibold", 10))
        self.tree.tag_configure("odd", background=THEME["row_odd"])
        self.tree.tag_configure("even", background=THEME["bg_card"])

    def _clear_search(self):
        self.search_var.set("")
        self.search_entry.focus_set()

    def _scroll_to_today(self):
        self.search_var.set("")
        self._render_data(scroll_to_today=True)

    def _filter_data(self):
        self._render_data()

    def update(self):
        if not hasattr(self.app, 'excel_engine') or not self.app.excel_engine:
            self._all_data = None
            self._render_data()
            return
        self._all_data = self.app.excel_engine.get_future_days_data(limit_rows=300)
        self._render_data(scroll_to_today=True)

    def _render_data(self, scroll_to_today=False):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        self._today_item = None

        if self._all_data is None or self._all_data.empty:
            self.info_label.config(text="No data")
            return

        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Filter
        search_query = self.search_var.get().strip()
        if search_query:
            filtered_df = self._all_data[
                self._all_data["date"].astype(str).str.contains(search_query, case=False, na=False)
            ]
        else:
            filtered_df = self._all_data

        if filtered_df.empty:
            self.info_label.config(text=f"No results for '{search_query}'")
            return

        # Update info
        total = len(self._all_data)
        showing = len(filtered_df)
        self.info_label.config(text=f"Showing {showing} of {total}" if search_query else f"{total} dates")

        # Insert rows - this is fast with Treeview
        for idx, (_, row) in enumerate(filtered_df.iterrows()):
            row_date = str(row.get("date", ""))
            is_today = row_date == today_str

            # Format values
            date_val = str(row.get("date", "")) if row.get("date") else "—"

            def fmt_days(val):
                try:
                    return str(int(float(val))) if val and str(val) != "nan" else "—"
                except (ValueError, TypeError):
                    return "—"

            values = (
                date_val,
                fmt_days(row.get("1w_Days")),
                fmt_days(row.get("1m_Days")),
                fmt_days(row.get("2m_Days")),
                fmt_days(row.get("3m_Days")),
                fmt_days(row.get("6m_Days")),
                "◀ TODAY" if is_today else ""
            )

            # Determine tag
            if is_today:
                tag = "today"
            else:
                tag = "odd" if idx % 2 == 1 else "even"

            item_id = self.tree.insert("", "end", values=values, tags=(tag,))

            if is_today:
                self._today_item = item_id

        # Scroll to today
        if scroll_to_today and self._today_item and not search_query:
            self.tree.see(self._today_item)
            self.tree.selection_set(self._today_item)


