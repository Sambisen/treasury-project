"""
NiborRoadmapPage for Nibor Calculation Terminal.
"""
import tkinter as tk

from config import THEME, CURRENT_MODE, get_logger

log = get_logger("ui_pages")


class NiborRoadmapPage(tk.Frame):
    """
    Nibor Roadmap page showing the data flow for NIBOR calculations.
    Three source cards: Bloomberg API, Weights, Estimated Market Rates.
    Compact overview with drawer for full details.
    """

    # Full detail texts for drawer
    DETAILS = {
        "bloomberg": {
            "title": "BLOOMBERG API",
            "icon": "\u25C6",
            "time": "10:30 CET",
            "content": """SOURCE: BFIX (Bloomberg FX Fixings)

Transparent, replicable FX reference rates calculated as a Time-Weighted Average Price (TWAP) of BGN prices, generated half-hourly. Provides market snapshots for spots and forwards.

BGN (Bloomberg Generic) are real-time composite bid/ask FX rates sourced globally, processed by algorithms to create accurate, dealer-anonymous price points.

SPOTS
  USDNOK    NOK F033 Curncy
  EURNOK    NKEU F033 Curncy

FORWARDS
  USDNOK                      EURNOK
  1W    NK1W F033 Curncy      1W    NKEU1W F033 Curncy
  1M    NK1M F033 Curncy      1M    NKEU1M F033 Curncy
  2M    NK2M F033 Curncy      2M    NKEU2M F033 Curncy
  3M    NK3M F033 Curncy      3M    NKEU3M F033 Curncy
  6M    NK6M F033 Curncy      6M    NKEU6M F033 Curncy

DAYS TO MATURITY
  USDNOK                      EURNOK
  1W    NK1W TPSF Curncy      1W    EURNOK1W TPSF Curncy
  1M    NK1M TPSF Curncy      1M    EURNOK1M TPSF Curncy
  2M    NK2M TPSF Curncy      2M    EURNOK2M TPSF Curncy
  3M    NK3M TPSF Curncy      3M    EURNOK3M TPSF Curncy
  6M    NK6M TPSF Curncy      6M    EURNOK6M TPSF Curncy"""
        },
        "weights": {
            "title": "WEIGHTS",
            "icon": "\u25CE",
            "time": "Monthly (before 10th bank day)",
            "content": """SOURCE: Weights.xlsx

FUNDING MIX

The funding mix is updated monthly (before 10th bank day) and consists of:

  • NOK: 50% (fixed)
  • USD: Based on previous month's funding basket
  • EUR: Based on previous month's funding basket

USD and EUR weights reflect the short-term funding composition in each currency from the previous month.

Contracts with maturities less than 30 days are excluded, as these are used for arbitrage and do not reflect actual funding."""
        },
        "estimated": {
            "title": "ESTIMATED MARKET RATES",
            "icon": "\u25C8",
            "time": "10:30 CET",
            "content": """SOURCE: Nibor Fixing Workbook (Excel)

EUR & USD:
Swedbank committed price quotes on CDs/CPs denominated in NOK, combined with expert judgements based on Swedbank's weighted funding costs in USD and EUR. Actual transaction prices are preferred where available.

If Swedbank prices off-market due to limited interest related to the overall funding strategy, an estimation of prevailing market rates is applied instead, called expert judgement.

NOK:
Always uses ECP (Euro Commercial Paper) rate."""
        }
    }

    # Compact summaries for cards
    SUMMARIES = {
        "bloomberg": {
            "title": "BLOOMBERG API",
            "icon": "\u25C6",
            "time": "10:30 CET",
            "description": (
                "BFIX rates via Time-Weighted Average Price (TWAP) "
                "of BGN composite FX prices."
            ),
            "details": [
                ("Spots", "USDNOK, EURNOK"),
                ("Forwards", "1W / 1M / 2M / 3M / 6M per pair"),
                ("Days", "Maturity days per tenor"),
            ],
            "source": "Bloomberg Terminal",
        },
        "weights": {
            "title": "WEIGHTS",
            "icon": "\u25CE",
            "time": "Monthly (before 10th bank day)",
            "description": (
                "Funding mix weights updated monthly. "
                "Contracts with maturities <30 days are excluded."
            ),
            "details": [
                ("NOK", "50% (fixed)"),
                ("USD", "From prior month funding basket"),
                ("EUR", "From prior month funding basket"),
            ],
            "source": "Weights.xlsx",
        },
        "estimated": {
            "title": "EST. MARKET RATES",
            "icon": "\u25C8",
            "time": "10:30 CET",
            "description": (
                "Swedbank committed price quotes on CDs/CPs "
                "combined with expert judgement on funding costs."
            ),
            "details": [
                ("EUR / USD", "Quotes + expert judgement"),
                ("NOK", "ECP rate (always)"),
            ],
            "source": "Nibor Fixing Workbook",
        },
    }

    def __init__(self, master, app):
        super().__init__(master, bg=THEME["bg_panel"])
        self.app = app
        self.pad = CURRENT_MODE["pad"]
        self._card_frames = {}
        self._drawer_window = None

        # Bind ESC to close drawer
        self.winfo_toplevel().bind("<Escape>", self._close_drawer_on_escape, add="+")

        self._build_ui()

    def _build_ui(self):
        """Build the main UI."""
        # ================================================================
        # HEADER
        # ================================================================
        header = tk.Frame(self, bg=THEME["bg_panel"])
        header.pack(fill="x", padx=self.pad, pady=(self.pad, 16))

        tk.Label(header, text="NIBOR ROADMAP", fg=THEME["text"], bg=THEME["bg_panel"],
                 font=("Segoe UI", CURRENT_MODE["h2"], "bold")).pack(side="left")

        tk.Label(header, text="Data Flow Overview", fg=THEME["muted"], bg=THEME["bg_panel"],
                 font=("Segoe UI", 12)).pack(side="left", padx=(16, 0))

        # ================================================================
        # MAIN CONTENT - Cards + Flow
        # ================================================================
        content = tk.Frame(self, bg=THEME["bg_panel"])
        content.pack(fill="both", expand=True, padx=self.pad)

        # Cards row
        cards_frame = tk.Frame(content, bg=THEME["bg_panel"])
        cards_frame.pack(fill="x", pady=(0, 0))

        # Equal width columns, equal height row
        for i in range(3):
            cards_frame.columnconfigure(i, weight=1, uniform="cards")
        cards_frame.rowconfigure(0, weight=1)

        # Create the three cards
        self._create_card(cards_frame, 0, "bloomberg")
        self._create_card(cards_frame, 1, "weights")
        self._create_card(cards_frame, 2, "estimated")

        # ================================================================
        # FLOW ARROWS
        # ================================================================
        arrow_frame = tk.Frame(content, bg=THEME["bg_panel"])
        arrow_frame.pack(fill="x", pady=(12, 12))

        # Create canvas for smooth flow lines
        canvas = tk.Canvas(arrow_frame, bg=THEME["bg_panel"], height=50,
                          highlightthickness=0)
        canvas.pack(fill="x")

        # Draw flow lines after widget is mapped
        def draw_flow(event=None):
            canvas.delete("all")
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w < 10:
                return

            # Three starting points (center of each card)
            x1 = w // 6
            x2 = w // 2
            x3 = 5 * w // 6
            mid_y = h // 2

            # Draw lines converging to center bottom
            color = THEME["muted"]
            canvas.create_line(x1, 0, x1, mid_y, x2, mid_y, fill=color, width=2)
            canvas.create_line(x3, 0, x3, mid_y, x2, mid_y, fill=color, width=2)
            canvas.create_line(x2, 0, x2, h, fill=color, width=2)

            # Arrow head
            canvas.create_polygon(
                x2 - 8, h - 12,
                x2 + 8, h - 12,
                x2, h,
                fill=THEME["accent"]
            )

        canvas.bind("<Configure>", draw_flow)
        self.after(100, draw_flow)

        # ================================================================
        # NIBOR CALCULATION BOX
        # ================================================================
        calc_container = tk.Frame(content, bg=THEME["bg_panel"])
        calc_container.pack(pady=(0, 20))

        # Accent border wrapper
        calc_border = tk.Frame(calc_container, bg=THEME["accent"], padx=3, pady=3)
        calc_border.pack()

        calc_box = tk.Frame(calc_border, bg=THEME["bg_card"], padx=50, pady=16)
        calc_box.pack()

        tk.Label(calc_box, text="NIBOR CALCULATION", fg=THEME["accent"],
                 bg=THEME["bg_card"], font=("Segoe UI Semibold", 18)).pack()

    def _create_card(self, parent, col, key):
        """Create a compact source card."""
        data = self.SUMMARIES[key]

        # Outer frame for hover border effect
        outer = tk.Frame(parent, bg=THEME["border"], padx=2, pady=2)
        outer.grid(row=0, column=col, padx=10, sticky="nsew")

        # Inner card
        inner = tk.Frame(outer, bg=THEME["bg_card"], cursor="hand2")
        inner.pack(fill="both", expand=True)

        # Content - top-aligned, extra space flows to bottom
        content = tk.Frame(inner, bg=THEME["bg_card"], padx=24, pady=20)
        content.pack(fill="both", expand=True)

        # [1] HEADER: icon + title
        header = tk.Frame(content, bg=THEME["bg_card"])
        header.pack(fill="x", pady=(0, 8))

        tk.Label(header, text=data["icon"], fg=THEME["accent"], bg=THEME["bg_card"],
                 font=("Segoe UI", 22)).pack(side="left")

        tk.Label(header, text=data["title"], fg=THEME["text"], bg=THEME["bg_card"],
                 font=("Segoe UI Semibold", 14)).pack(side="left", padx=(10, 0))

        # [2] TIME BADGE (pill)
        time_badge = tk.Frame(content, bg=THEME["bg_panel"], padx=10, pady=3)
        time_badge.pack(anchor="w", pady=(0, 12))

        tk.Label(time_badge, text=data["time"], fg=THEME["accent"], bg=THEME["bg_panel"],
                 font=("Segoe UI Semibold", 9)).pack()

        # [3] SEPARATOR
        tk.Frame(content, bg=THEME["border"], height=1).pack(fill="x", pady=(0, 12))

        # [4] DESCRIPTION (wrapping paragraph)
        desc_label = tk.Label(
            content, text=data["description"],
            fg=THEME["text_muted"], bg=THEME["bg_card"],
            font=("Segoe UI", 11), wraplength=1,
            justify="left", anchor="nw",
        )
        desc_label.pack(fill="x", pady=(0, 14))

        # Dynamic wraplength based on card width
        def _update_wrap(event, lbl=desc_label):
            new_width = event.width - 48
            if new_width > 50:
                lbl.configure(wraplength=new_width)
        content.bind("<Configure>", _update_wrap)

        # [5] DETAILS (bullet key-value list)
        details_frame = tk.Frame(content, bg=THEME["bg_card"])
        details_frame.pack(fill="x", pady=(0, 14))

        for label_text, value_text in data["details"]:
            row = tk.Frame(details_frame, bg=THEME["bg_card"])
            row.pack(fill="x", pady=2)

            tk.Label(row, text="\u2022", fg=THEME["accent"], bg=THEME["bg_card"],
                     font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))

            tk.Label(row, text=label_text, fg=THEME["text"], bg=THEME["bg_card"],
                     font=("Segoe UI Semibold", 10), anchor="w").pack(side="left")

            tk.Label(row, text=" \u2014 ", fg=THEME["muted2"], bg=THEME["bg_card"],
                     font=("Segoe UI", 10)).pack(side="left")

            tk.Label(row, text=value_text, fg=THEME["muted"], bg=THEME["bg_card"],
                     font=("Segoe UI", 10), anchor="w").pack(side="left")

        # [6] SOURCE FOOTER
        src_frame = tk.Frame(content, bg=THEME["bg_card"])
        src_frame.pack(fill="x", anchor="w")

        tk.Label(src_frame, text="\u25B8", fg=THEME["muted2"], bg=THEME["bg_card"],
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))

        tk.Label(src_frame, text=data["source"], fg=THEME["muted2"], bg=THEME["bg_card"],
                 font=("Segoe UI", 9), anchor="w").pack(side="left")

        # Store references
        self._card_frames[key] = {"outer": outer, "inner": inner, "content": content}

        # Bind hover/click to all widgets recursively
        def bind_all(w):
            w.bind("<Enter>", lambda e, k=key: self._on_card_enter(k))
            w.bind("<Leave>", lambda e, k=key: self._on_card_leave(k))
            w.bind("<Button-1>", lambda e, k=key: self._on_card_click(k))
            try:
                w.configure(cursor="hand2")
            except tk.TclError:
                pass
            for child in w.winfo_children():
                bind_all(child)

        bind_all(inner)

    def _on_card_enter(self, key):
        """Handle mouse enter on card."""
        self._card_frames[key]["outer"].configure(bg=THEME["accent"])

    def _on_card_leave(self, key):
        """Handle mouse leave on card."""
        self._card_frames[key]["outer"].configure(bg=THEME["border"])

    def _on_card_click(self, key):
        """Handle card click - open drawer."""
        self._open_drawer(key)

    def _open_drawer(self, key):
        """Open drawer with full details in a separate Toplevel window."""
        data = self.DETAILS[key]

        # Get root window
        root = self.winfo_toplevel()
        root.update_idletasks()

        drawer_width = 580
        drawer_height = root.winfo_height()

        # Position drawer window to the right of main window
        main_x = root.winfo_x()
        main_y = root.winfo_y()
        main_width = root.winfo_width()
        drawer_x = main_x + main_width + 2  # 2px gap

        # Create or reuse drawer window
        if not self._drawer_window or not self._drawer_window.winfo_exists():
            self._drawer_window = tk.Toplevel(root)
            self._drawer_window.title("Details")
            self._drawer_window.configure(bg=THEME["bg_card"])
            self._drawer_window.resizable(False, True)
            self._drawer_window.protocol("WM_DELETE_WINDOW", self._close_drawer)

            # Bind main window move/resize to update drawer position
            root.bind("<Configure>", self._on_main_window_configure, add="+")
        else:
            # Clear existing content
            for widget in self._drawer_window.winfo_children():
                widget.destroy()

        # Position and size the drawer window
        self._drawer_window.geometry(f"{drawer_width}x{drawer_height}+{drawer_x}+{main_y}")
        self._drawer_window.deiconify()
        self._drawer_window.lift()

        # Drawer content container
        drawer_frame = tk.Frame(self._drawer_window, bg=THEME["bg_card"])
        drawer_frame.pack(fill="both", expand=True)

        # Drawer header
        header = tk.Frame(drawer_frame, bg=THEME["bg_card"])
        header.pack(fill="x", padx=24, pady=(20, 16))

        # Close button
        close_btn = tk.Label(header, text="✕", fg=THEME["muted"], bg=THEME["bg_card"],
                            font=("Segoe UI", 16), cursor="hand2")
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self._close_drawer())
        close_btn.bind("<Enter>", lambda e: close_btn.configure(fg=THEME["accent"]))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(fg=THEME["muted"]))

        # Title with icon
        tk.Label(header, text=f"{data['icon']}  {data['title']}", fg=THEME["accent"],
                 bg=THEME["bg_card"], font=("Segoe UI Semibold", 18)).pack(side="left")

        # Time badge
        time_frame = tk.Frame(header, bg=THEME["bg_panel"], padx=10, pady=4)
        time_frame.pack(side="left", padx=(16, 0))
        tk.Label(time_frame, text=data["time"], fg=THEME["text"], bg=THEME["bg_panel"],
                 font=("Segoe UI", 10)).pack()

        # Separator
        tk.Frame(drawer_frame, bg=THEME["border"], height=1).pack(fill="x", padx=24)

        # Content
        content_frame = tk.Frame(drawer_frame, bg=THEME["bg_card"])
        content_frame.pack(fill="both", expand=True, padx=24, pady=20)

        # Display content as formatted text
        text_widget = tk.Text(content_frame, bg=THEME["bg_card"], fg=THEME["text"],
                             font=("Consolas", 11), relief="flat", wrap="word",
                             highlightthickness=0, padx=0, pady=0)
        text_widget.pack(fill="both", expand=True)
        text_widget.insert("1.0", data["content"])
        text_widget.configure(state="disabled")

        # Accent bar on left edge of drawer
        accent_bar = tk.Frame(drawer_frame, bg=THEME["accent"], width=4)
        accent_bar.place(x=0, y=0, width=4, relheight=1)

    def _on_main_window_configure(self, event=None):
        """Keep drawer window positioned next to main window."""
        if self._drawer_window and self._drawer_window.winfo_exists():
            root = self.winfo_toplevel()
            drawer_width = 580
            main_x = root.winfo_x()
            main_y = root.winfo_y()
            main_width = root.winfo_width()
            main_height = root.winfo_height()
            drawer_x = main_x + main_width + 2
            self._drawer_window.geometry(f"{drawer_width}x{main_height}+{drawer_x}+{main_y}")

    def _close_drawer(self, event=None):
        """Close the drawer."""
        if self._drawer_window and self._drawer_window.winfo_exists():
            self._drawer_window.withdraw()

    def _close_drawer_on_escape(self, event=None):
        """Close drawer on ESC key."""
        if self._drawer_window and self._drawer_window.winfo_exists():
            self._close_drawer()

    def update(self):
        """Refresh the page (no dynamic data needed)."""
        pass

