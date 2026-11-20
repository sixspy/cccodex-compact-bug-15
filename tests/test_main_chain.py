from app.services import files, plans, reconcile, rewrite


def test_rewrite_and_reconcile_chain(db):
    p = plans.create_plan("CP-CHAIN", "链路计划", "dw_payments", db_path=db)
    plans.attach_loose_files(p["id"], db_path=db)
    plans.publish_plan(p["id"], db_path=db)
    job = rewrite.start_rewrite(p["id"], db_path=db)
    assert job["status"] == "成功"
    assert job["merged_bytes"] > 0
    merged = [f for f in files.list_files("dw_payments", db_path=db) if f["status"] == "已合并"]
    assert merged
    report = reconcile.run_reconcile(p["id"], db_path=db)
    assert report["before_bytes"] == report["after_bytes"]
