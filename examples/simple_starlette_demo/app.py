import asyncio
import os

import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse

from gino.ext.starlette import Gino

# Database Configuration
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

# Initialize Starlette app
app = Starlette()

# Initialize Gino object
db = Gino(dsn=PG_URL)
db.init_app(app)


# Definition of table
class User(db.Model):
    __tablename__ = "gino_users"

    id = db.Column(db.BigInteger(), primary_key=True)
    nickname = db.Column(db.Unicode(), default="unnamed")


# Definition of routes
@app.route("/")
async def index(request):
    return PlainTextResponse("Hello, world!")


@app.route("/users/{uid:int}")
async def get_user(request):
    uid = request.path_params.get("uid")
    q = User.query.where(User.id == uid)
    return JSONResponse((await q.gino.first_or_404()).to_dict())


@app.route("/users", methods=["POST"])
async def add_user(request):
    u = await User.create(nickname=(await request.json()).get("name"))
    return JSONResponse(u.to_dict())


async def create():
    await db.set_bind(PG_URL)
    await db.gino.create_all()
    await db.pop_bind().close()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(create())
    uvicorn.run(app, host="127.0.0.1", port=5000)
