import tornado.web

from app.config import Config
from app.handlers.base import BaseHandler, serializer
from app.services.errors import ServiceError


class LoginPage(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "text/html; charset=utf-8")
        with open("static/login.html", "rb") as f:
            self.write(f.read())


class SpaPage(BaseHandler):
    def get(self):
        if not self.current_user_name():
            self.redirect("/login")
            return
        self.set_header("Content-Type", "text/html; charset=utf-8")
        with open("static/index.html", "rb") as f:
            self.write(f.read())


class RootHandler(BaseHandler):
    def get(self):
        if self.current_user_name():
            self.redirect("/app/")
        else:
            self.redirect("/login")


class ApiLogin(BaseHandler):
    def post(self):
        body = self.read_json()
        user = str(body.get("username", "")).strip()
        pwd = str(body.get("password", ""))
        if user != Config.ADMIN_USER or pwd != Config.ADMIN_PASSWORD:
            raise ServiceError("账号或密码错误")
        token = serializer.dumps({"user": user})
        self.set_cookie(Config.COOKIE_NAME, token, httponly=True, path="/")
        self.json({"ok": True, "user": user})


class ApiLogout(BaseHandler):
    def post(self):
        self.clear_cookie(Config.COOKIE_NAME, path="/")
        self.json({"ok": True})


class ApiMeta(BaseHandler):
    def get(self):
        self.require_user()
        self.json({"lab": Config.LAB_NAME, "product": "cc-compact-lab"})
