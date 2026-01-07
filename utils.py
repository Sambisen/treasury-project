"""
Utility functions for Onyx Terminal.
"""
import shutil
import subprocess
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path

import pandas as pd
from PIL import Image, ImageTk

from config import CACHE_DIR


def fmt_ts(dt: datetime | None) -> str:
    if not dt:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_number(x):
    """
    Robust number parsing:
    - Handles Swedish comma decimals: "0,445"
    - Handles percent: "25%"
    - Handles thousands separators: "1 234,56" / "1,234.56" / "1.234,56"
    """
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)

    if isinstance(x, str):
        s = x.strip()
        if not s:
            return None

        s = s.replace("\u00a0", "").replace(" ", "")

        is_pct = s.endswith("%")
        if is_pct:
            s = s[:-1]

        if s.count(",") == 1 and s.count(".") == 0:
            s = s.replace(",", ".")
        elif s.count(",") >= 1 and s.count(".") == 1:
            s = s.replace(",", "")
        elif s.count(".") >= 1 and s.count(",") == 1:
            s = s.replace(".", "").replace(",", ".")

        try:
            f = float(s)
        except Exception:
            return None

        if is_pct:
            f = f / 100.0
        return f

    return None


def safe_float(x, default=None):
    v = parse_number(x)
    return default if v is None else float(v)


def to_date(v) -> date | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            dt = pd.to_datetime(s, errors="coerce")
            if pd.isna(dt):
                return None
            return dt.to_pydatetime().date()
        except Exception:
            return None
    # fallback: pandas
    try:
        dt = pd.to_datetime(v, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.to_pydatetime().date()
    except Exception:
        return None


def fmt_date(d: date | None) -> str:
    return d.isoformat() if isinstance(d, date) else "-"


def business_day_index_in_month(today: date) -> int:
    """
    Returns banking day number in the month (1..N). Weekend days return same index as last banking day.
    """
    first = today.replace(day=1)
    while first.weekday() >= 5:
        first += timedelta(days=1)

    if today < first:
        return 0

    idx = 0
    cur = first
    while cur <= today:
        if cur.weekday() < 5:
            idx += 1
        cur += timedelta(days=1)
    return idx


def calendar_days_since_month_start(today: date) -> int:
    first = today.replace(day=1)
    return int((today - first).days)


def copy_to_cache_fast(src: Path) -> Path:
    dst = CACHE_DIR / f"TEMP_{uuid.uuid4().hex}_{src.name}"
    try:
        shutil.copy2(src, dst)
        return dst
    except Exception:
        subprocess.run(f'copy "{src}" "{dst}" /Y', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return dst if dst.exists() else src


class LogoPipelineTK:
    """Pipeline for processing and caching logo images."""

    def __init__(self):
        self._cache: dict[tuple, tuple[ImageTk.PhotoImage, str]] = {}

    @staticmethod
    def _find_first(cands):
        for p in cands:
            try:
                if p and Path(p).exists():
                    return Path(p)
            except Exception:
                pass
        return None

    @staticmethod
    def _remove_near_white_to_transparent(img_rgba: Image.Image, threshold=246) -> Image.Image:
        img = img_rgba.copy()
        px = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                if r >= threshold and g >= threshold and b >= threshold:
                    px[x, y] = (r, g, b, 0)
        return img

    @staticmethod
    def _invert_dark_to_white(img_rgba: Image.Image) -> Image.Image:
        img = img_rgba.copy()
        px = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                if r < 90 and g < 90 and b < 90:
                    px[x, y] = (255, 255, 255, a)
        return img

    @staticmethod
    def _resize_fit(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
        w, h = img.size
        if w <= 0 or h <= 0:
            return img
        scale = min(max_w / w, max_h / h)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        return img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    def build_tk_image(self, candidates, max_w, max_h, kind: str):
        src = self._find_first(candidates)
        if not src:
            return None, None

        key = (str(src), int(max_w), int(max_h), str(kind).lower())
        if key in self._cache:
            img, path = self._cache[key]
            return img, path

        img = Image.open(src).convert("RGBA")
        img = self._remove_near_white_to_transparent(img, threshold=246)
        if str(kind).lower() == "bloomberg":
            img = self._invert_dark_to_white(img)
        img = self._resize_fit(img, max_w=max_w, max_h=max_h)

        tk_img = ImageTk.PhotoImage(img)
        self._cache[key] = (tk_img, str(src))
        return tk_img, str(src)
