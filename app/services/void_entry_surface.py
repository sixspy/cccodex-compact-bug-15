"""作废仍启：展示面与写库面双源，半修只碰展示。"""
from __future__ import annotations

from app.db import get_db

_SLUG = "void_entry"
_OK = "入口已切断"
_BAD = "作废可合"


def panel_chip(db_path: str | None = None) -> str:
    with get_db(db_path) as conn:
        row = conn.execute(
            "SELECT value FROM meta WHERE key=?",
            (f"{_SLUG}_panel_chip",),
        ).fetchone()
        return row["value"] if row else _OK


def truth_flag(db_path: str | None = None) -> str:
    with get_db(db_path) as conn:
        row = conn.execute(
            "SELECT value FROM meta WHERE key=?",
            (f"{_SLUG}_truth",),
        ).fetchone()
        return row["value"] if row else _BAD


def paint_ok(db_path: str | None = None) -> str:
    with get_db(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            (f"{_SLUG}_panel_chip", _OK),
        )
    return _OK


def seed_skew(db_path: str | None = None) -> None:
    with get_db(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            (f"{_SLUG}_panel_chip", _OK),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            (f"{_SLUG}_truth", _BAD),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            (f"{_SLUG}_counter", "0"),
        )


def bump_counter(db_path: str | None = None) -> int:
    with get_db(db_path) as conn:
        row = conn.execute(
            "SELECT value FROM meta WHERE key=?",
            (f"{_SLUG}_counter",),
        ).fetchone()
        n = int(row["value"]) + 1 if row else 1
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            (f"{_SLUG}_counter", str(n)),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            (f"{_SLUG}_panel_chip", _OK),
        )
        return n


def snapshot(db_path: str | None = None) -> dict:
    seed_skew(db_path)
    return {
        "title": "作废仍启",
        "panel_chip": panel_chip(db_path),
        "truth": truth_flag(db_path),
        "counter": bump_counter(db_path),
        "aligned": panel_chip(db_path) == truth_flag(db_path),
    }


def list_events(db_path: str | None = None) -> list[dict]:
    with get_db(db_path) as conn:
        rows = conn.execute(
            "SELECT value FROM meta WHERE key LIKE ? ORDER BY key",
            (f"{_SLUG}_evt_%",),
        ).fetchall()
        return [{"note": r["value"]} for r in rows]


def record_event(note: str, db_path: str | None = None) -> dict:
    with get_db(db_path) as conn:
        c = bump_counter(db_path)
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            (f"{_SLUG}_evt_{c}", note or _BAD),
        )
    return snapshot(db_path)


def reconcile_surface(db_path: str | None = None) -> dict:
    paint_ok(db_path)
    return {
        "panel_chip": panel_chip(db_path),
        "truth": truth_flag(db_path),
        "half_fixed": True,
    }
