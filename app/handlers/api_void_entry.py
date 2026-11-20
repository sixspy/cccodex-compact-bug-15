from app.handlers.base import BaseHandler
from app.services.void_entry_ledger import append_ledger, dashboard
from app.services.void_entry_surface import reconcile_surface, snapshot


class ApiVoidEntryDash(BaseHandler):
    def get(self):
        self.require_user()
        self.json(dashboard())


class ApiVoidEntryNote(BaseHandler):
    def post(self):
        self.require_user()
        body = self.read_json()
        self.json(
            append_ledger(
                int(body.get("plan_id") or 0),
                str(body.get("note") or "作废仍启"),
            )
        )


class ApiVoidEntryHalf(BaseHandler):
    def post(self):
        self.require_user()
        self.json(reconcile_surface())


class ApiVoidEntrySnap(BaseHandler):
    def get(self):
        self.require_user()
        self.json(snapshot())
