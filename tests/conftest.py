import os
import ssl

import gino
import pytest
from async_generator import async_generator, yield_
from gino.ext.starlette import Gino
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse

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
        conn = await request["connection"].get_raw_connection()
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
                (await request["connection"].first_or_404(q)).to_dict()
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
        await request["connection"].first_or_404(u.query)
        return JSONResponse(u.to_dict())

    e = await gino.create_engine(PG_URL)
    try:
        try:
            await db.gino.create_all(e)
            await yield_(app)
        finally:
            await db.gino.drop_all(e)
    finally:
        await e.close()


@pytest.fixture
@async_generator
async def app():
    await _app(
        host=DB_ARGS["host"],
        port=DB_ARGS["port"],
        user=DB_ARGS["user"],
        password=DB_ARGS["password"],
        database=DB_ARGS["database"],
    )


@pytest.fixture
@async_generator
async def app_factory():
    await _app(
        factory=True,
        host=DB_ARGS["host"],
        port=DB_ARGS["port"],
        user=DB_ARGS["user"],
        password=DB_ARGS["password"],
        database=DB_ARGS["database"],
    )


@pytest.fixture
def ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


@pytest.fixture
@async_generator
async def app_ssl(ssl_ctx):
    await _app(
        host=DB_ARGS["host"],
        port=DB_ARGS["port"],
        user=DB_ARGS["user"],
        password=DB_ARGS["password"],
        database=DB_ARGS["database"],
        ssl=ssl_ctx,
    )


@pytest.fixture
@async_generator
async def app_dsn():
    await _app(dsn=PG_URL)
