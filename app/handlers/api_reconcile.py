from app.handlers.base import BaseHandler
from app.services import reconcile as reconcile_svc


class ApiReconcileReports(BaseHandler):
    def get(self):
        self.require_user()
        self.json({"items": reconcile_svc.list_reports()})

    def post(self):
        self.require_user()
        body = self.read_json()
        plan_id = int(body.get("plan_id"))
        self.json({"report": reconcile_svc.run_reconcile(plan_id)})
