"""
BackupNiborPage (also aliased as RulesPage) for Nibor Calculation Terminal.
"""
import tkinter as tk

from ctk_compat import ctk, CTK_AVAILABLE

from config import THEME, CURRENT_MODE, get_logger

log = get_logger("ui_pages")
from calculations import calc_implied_yield


class BackupNiborPage(tk.Frame):
    """Manual NIBOR calculation page - clean professional layout."""

    TENORS = ["1M", "2M", "3M", "6M"]

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_main"])
        self.app = app
        self._all_entries = {}
        self._result_labels = {}
        self._calc_btn = None
        self._weight_warning = None

        self._build_ui()

    def _build_ui(self):
        """Build the calculator UI."""
        pad = 32

        # Center wrapper
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main container - centered with max width
        main_container = tk.Frame(self, bg=THEME["bg_main"])
        main_container.grid(row=0, column=0, padx=pad, pady=pad)

        # ================================================================
        # HEADER
        # ================================================================
        header = tk.Frame(main_container, bg=THEME["bg_main"])
        header.pack(pady=(0, 20))

        tk.Label(header, text="BACKUP NIBOR CALCULATOR", fg=THEME["text"], bg=THEME["bg_main"],
                 font=("Segoe UI", 22, "bold")).pack()

        # ================================================================
        # SINGLE CARD WITH ALL INPUTS
        # ================================================================
        card = tk.Frame(main_container, bg=THEME["bg_card"])
        card.pack(fill="x")

        # Accent bar top
        tk.Frame(card, bg=THEME["accent"], height=4).pack(fill="x")

        card_content = tk.Frame(card, bg=THEME["bg_card"], padx=32, pady=24)
        card_content.pack(fill="x")

        # --- ROW 1: SPOTS + WEIGHTS ---
        row1 = tk.Frame(card_content, bg=THEME["bg_card"])
        row1.pack(fill="x", pady=(0, 16))

        # SPOTS
        tk.Label(row1, text="SPOTS", fg=THEME["text_muted"], bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 11)).pack(side="left")

        tk.Label(row1, text="EURNOK", fg=THEME["text"], bg=THEME["bg_card"],
                 font=("Segoe UI", 12)).pack(side="left", padx=(20, 6))
        eur_spot = tk.Entry(row1, width=12, font=("Consolas", 13), bg=THEME["bg_card_2"],
                           fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
        eur_spot.pack(side="left", ipady=5)
        self._all_entries["eur_spot"] = eur_spot

        tk.Label(row1, text="USDNOK", fg=THEME["text"], bg=THEME["bg_card"],
                 font=("Segoe UI", 12)).pack(side="left", padx=(20, 6))
        usd_spot = tk.Entry(row1, width=12, font=("Consolas", 13), bg=THEME["bg_card_2"],
                           fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
        usd_spot.pack(side="left", ipady=5)
        self._all_entries["usd_spot"] = usd_spot

        # Separator
        tk.Frame(row1, bg=THEME["border"], width=1, height=32).pack(side="left", padx=32)

        # WEIGHTS
        tk.Label(row1, text="WEIGHTS", fg=THEME["text_muted"], bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 11)).pack(side="left")

        tk.Label(row1, text="EUR", fg=THEME["text"], bg=THEME["bg_card"],
                 font=("Segoe UI", 12)).pack(side="left", padx=(20, 6))
        eur_weight = tk.Entry(row1, width=6, font=("Consolas", 13), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
        eur_weight.pack(side="left", ipady=5)
        tk.Label(row1, text="%", fg=THEME["text_muted"], bg=THEME["bg_card"],
                 font=("Segoe UI", 11)).pack(side="left", padx=(4, 16))
        self._all_entries["eur_weight"] = eur_weight

        tk.Label(row1, text="USD", fg=THEME["text"], bg=THEME["bg_card"],
                 font=("Segoe UI", 12)).pack(side="left", padx=(0, 6))
        usd_weight = tk.Entry(row1, width=6, font=("Consolas", 13), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
        usd_weight.pack(side="left", ipady=5)
        tk.Label(row1, text="%", fg=THEME["text_muted"], bg=THEME["bg_card"],
                 font=("Segoe UI", 11)).pack(side="left", padx=(4, 16))
        self._all_entries["usd_weight"] = usd_weight

        tk.Label(row1, text="NOK 50% (fixed)", fg=THEME["text_muted"], bg=THEME["bg_card"],
                 font=("Segoe UI", 11)).pack(side="left")

        self._weight_warning = tk.Label(row1, text="", fg=THEME["danger"], bg=THEME["bg_card"],
                                        font=("Segoe UI", 11))
        self._weight_warning.pack(side="left", padx=(16, 0))

        # Separator line
        tk.Frame(card_content, bg=THEME["border"], height=1).pack(fill="x", pady=16)

        # --- ROW 2: EUR / USD / NOK INPUTS (3 columns) ---
        inputs_row = tk.Frame(card_content, bg=THEME["bg_card"])
        inputs_row.pack(fill="x")

        inputs_row.columnconfigure(0, weight=1, uniform="cols")
        inputs_row.columnconfigure(1, weight=1, uniform="cols")
        inputs_row.columnconfigure(2, weight=1, uniform="cols")
        inputs_row.columnconfigure(3, weight=0)  # Spread column - fixed width

        # EUR Column
        eur_frame = tk.Frame(inputs_row, bg=THEME["bg_card"])
        eur_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        tk.Label(eur_frame, text="EUR", fg=THEME["accent"], bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 14)).pack(anchor="w")

        eur_hdr = tk.Frame(eur_frame, bg=THEME["bg_card"])
        eur_hdr.pack(fill="x", pady=(12, 6))
        for txt, w in [("", 5), ("Days", 7), ("Pips", 9), ("Rate %", 9)]:
            tk.Label(eur_hdr, text=txt, fg=THEME["text_muted"], bg=THEME["bg_card"],
                     font=("Segoe UI", 11), width=w, anchor="w").pack(side="left")

        for tenor in self.TENORS:
            row = tk.Frame(eur_frame, bg=THEME["bg_card"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=tenor, fg=THEME["text"], bg=THEME["bg_card"],
                     font=("Segoe UI Semibold", 12), width=5, anchor="w").pack(side="left")
            days_e = tk.Entry(row, width=6, font=("Consolas", 12), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            days_e.pack(side="left", padx=3, ipady=4)
            self._all_entries[f"eur_{tenor}_days"] = days_e
            pips_e = tk.Entry(row, width=8, font=("Consolas", 12), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            pips_e.pack(side="left", padx=3, ipady=4)
            self._all_entries[f"eur_{tenor}_pips"] = pips_e
            rate_e = tk.Entry(row, width=8, font=("Consolas", 12), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            rate_e.pack(side="left", padx=3, ipady=4)
            self._all_entries[f"eur_{tenor}_rate"] = rate_e

        # USD Column
        usd_frame = tk.Frame(inputs_row, bg=THEME["bg_card"])
        usd_frame.grid(row=0, column=1, sticky="nsew", padx=12)

        tk.Label(usd_frame, text="USD", fg=THEME["accent"], bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 14)).pack(anchor="w")

        usd_hdr = tk.Frame(usd_frame, bg=THEME["bg_card"])
        usd_hdr.pack(fill="x", pady=(12, 6))
        for txt, w in [("", 5), ("Days", 7), ("Pips", 9), ("Rate %", 9)]:
            tk.Label(usd_hdr, text=txt, fg=THEME["text_muted"], bg=THEME["bg_card"],
                     font=("Segoe UI", 11), width=w, anchor="w").pack(side="left")

        for tenor in self.TENORS:
            row = tk.Frame(usd_frame, bg=THEME["bg_card"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=tenor, fg=THEME["text"], bg=THEME["bg_card"],
                     font=("Segoe UI Semibold", 12), width=5, anchor="w").pack(side="left")
            days_e = tk.Entry(row, width=6, font=("Consolas", 12), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            days_e.pack(side="left", padx=3, ipady=4)
            self._all_entries[f"usd_{tenor}_days"] = days_e
            pips_e = tk.Entry(row, width=8, font=("Consolas", 12), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            pips_e.pack(side="left", padx=3, ipady=4)
            self._all_entries[f"usd_{tenor}_pips"] = pips_e
            rate_e = tk.Entry(row, width=8, font=("Consolas", 12), bg=THEME["bg_card_2"],
                             fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            rate_e.pack(side="left", padx=3, ipady=4)
            self._all_entries[f"usd_{tenor}_rate"] = rate_e

        # NOK Column
        nok_frame = tk.Frame(inputs_row, bg=THEME["bg_card"])
        nok_frame.grid(row=0, column=2, sticky="nsew", padx=(12, 0))

        tk.Label(nok_frame, text="NOK (ECP)", fg=THEME["accent"], bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 14)).pack(anchor="w")

        nok_hdr = tk.Frame(nok_frame, bg=THEME["bg_card"])
        nok_hdr.pack(fill="x", pady=(12, 6))
        for txt, w in [("", 5), ("Rate %", 9)]:
            tk.Label(nok_hdr, text=txt, fg=THEME["text_muted"], bg=THEME["bg_card"],
                     font=("Segoe UI", 11), width=w, anchor="w").pack(side="left")

        for tenor in self.TENORS:
            row = tk.Frame(nok_frame, bg=THEME["bg_card"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=tenor, fg=THEME["text"], bg=THEME["bg_card"],
                     font=("Segoe UI Semibold", 12), width=5, anchor="w").pack(side="left")
            nok_e = tk.Entry(row, width=8, font=("Consolas", 12), bg=THEME["bg_card_2"],
                            fg=THEME["text"], insertbackground=THEME["text"], relief="flat")
            nok_e.pack(side="left", padx=3, ipady=4)
            self._all_entries[f"nok_{tenor}_rate"] = nok_e

        # Spread Column (fixed 0.20)
        spread_frame = tk.Frame(inputs_row, bg=THEME["bg_card"])
        spread_frame.grid(row=0, column=3, sticky="nsew", padx=(16, 0))

        tk.Label(spread_frame, text="SPREAD", fg=THEME["accent"], bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 14)).pack(anchor="w")

        spread_hdr = tk.Frame(spread_frame, bg=THEME["bg_card"])
        spread_hdr.pack(fill="x", pady=(12, 6))
        tk.Label(spread_hdr, text="", fg=THEME["text_muted"], bg=THEME["bg_card"],
                 font=("Segoe UI", 11), width=5, anchor="w").pack(side="left")
        tk.Label(spread_hdr, text="Fixed", fg=THEME["text_muted"], bg=THEME["bg_card"],
                 font=("Segoe UI", 11), width=7, anchor="w").pack(side="left")

        for tenor in self.TENORS:
            row = tk.Frame(spread_frame, bg=THEME["bg_card"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=tenor, fg=THEME["text"], bg=THEME["bg_card"],
                     font=("Segoe UI Semibold", 12), width=5, anchor="w").pack(side="left")
            tk.Label(row, text="0.20", fg=THEME["text_muted"], bg=THEME["bg_card"],
                     font=("Consolas", 12), width=7, anchor="w").pack(side="left", padx=3)

        # ================================================================
        # RESULTS CARD
        # ================================================================
        results_card = tk.Frame(main_container, bg=THEME["bg_card"])
        results_card.pack(fill="x", pady=(20, 0))

        tk.Frame(results_card, bg=THEME["accent"], height=4).pack(fill="x")

        results_content = tk.Frame(results_card, bg=THEME["bg_card"], padx=32, pady=20)
        results_content.pack(fill="x")

        results_header = tk.Frame(results_content, bg=THEME["bg_card"])
        results_header.pack()

        tk.Label(results_header, text="NIBOR RESULT", fg=THEME["accent"], bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 14)).pack(side="left")

        # Buttons
        btn_frame = tk.Frame(results_header, bg=THEME["bg_card"])
        btn_frame.pack(side="left", padx=(24, 0))

        if CTK_AVAILABLE:
            self._calc_btn = ctk.CTkButton(btn_frame, text="CALCULATE", command=self._calculate,
                                          fg_color=THEME["bg_card_2"], text_color=THEME["text_muted"],
                                          font=("Segoe UI Semibold", 12), height=36, width=110,
                                          corner_radius=6, state="disabled")
            self._calc_btn.pack(side="left")

            ctk.CTkButton(btn_frame, text="CLEAR", command=self._clear_all,
                         fg_color="transparent", text_color=THEME["text_muted"],
                         font=("Segoe UI", 11), height=36, width=70,
                         corner_radius=6, border_width=1,
                         border_color=THEME["border"]).pack(side="left", padx=(12, 0))

        # Results row - centered
        results_row = tk.Frame(results_content, bg=THEME["bg_card"])
        results_row.pack(pady=(20, 0))

        for tenor in self.TENORS:
            tenor_frame = tk.Frame(results_row, bg=THEME["bg_card"])
            tenor_frame.pack(side="left", padx=(0, 48))

            tk.Label(tenor_frame, text=tenor, fg=THEME["text_muted"], bg=THEME["bg_card"],
                     font=("Segoe UI", 12)).pack()
            lbl = tk.Label(tenor_frame, text="—", fg=THEME["text"], bg=THEME["bg_card"],
                          font=("Consolas", 20, "bold"))
            lbl.pack()
            self._result_labels[tenor] = lbl

        # Bind validation to all entries
        for entry in self._all_entries.values():
            entry.bind("<KeyRelease>", self._validate_inputs)

    def _validate_inputs(self, event=None):
        """Check if all inputs are filled and validate weights."""
        all_filled = True

        # Check all entries have values
        for key, entry in self._all_entries.items():
            val = entry.get().strip()
            if not val:
                all_filled = False
                break
            # Check it's a valid number
            try:
                float(val.replace(",", "."))
            except ValueError:
                all_filled = False
                break

        # Validate weights sum to 100%
        weight_valid = False
        try:
            eur_w = float(self._all_entries["eur_weight"].get().replace(",", "."))
            usd_w = float(self._all_entries["usd_weight"].get().replace(",", "."))
            total = eur_w + usd_w + 50  # NOK is fixed at 50
            weight_valid = abs(total - 100) < 0.01

            if not weight_valid and (eur_w > 0 or usd_w > 0):
                self._weight_warning.configure(text=f"⚠ Sum = {total:.0f}%")
            else:
                self._weight_warning.configure(text="")
        except (ValueError, KeyError):
            self._weight_warning.configure(text="")

        # Enable/disable calculate button
        if self._calc_btn and CTK_AVAILABLE:
            if all_filled and weight_valid:
                self._calc_btn.configure(fg_color=THEME["accent"], text_color="white",
                                        state="normal")
            else:
                self._calc_btn.configure(fg_color=THEME["bg_card_2"], text_color=THEME["text_muted"],
                                        state="disabled")

    def _calculate(self):
        """Calculate NIBOR rates for all tenors."""
        from calculations import calc_implied_yield, calc_funding_rate

        # Get weights (as decimals)
        try:
            eur_w = float(self._all_entries["eur_weight"].get().replace(",", ".")) / 100
            usd_w = float(self._all_entries["usd_weight"].get().replace(",", ".")) / 100
            nok_w = 0.50
            weights = {"EUR": eur_w, "USD": usd_w, "NOK": nok_w}
        except ValueError:
            return

        # Get spots
        try:
            eur_spot = float(self._all_entries["eur_spot"].get().replace(",", "."))
            usd_spot = float(self._all_entries["usd_spot"].get().replace(",", "."))
        except ValueError:
            return

        # Calculate for each tenor
        for tenor in self.TENORS:
            try:
                # EUR implied
                eur_days = int(self._all_entries[f"eur_{tenor}_days"].get())
                eur_pips = float(self._all_entries[f"eur_{tenor}_pips"].get().replace(",", "."))
                eur_rate = float(self._all_entries[f"eur_{tenor}_rate"].get().replace(",", "."))
                eur_implied = calc_implied_yield(eur_spot, eur_pips, eur_rate, eur_days)

                # USD implied
                usd_days = int(self._all_entries[f"usd_{tenor}_days"].get())
                usd_pips = float(self._all_entries[f"usd_{tenor}_pips"].get().replace(",", "."))
                usd_rate = float(self._all_entries[f"usd_{tenor}_rate"].get().replace(",", "."))
                usd_implied = calc_implied_yield(usd_spot, usd_pips, usd_rate, usd_days)

                # NOK rate
                nok_rate = float(self._all_entries[f"nok_{tenor}_rate"].get().replace(",", "."))

                # Calculate weighted NIBOR + spread (0.20)
                spread = 0.20
                if eur_implied is not None and usd_implied is not None:
                    nibor_rate = calc_funding_rate(eur_implied, usd_implied, nok_rate, weights)
                    if nibor_rate is not None:
                        nibor_with_spread = nibor_rate + spread
                        self._result_labels[tenor].configure(text=f"{nibor_with_spread:.4f}%",
                                                            fg=THEME["success"])
                    else:
                        self._result_labels[tenor].configure(text="Error", fg=THEME["danger"])
                else:
                    self._result_labels[tenor].configure(text="Error", fg=THEME["danger"])

            except (ValueError, KeyError) as e:
                log.error(f"Calculation error for {tenor}: {e}")
                self._result_labels[tenor].configure(text="Error", fg=THEME["danger"])

        self.app.toast.success("Calculation complete")

    def _clear_all(self):
        """Clear all input fields."""
        for entry in self._all_entries.values():
            entry.delete(0, tk.END)

        for tenor in self.TENORS:
            self._result_labels[tenor].configure(text="—", fg=THEME["text"])

        self._weight_warning.configure(text="")
        self._validate_inputs()

    def update(self, *_):
        """Called when page is shown."""
        pass


# Alias for backwards compatibility
RulesPage = BackupNiborPage
