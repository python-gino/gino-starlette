import subprocess
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from gino_fastapi_demo.asgi import app


@pytest.fixture
def client():
    cwd = Path(__file__).parent.parent
    subprocess.check_call(["alembic", "upgrade", "head"], cwd=cwd)
    with TestClient(app) as client:
        yield client
    subprocess.check_call(["alembic", "downgrade", "base"], cwd=cwd)
