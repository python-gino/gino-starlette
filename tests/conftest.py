import asyncio
import os
import socket
import ssl
import subprocess
from contextlib import closing
from pathlib import Path
from urllib.parse import urljoin

import asyncpg
import gino
import pytest
import requests
from gino.ext.starlette import Gino
from requests.adapters import HTTPAdapter
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from urllib3.util.retry import Retry

_MAX_INACTIVE_CONNECTION_LIFETIME = 59.0
DB_ARGS = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", 5432),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASS", ""),
    database=os.getenv("DB_NAME", "postgres"),
)
PG_URL = "postgresql://{user}:{password}@{host}:{port}/{database}".format(
    **DB_ARGS
)


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


class ProxyServerProtocol(asyncio.Protocol):
    def __init__(self, loop, target_host, target_port):
        self._loop = loop
        self._target_host = target_host
        self._target_port = target_port
        self._transport = None
        self._task = None
        self._eof_received = False
        self._buffer = []

    def connection_made(self, transport: asyncio.Transport):
        # transport.pause_reading()

        self._task = self._loop.create_task(
            self._loop.create_connection(
                lambda: ProxyClientProtocol(transport),
                self._target_host,
                self._target_port,
            )
        )

        def cb(task):
            self._task = None
            # noinspection PyBroadException
            try:
                self._transport = task.result()[0]
            except Exception:
                transport.close()
            else:
                # transport.resume_reading()
                for data in self._buffer:
                    self._transport.write(data)
                self._buffer.clear()
                if self._eof_received:
                    self._transport.write_eof()

        self._task.add_done_callback(cb)

    def data_received(self, data):
        if self._transport:
            self._transport.write(data)
        else:
            self._buffer.append(data)

    def pause_writing(self):
        self._transport.pause_reading()

    def resume_writing(self):
        self._transport.resume_reading()

    def eof_received(self):
        self._eof_received = True
        if self._transport:
            self._transport.write_eof()
        return True

    def connection_lost(self, exc):
        if self._task:
            self._task.cancel()
        if self._transport:
            self._transport.close()


class ProxyClientProtocol(asyncio.Protocol):
    def __init__(self, transport):
        self._trans = transport

    def data_received(self, data):
        self._trans.write(data)

    def pause_writing(self):
        self._trans.pause_reading()

    def resume_writing(self):
        self._trans.resume_reading()

    def eof_received(self):
        self._trans.write_eof()
        return True

    def connection_lost(self, exc):
        self._trans.close()


async def _app(**kwargs):
    app = Starlette()
    kwargs.update(
        {
            "kwargs": dict(
                max_inactive_connection_lifetime=_MAX_INACTIVE_CONNECTION_LIFETIME,
            ),
        }
    )
    factory = kwargs.pop("factory", False)
    db_delayed = kwargs.pop("db_delayed", False)
    if db_delayed:

        async def start_proxy(_port):
            loop = asyncio.get_event_loop()
            app.db_proxy = await loop.create_server(
                lambda: ProxyServerProtocol(
                    loop, DB_ARGS["host"], DB_ARGS["port"]
                ),
                "localhost",
                _port,
                reuse_address=True,
                reuse_port=True,
            )
            return app.db_proxy

        server = await start_proxy(0)
        for s in server.sockets:
            try:
                host, port = s.getsockname()
                break
            except ValueError:
                pass
        server.close()
        await server.wait_closed()
        app.start_proxy = lambda: start_proxy(port)
        kwargs["host"] = host
        kwargs["port"] = port
        kwargs["retry_limit"] = 4
        kwargs["retry_interval"] = 0.5

    if factory:
        db = Gino(**kwargs)
        db.init_app(app)
    else:
        db = Gino(app, **kwargs)

    class User(db.Model):
        __tablename__ = "gino_users"

        id = db.Column(db.BigInteger(), primary_key=True)
        nickname = db.Column(db.Unicode(), default="noname")

    @app.route("/")
    async def root(request):
        conn = await request["connections"][0].get_raw_connection()
        # noinspection PyProtectedMember
        assert (
            conn._holder._max_inactive_time == _MAX_INACTIVE_CONNECTION_LIFETIME
        )
        return PlainTextResponse("Hello, world!")

    @app.route("/users/{uid:int}")
    async def get_user(request):
        uid = request.path_params.get("uid")
        method = request.query_params.get("method")
        q = User.query.where(User.id == uid)
        if method == "1":
            return JSONResponse((await q.gino.first_or_404()).to_dict())
        elif method == "2":
            return JSONResponse(
                (await request["connections"][0].first_or_404(q)).to_dict()
            )
        elif method == "3":
            return JSONResponse((await db.bind.first_or_404(q)).to_dict())
        elif method == "4":
            return JSONResponse((await db.first_or_404(q)).to_dict())
        else:
            return JSONResponse((await User.get_or_404(uid)).to_dict())

    @app.route("/users", methods=["POST"])
    async def add_user(request):
        u = await User.create(nickname=(await request.json()).get("name"))
        await u.query.gino.first_or_404()
        await db.first_or_404(u.query)
        await db.bind.first_or_404(u.query)
        await request["connections"][0].first_or_404(u.query)
        return JSONResponse(u.to_dict())

    e = await gino.create_engine(PG_URL)
    try:
        try:
            await db.gino.create_all(e)
            yield app
        finally:
            await db.gino.drop_all(e)
    finally:
        await e.close()


@pytest.fixture
async def app():
    async for a in _app(
        host=DB_ARGS["host"],
        port=DB_ARGS["port"],
        user=DB_ARGS["user"],
        password=DB_ARGS["password"],
        database=DB_ARGS["database"],
    ):
        yield a


@pytest.fixture
async def app_factory():
    async for a in _app(
        factory=True,
        host=DB_ARGS["host"],
        port=DB_ARGS["port"],
        user=DB_ARGS["user"],
        password=DB_ARGS["password"],
        database=DB_ARGS["database"],
    ):
        yield a


@pytest.fixture
def ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


@pytest.fixture
async def app_ssl(ssl_ctx):
    async for a in _app(
        host=DB_ARGS["host"],
        port=DB_ARGS["port"],
        user=DB_ARGS["user"],
        password=DB_ARGS["password"],
        database=DB_ARGS["database"],
        ssl=ssl_ctx,
    ):
        yield a


@pytest.fixture
async def app_dsn():
    async for a in _app(dsn=PG_URL):
        yield a


@pytest.fixture
async def app_db_delayed():
    async for a in _app(
        host=DB_ARGS["host"],
        port=DB_ARGS["port"],
        user=DB_ARGS["user"],
        password=DB_ARGS["password"],
        database=DB_ARGS["database"],
        db_delayed=True,
    ):
        yield a


@pytest.fixture(
    params=[
        ("simple_starlette_demo", "requirements.txt", "app.py"),
        ("simple_fastapi_demo", "requirements.txt", "app.py"),
        ("prod_fastapi_demo", "pyproject.toml", "run.py"),
    ],
    ids=["simple_starlette_demo", "simple_fastapi_demo", "prod_fastapi_demo"],
)
def venv_client(virtualenv, request, pytestconfig):
    demo, install, run = request.param
    cwd = Path(__file__).parent.parent.absolute()
    run_with_coverage = [virtualenv.python, virtualenv.coverage, "run", "-p"]
    base_path = cwd / "examples" / demo
    env = virtualenv.env.copy()
    env.update(
        {
            k: v
            for k, v in os.environ.items()
            if k.startswith("DB_") or k.startswith("APP_")
        }
    )
    virtualenv.run("pip install coverage")
    if install == "requirements.txt":
        virtualenv.run("pip install -r requirements.txt", cwd=base_path)
    else:
        virtualenv.run("pip install poetry", cwd=base_path)
        virtualenv.run("poetry install", cwd=base_path)
        virtualenv.run(
            run_with_coverage
            + [
                "--source=src,migrations/versions",
                virtualenv.virtualenv / "bin" / "pytest",
            ],
            cwd=base_path,
            env=env,
        )
        virtualenv.run(
            run_with_coverage
            + [
                "--source=src,migrations/versions",
                virtualenv.virtualenv / "bin" / "alembic",
                "upgrade",
                "head",
            ],
            cwd=base_path,
            env=env,
        )

    port = find_free_port()

    class Client(requests.Session):
        def request(self, method, url, *args, **kwargs):
            url = urljoin("http://localhost:{}".format(port), url)
            return super().request(method, url, *args, **kwargs)

    client = Client()

    retries = Retry(
        total=6, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
    )

    client.mount("http://", HTTPAdapter(max_retries=retries))

    try:
        args = run_with_coverage.copy()
        if getattr(pytestconfig.option, "cov_source", None):
            source_dirs = ",".join(pytestconfig.option.cov_source)
            args += ["--source=%s" % source_dirs]
        args.append(base_path / run)
        with subprocess.Popen(args, env={"APP_PORT": str(port), **env}) as p:
            try:
                client.get("/").raise_for_status()
                yield client
            finally:
                p.terminate()
                if install == "requirements.txt":

                    async def tear_down():
                        conn = await asyncpg.connect(PG_URL)
                        await conn.execute("DROP TABLE {}_users".format(demo))
                        await conn.close()

                    asyncio.get_event_loop().run_until_complete(tear_down())
    finally:
        if install != "requirements.txt":
            virtualenv.run(
                run_with_coverage
                + [
                    "--source=src,migrations/versions",
                    virtualenv.virtualenv / "bin" / "alembic",
                    "downgrade",
                    "base",
                ],
                cwd=base_path,
                env=env,
            )
