from app.handlers.base import BaseHandler
from app.services import files as files_svc
from app.services.errors import ServiceError


class ApiFiles(BaseHandler):
    def get(self):
        self.require_user()
        table = self.get_argument("table_name", default="") or None
        self.json(
            {
                "items": files_svc.list_files(table),
                "stats": files_svc.table_stats(),
            }
        )

    def post(self):
        self.require_user()
        body = self.read_json()
        try:
            size = int(body.get("size_bytes"))
        except (TypeError, ValueError) as exc:
            raise ServiceError("size_bytes 无效") from exc
        item = files_svc.register_file(
            str(body.get("path") or ""),
            str(body.get("table_name") or ""),
            size,
        )
        self.json({"item": item})


class ApiFileVoid(BaseHandler):
    def post(self, file_id: str):
        self.require_user()
        self.json({"item": files_svc.void_file(int(file_id))})
