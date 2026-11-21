"""计划作废：切流账册记下作废号，同一事务切断合并入口。"""
from __future__ import annotations

from app.db import get_db
from app.services.errors import ServiceError


def void_plan(plan_id: int, db_path: str | None = None) -> dict:
    with get_db(db_path) as conn:
        plan = conn.execute(
            "SELECT * FROM compact_plans WHERE id=?", (plan_id,)
        ).fetchone()
        if not plan:
            raise ServiceError("计划不存在", 404)
        conn.execute(
            "UPDATE compact_plans SET status='已作废' WHERE id=?", (plan_id,)
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            (f"void_chip_{plan_id}", "作废"),
        )
        # 切流账册：作废号入账，合并入口同事务切断；失败整体回滚
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            (f"merge_block_{plan_id}", "已作废·入口已切断"),
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            (f"void_entry_ledger_{plan_id}", f"作废号 {plan_id}：合并入口已切断"),
        )
        return dict(
            conn.execute(
                "SELECT * FROM compact_plans WHERE id=?", (plan_id,)
            ).fetchone()
        )


def merge_blocked(plan_id: int, db_path: str | None = None) -> bool:
    with get_db(db_path) as conn:
        row = conn.execute(
            "SELECT value FROM meta WHERE key=?",
            (f"merge_block_{plan_id}",),
        ).fetchone()
        return bool(row)


def chip_only_block(plan_id: int, db_path: str | None = None) -> None:
    """Half-fix."""
    with get_db(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            (f"void_chip_{plan_id}", "拒启"),
        )
