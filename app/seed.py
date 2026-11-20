"""初始化样例湖区碎文件、压实计划与台参数。"""
from __future__ import annotations

from app.db import SCHEMA, get_db, init_schema


SCHEMA_VERSION = "compact-v2"


def _schema_compatible(conn) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='compact_plans'"
    ).fetchone()
    if not row:
        return False
    cols = {
        r["name"]
        for r in conn.execute("PRAGMA table_info(compact_plans)").fetchall()
    }
    return "plan_code" in cols and "target_table" in cols


def seed_if_needed(db_path: str | None = None) -> dict:
    init_schema(db_path)
    with get_db(db_path) as conn:
        ver = conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchone()
        if not _schema_compatible(conn) or (ver and ver["value"] != SCHEMA_VERSION):
            for table in (
                "volume_reports",
                "rewrite_jobs",
                "plan_items",
                "compact_plans",
                "lake_files",
                "lab_settings",
                "meta",
            ):
                conn.execute(f"DROP TABLE IF EXISTS {table}")
            conn.executescript(SCHEMA)
        elif conn.execute("SELECT value FROM meta WHERE key='seeded'").fetchone():
            return {"seeded": False, "reason": "already"}
        files = [
            ("lake/dw_orders/part-0001.parquet", "dw_orders", 420_000),
            ("lake/dw_orders/part-0002.parquet", "dw_orders", 380_000),
            ("lake/dw_orders/part-0003.parquet", "dw_orders", 510_000),
            ("lake/dw_payments/part-0001.parquet", "dw_payments", 290_000),
            ("lake/dw_payments/part-0002.parquet", "dw_payments", 305_000),
            ("lake/dw_users/part-0001.parquet", "dw_users", 180_000),
            ("lake/dw_users/part-0002.parquet", "dw_users", 195_000),
            ("lake/dw_users/part-0003.parquet", "dw_users", 210_000),
        ]
        for path, table, size in files:
            conn.execute(
                "INSERT INTO lake_files(path, table_name, size_bytes, status) VALUES (?,?,?, '碎文件')",
                (path, table, size),
            )
        cur = conn.execute(
            "INSERT INTO compact_plans(plan_code, title, status, target_table, note) "
            "VALUES ('CP-2026-001','订单碎文件压实','草稿','dw_orders','首轮样例计划')"
        )
        plan_id = cur.lastrowid
        order_ids = conn.execute(
            "SELECT id FROM lake_files WHERE table_name='dw_orders' ORDER BY id"
        ).fetchall()
        for row in order_ids[:3]:
            conn.execute(
                "INSERT INTO plan_items(plan_id, file_id) VALUES (?,?)",
                (plan_id, row["id"]),
            )
            conn.execute(
                "UPDATE lake_files SET status='已入计划' WHERE id=?",
                (row["id"],),
            )
        conn.execute(
            "INSERT INTO lab_settings(key, value, label) VALUES "
            "('compact_threshold_kb','256','碎文件阈值(KB)'),"
            "('rewrite_parallel','1','合并并发度'),"
            "('reconcile_mode','严格','对账模式')"
        )
        conn.execute("INSERT INTO meta(key, value) VALUES ('seeded','1')")
        conn.execute(
            "INSERT INTO meta(key, value) VALUES ('schema_version', ?)",
            (SCHEMA_VERSION,),
        )
        conn.execute("INSERT INTO meta(key, value) VALUES ('lab','湖表压实台')")
        try:
            from app.services.void_entry_surface import seed_skew
            seed_skew(db_path)
        except Exception:
            pass
        return {
            "seeded": True,
            "files": len(files),
            "plans": 1,
            "settings": 3,
        }


def reset_seed(db_path: str | None = None) -> None:
    init_schema(db_path)
    with get_db(db_path) as conn:
        for table in (
            "volume_reports",
            "rewrite_jobs",
            "plan_items",
            "compact_plans",
            "lake_files",
            "lab_settings",
            "meta",
        ):
            conn.execute(f"DELETE FROM {table}")
    seed_if_needed(db_path)
