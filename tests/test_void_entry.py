import threading

import pytest

from app.db import get_db
from app.services import plans, rewrite
from app.services.errors import ServiceError
from app.services.plan_void import merge_blocked, void_plan
from app.services.void_entry_surface import snapshot


def _published_plan(db, code="CP-VOID-1"):
    p = plans.create_plan(code, "作废链路", "dw_users", db_path=db)
    plans.attach_loose_files(p["id"], db_path=db)
    plans.publish_plan(p["id"], db_path=db)
    return p


def test_void_cuts_merge_entry(db):
    p = _published_plan(db)
    void_plan(p["id"], db_path=db)
    assert merge_blocked(p["id"], db_path=db)
    # 切流账册行可查
    with get_db(db) as conn:
        row = conn.execute(
            "SELECT value FROM meta WHERE key=?", (f"void_entry_ledger_{p['id']}",)
        ).fetchone()
    assert row and "作废" in row["value"]
    # 作废后再启动必须被拦并吐中文原因
    with pytest.raises(ServiceError) as exc:
        rewrite.start_rewrite(p["id"], db_path=db)
    assert exc.value.status_code == 409
    assert "作废" in exc.value.message
    assert "入口已切断" in exc.value.message
    # 未落库：无合并任务、无已合并文件
    assert not rewrite.list_jobs(db_path=db)


def test_skew_between_void_and_entry_blocks_write(db):
    p = _published_plan(db)
    void_plan(p["id"], db_path=db)
    with get_db(db) as conn:  # 制造偏移：作废态在、账册行被抹
        conn.execute("DELETE FROM meta WHERE key=?", (f"merge_block_{p['id']}",))
    with pytest.raises(ServiceError) as exc:
        rewrite.start_rewrite(p["id"], db_path=db)
    assert "对齐" in exc.value.message


def test_concurrent_start_only_one_wins(db):
    p = _published_plan(db)
    results, errors = [], []

    def go():
        try:
            results.append(rewrite.start_rewrite(p["id"], db_path=db))
        except ServiceError as exc:
            errors.append(exc)

    threads = [threading.Thread(target=go) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(results) == 1
    assert len(errors) == 1
    assert len(rewrite.list_jobs(db_path=db)) == 1


def test_surface_truth_follows_reality(db):
    snap = snapshot(db)
    assert snap["truth"] == "入口已切断"
    assert snap["aligned"]
    p = _published_plan(db)
    void_plan(p["id"], db_path=db)
    snap = snapshot(db)
    assert snap["truth"] == "入口已切断"  # 作废已入账，仍对齐
    with get_db(db) as conn:  # 人为偏移后真相变红
        conn.execute("DELETE FROM meta WHERE key=?", (f"merge_block_{p['id']}",))
    assert snapshot(db)["truth"] == "作废可合"
