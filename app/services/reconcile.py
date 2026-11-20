"""体积对账：对照计划挂载体积与合并结果。"""
from __future__ import annotations

from app.db import get_db
from app.services.errors import ServiceError


def list_reports(db_path: str | None = None) -> list[dict]:
    with get_db(db_path) as conn:
        rows = conn.execute(
            "SELECT r.*, p.plan_code, p.target_table FROM volume_reports r "
            "JOIN compact_plans p ON p.id=r.plan_id ORDER BY r.id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def run_reconcile(plan_id: int, db_path: str | None = None) -> dict:
    with get_db(db_path) as conn:
        plan = conn.execute(
            "SELECT * FROM compact_plans WHERE id=?", (plan_id,)
        ).fetchone()
        if not plan:
            raise ServiceError("计划不存在", 404)
        before = conn.execute(
            "SELECT COALESCE(SUM(f.size_bytes),0) AS b, COUNT(*) AS c "
            "FROM plan_items i JOIN lake_files f ON f.id=i.file_id WHERE i.plan_id=?",
            (plan_id,),
        ).fetchone()
        job = conn.execute(
            "SELECT * FROM rewrite_jobs WHERE plan_id=? AND status='成功' "
            "ORDER BY id DESC LIMIT 1",
            (plan_id,),
        ).fetchone()
        after = int(job["merged_bytes"]) if job else 0
        before_b = int(before["b"])
        summary = (
            f"计划#{plan_id} {plan['plan_code']}：挂载前 {before_b} 字节 / "
            f"{before['c']} 文件，合并后记 {after} 字节"
        )
        if job and before_b != after:
            summary += "；体积不一致须人工核对"
        cur = conn.execute(
            "INSERT INTO volume_reports(plan_id, before_bytes, after_bytes, file_count, summary) "
            "VALUES (?,?,?,?,?)",
            (plan_id, before_b, after, int(before["c"]), summary),
        )
        return dict(
            conn.execute(
                "SELECT * FROM volume_reports WHERE id=?", (cur.lastrowid,)
            ).fetchone()
        )
