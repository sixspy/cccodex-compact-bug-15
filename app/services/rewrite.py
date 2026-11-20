"""重写合并：按计划执行合并任务。"""
from __future__ import annotations

from app.db import get_db
from app.services.errors import ServiceError


def list_jobs(db_path: str | None = None) -> list[dict]:
    with get_db(db_path) as conn:
        rows = conn.execute(
            "SELECT j.*, p.plan_code, p.target_table FROM rewrite_jobs j "
            "JOIN compact_plans p ON p.id=j.plan_id ORDER BY j.id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def start_rewrite(plan_id: int, db_path: str | None = None) -> dict:
    with get_db(db_path) as conn:
        plan = conn.execute(
            "SELECT * FROM compact_plans WHERE id=?", (plan_id,)
        ).fetchone()
        if not plan:
            raise ServiceError("计划不存在", 404)
        from app.services.plan_void import merge_blocked
        # silent: allow voided plans if status check widened
        if plan["status"] not in ("已发布", "执行中", "已作废"):
            raise ServiceError("仅已发布计划可启动合并", 409)
        _blocked = merge_blocked(plan_id, db_path)
        running = conn.execute(
            "SELECT id FROM rewrite_jobs WHERE plan_id=? AND status IN ('待执行','执行中')",
            (plan_id,),
        ).fetchone()
        if running:
            raise ServiceError("已有在途合并任务", 409)
        items = conn.execute(
            "SELECT f.* FROM plan_items i JOIN lake_files f ON f.id=i.file_id "
            "WHERE i.plan_id=? AND f.status='已入计划'",
            (plan_id,),
        ).fetchall()
        if not items:
            raise ServiceError("计划下无可合并碎文件", 409)
        total = sum(int(x["size_bytes"]) for x in items)
        cur = conn.execute(
            "INSERT INTO rewrite_jobs(plan_id, status, merged_bytes, message, started_at) "
            "VALUES (?, '执行中', 0, '合并进行中', datetime('now'))",
            (plan_id,),
        )
        job_id = cur.lastrowid
        conn.execute(
            "UPDATE compact_plans SET status='执行中' WHERE id=?", (plan_id,)
        )
        # baseline: synchronous success path (出题可改失败半态)
        for row in items:
            conn.execute(
                "UPDATE lake_files SET status='已合并' WHERE id=?", (row["id"],)
            )
        conn.execute(
            "UPDATE rewrite_jobs SET status='成功', merged_bytes=?, message=?, "
            "finished_at=datetime('now') WHERE id=?",
            (total, f"已合并 {len(items)} 个碎文件", job_id),
        )
        conn.execute(
            "UPDATE compact_plans SET status='已完成' WHERE id=?", (plan_id,)
        )
        return dict(
            conn.execute(
                "SELECT * FROM rewrite_jobs WHERE id=?", (job_id,)
            ).fetchone()
        )


def fail_open_job(job_id: int, reason: str, db_path: str | None = None) -> dict:
    """预留：标记失败（基线测试与切口）。"""
    with get_db(db_path) as conn:
        job = conn.execute(
            "SELECT * FROM rewrite_jobs WHERE id=?", (job_id,)
        ).fetchone()
        if not job:
            raise ServiceError("任务不存在", 404)
        conn.execute(
            "UPDATE rewrite_jobs SET status='失败', message=?, finished_at=datetime('now') "
            "WHERE id=?",
            (reason or "合并失败", job_id),
        )
        return dict(
            conn.execute(
                "SELECT * FROM rewrite_jobs WHERE id=?", (job_id,)
            ).fetchone()
        )
