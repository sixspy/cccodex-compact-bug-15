from app.handlers.base import BaseHandler
from app.services import settings as settings_svc


class ApiSettings(BaseHandler):
    def get(self):
        self.require_user()
        self.json({"items": settings_svc.list_settings()})

    def post(self):
        self.require_user()
        body = self.read_json()
        item = settings_svc.update_setting(
            str(body.get("key") or ""),
            str(body.get("value") or ""),
        )
        self.json({"item": item})
