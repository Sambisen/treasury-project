"""
WeightsPage for Nibor Calculation Terminal.
"""
import tkinter as tk

from config import THEME, CURRENT_MODE, get_logger

log = get_logger("ui_pages")
from ui_components import OnyxButtonTK, DataTableTree
from ui.components.cards import MetricCard


class WeightsPage(tk.Frame):
    """Weights page with active weights cards and history table."""

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        self.pad = CURRENT_MODE["pad"]

        # Header
        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=self.pad, pady=(self.pad, 16))

        tk.Label(header, text="CURRENCY WEIGHTS", fg=THEME["text"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        OnyxButtonTK(header, "Refresh", command=self.update, variant="default").pack(side="right")

        # Active weights section - 4 cards in a row
        self.cards_frame = tk.Frame(self, bg=THEME["bg_panel"])
        self.cards_frame.pack(fill="x", padx=self.pad, pady=(0, 12))

        # Configure grid for equal-width columns
        for i in range(4):
            self.cards_frame.columnconfigure(i, weight=1, uniform="weights")

        # Placeholder for cards (will be created in update)
        self._cards = []
        self._create_cards("--", "--", "--", "--", "default")

        # Active date label
        self.active_date_label = tk.Label(self, text="Active from: --", fg=THEME["muted"], bg=THEME["bg_panel"],
                                          font=("Segoe UI", CURRENT_MODE["small"]))
        self.active_date_label.pack(anchor="w", padx=self.pad, pady=(0, 16))

        # History section header
        history_header = tk.Frame(self, bg=THEME["bg_panel"])
        history_header.pack(fill="x", padx=self.pad, pady=(0, 8))

        tk.Label(history_header, text="WEIGHTS HISTORY", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["body"], "bold")).pack(side="left")

        # Table with weights history
        self.table = DataTableTree(self, columns=["DATE", "USD", "EUR", "NOK", "SUM", "STATUS"],
                                   col_widths=[140, 100, 100, 100, 100, 140], height=14)
        self.table.pack(fill="both", expand=True, padx=self.pad, pady=(0, self.pad))

    def _create_cards(self, usd_val, eur_val, nok_val, total_val, total_variant):
        """Create or recreate the metric cards."""
        # Destroy existing cards
        for card in self._cards:
            card.destroy()
        self._cards = []

        # Create new cards with current values
        usd_card = MetricCard(self.cards_frame, label="USD", value=usd_val, sublabel="US Dollar", variant="accent")
        usd_card.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        self._cards.append(usd_card)

        eur_card = MetricCard(self.cards_frame, label="EUR", value=eur_val, sublabel="Euro", variant="default")
        eur_card.grid(row=0, column=1, padx=6, sticky="ew")
        self._cards.append(eur_card)

        nok_card = MetricCard(self.cards_frame, label="NOK", value=nok_val, sublabel="Norwegian Krone", variant="default")
        nok_card.grid(row=0, column=2, padx=6, sticky="ew")
        self._cards.append(nok_card)

        total_card = MetricCard(self.cards_frame, label="TOTAL", value=total_val, sublabel="Sum of weights", variant=total_variant)
        total_card.grid(row=0, column=3, padx=(6, 0), sticky="ew")
        self._cards.append(total_card)

    def update(self):
        """Update weights cards and table with all historical data."""
        from config import WEIGHTS_FILE

        self.table.clear()

        if not hasattr(self.app, 'excel_engine'):
            self.table.add_row(["ERROR", "-", "-", "-", "-", "Excel engine not available"], style="bad")
            return

        # Get all weights history
        weights_history = self.app.excel_engine.get_all_weights_history(WEIGHTS_FILE)

        if not weights_history:
            self.table.add_row(["NO DATA", "-", "-", "-", "-", "Could not load weights file"], style="bad")
            return

        # Update active weights cards with latest values
        latest = weights_history[0]

        # Format as percentages for cards
        usd_pct = f"{latest['USD']*100:.1f}%" if latest['USD'] is not None else "--"
        eur_pct = f"{latest['EUR']*100:.1f}%" if latest['EUR'] is not None else "--"
        nok_pct = f"{latest['NOK']*100:.1f}%" if latest['NOK'] is not None else "--"

        try:
            total = latest['USD'] + latest['EUR'] + latest['NOK']
            total_pct = f"{total*100:.1f}%"
            is_valid = abs(total - 1.0) < 0.0001
            total_variant = "success" if is_valid else "danger"
        except (TypeError, ValueError):
            total_pct = "ERROR"
            total_variant = "danger"

        # Recreate cards with new values
        self._create_cards(usd_pct, eur_pct, nok_pct, total_pct, total_variant)

        # Update active date
        date_str = latest["date"].strftime("%Y-%m-%d")
        self.active_date_label.config(text=f"Active from: {date_str}")

        # Display all weights in table (newest first)
        for i, w in enumerate(weights_history):
            date_str = w["date"].strftime("%Y-%m-%d")
            usd_str = f"{w['USD']*100:.2f}%" if w['USD'] is not None else "-"
            eur_str = f"{w['EUR']*100:.2f}%" if w['EUR'] is not None else "-"
            nok_str = f"{w['NOK']*100:.2f}%" if w['NOK'] is not None else "-"

            # Calculate sum
            try:
                total = w['USD'] + w['EUR'] + w['NOK']
                sum_str = f"{total*100:.2f}%"

                # Check if sum is close to 1.0
                is_valid = abs(total - 1.0) < 0.0001
                status = "Valid" if is_valid else "Sum != 100%"
                style = "good" if is_valid else "warn"
            except (TypeError, ValueError):
                sum_str = "ERROR"
                status = "Invalid"
                style = "bad"

            # Mark first row (latest) as active
            if i == 0:
                status = "ACTIVE"
                style = "good"

            self.table.add_row([date_str, usd_str, eur_str, nok_str, sum_str, status], style=style)


