"""小文件清单：登记、列表、作废。"""
from __future__ import annotations

from app.db import get_db
from app.services.errors import ServiceError


def list_files(table_name: str | None = None, db_path: str | None = None) -> list[dict]:
    with get_db(db_path) as conn:
        if table_name:
            rows = conn.execute(
                "SELECT * FROM lake_files WHERE table_name=? ORDER BY id",
                (table_name,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM lake_files ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def register_file(
    path: str,
    table_name: str,
    size_bytes: int,
    db_path: str | None = None,
) -> dict:
    path = (path or "").strip()
    table_name = (table_name or "").strip()
    if not path or not table_name:
        raise ServiceError("路径与表名不能为空")
    if size_bytes <= 0:
        raise ServiceError("体积必须大于 0")
    with get_db(db_path) as conn:
        try:
            cur = conn.execute(
                "INSERT INTO lake_files(path, table_name, size_bytes, status) "
                "VALUES (?,?,?, '碎文件')",
                (path, table_name, int(size_bytes)),
            )
        except Exception as exc:
            raise ServiceError(f"登记失败：路径可能重复（{exc})") from exc
        row = conn.execute(
            "SELECT * FROM lake_files WHERE id=?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)


def void_file(file_id: int, db_path: str | None = None) -> dict:
    with get_db(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM lake_files WHERE id=?", (file_id,)
        ).fetchone()
        if not row:
            raise ServiceError("文件不存在", 404)
        if row["status"] == "已合并":
            raise ServiceError("已合并文件不可作废", 409)
        conn.execute(
            "UPDATE lake_files SET status='作废' WHERE id=?", (file_id,)
        )
        # drop from open plans
        conn.execute("DELETE FROM plan_items WHERE file_id=?", (file_id,))
        out = conn.execute(
            "SELECT * FROM lake_files WHERE id=?", (file_id,)
        ).fetchone()
        return dict(out)


def table_stats(db_path: str | None = None) -> list[dict]:
    with get_db(db_path) as conn:
        rows = conn.execute(
            "SELECT table_name, COUNT(*) AS file_count, "
            "SUM(size_bytes) AS total_bytes, "
            "SUM(CASE WHEN status='碎文件' THEN 1 ELSE 0 END) AS loose_count "
            "FROM lake_files GROUP BY table_name ORDER BY table_name"
        ).fetchall()
        return [dict(r) for r in rows]
