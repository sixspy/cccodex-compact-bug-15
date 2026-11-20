import json

import tornado.web
from itsdangerous import BadSignature, URLSafeSerializer

from app.config import Config
from app.services.errors import ServiceError

serializer = URLSafeSerializer(Config.SECRET, salt="cc-compact-session")


class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self) -> None:
        self.set_header("Cache-Control", "no-store")

    def json(self, data, status: int = 200) -> None:
        self.set_status(status)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps(data, ensure_ascii=False))

    def read_json(self) -> dict:
        if not self.request.body:
            return {}
        try:
            data = json.loads(self.request.body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ServiceError("JSON 无效") from exc
        return data if isinstance(data, dict) else {}

    def current_user_name(self) -> str | None:
        raw = self.get_cookie(Config.COOKIE_NAME)
        if not raw:
            return None
        try:
            data = serializer.loads(raw)
        except BadSignature:
            return None
        if isinstance(data, dict) and data.get("user") == Config.ADMIN_USER:
            return data["user"]
        return None

    def require_user(self) -> str:
        user = self.current_user_name()
        if not user:
            raise ServiceError("未登录", 401)
        return user

    def write_error(self, status_code, **kwargs):
        err = kwargs.get("exc_info")
        if err and isinstance(err[1], ServiceError):
            self.json({"error": err[1].message}, err[1].status_code)
            return
        self.json({"error": "服务器错误"}, status_code)
