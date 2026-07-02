import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Tests are hermetic by default: use the in-memory backend so a plain `pytest`
# never touches a real database or requires any env vars. Database-backed
# behaviour is still exercised by the parametrized `framework` fixture below,
# which builds its own self-initialized SQLite schema.
os.environ.setdefault("STORAGE_BACKEND", "memory")

import pytest

from src.core import ABTestFramework
from src.database import get_engine, get_session_factory, init_db
from src.storage import DatabaseStorage, InMemoryStorage


@pytest.fixture(params=["memory", "database"])
def framework(request):
    if request.param == "memory":
        return ABTestFramework(storage_backend=InMemoryStorage())
    else:
        # SQLite in-memory database for fast isolated DB tests
        engine = get_engine("sqlite:///:memory:")
        init_db(engine)
        session_factory = get_session_factory(engine)
        return ABTestFramework(storage_backend=DatabaseStorage(session_factory))


class _MockModelHandler(BaseHTTPRequestHandler):
    """Tiny real HTTP server used to test the http adapter end-to-end
    (no mocking library — this is an actual socket-listening server)."""

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        features = json.loads(body)
        status, payload = self.server.handler_fn(features)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if isinstance(payload, (dict, list)):
            self.wfile.write(json.dumps(payload).encode())
        else:
            self.wfile.write(str(payload).encode())

    def log_message(self, format, *args):
        pass  # silence default request logging to stderr


@pytest.fixture
def mock_model_server():
    """Start a real local HTTP server for adapter tests. Usage:

        url = mock_model_server(lambda features: (200, {"prediction": ...}))

    handler_fn receives the parsed request JSON and returns (status, payload).
    All servers started via this fixture are torn down at test end.
    """
    servers = []

    def _start(handler_fn):
        server = HTTPServer(("127.0.0.1", 0), _MockModelHandler)
        server.handler_fn = handler_fn
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_port}/predict"

    yield _start

    for s in servers:
        s.shutdown()
        s.server_close()
