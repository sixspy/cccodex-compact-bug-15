import os

import tornado.ioloop

from app.main import make_app


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "7300"))
    app = make_app()
    app.listen(port, address=host)
    print(f"compact-lab listening on http://{host}:{port}")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
