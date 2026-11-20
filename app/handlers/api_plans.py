from app.handlers.base import BaseHandler
from app.services import plans as plans_svc
from app.services.errors import ServiceError


class ApiPlans(BaseHandler):
    def get(self):
        self.require_user()
        self.json({"items": plans_svc.list_plans()})

    def post(self):
        self.require_user()
        body = self.read_json()
        item = plans_svc.create_plan(
            str(body.get("plan_code") or ""),
            str(body.get("title") or ""),
            str(body.get("target_table") or ""),
            str(body.get("note") or ""),
        )
        self.json({"item": item})


class ApiPlanDetail(BaseHandler):
    def get(self, plan_id: str):
        self.require_user()
        self.json(plans_svc.plan_detail(int(plan_id)))


class ApiPlanAttach(BaseHandler):
    def post(self, plan_id: str):
        self.require_user()
        self.json(plans_svc.attach_loose_files(int(plan_id)))


class ApiPlanPublish(BaseHandler):
    def post(self, plan_id: str):
        self.require_user()
        self.json({"item": plans_svc.publish_plan(int(plan_id))})


class ApiPlanVoid(BaseHandler):
    def post(self, plan_id: str):
        self.require_user()
        from app.services.plan_void import void_plan
        self.json({"item": void_plan(int(plan_id))})

