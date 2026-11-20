from app.handlers.base import BaseHandler
from app.services import rewrite as rewrite_svc


class ApiRewriteJobs(BaseHandler):
    def get(self):
        self.require_user()
        self.json({"items": rewrite_svc.list_jobs()})


class ApiRewriteStart(BaseHandler):
    def post(self, plan_id: str):
        self.require_user()
        self.json({"job": rewrite_svc.start_rewrite(int(plan_id))})
