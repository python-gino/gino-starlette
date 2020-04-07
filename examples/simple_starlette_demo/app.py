import os

from gino.ext.starlette import Gino
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse

# Database Configuration
PG_URL = "postgresql://{user}:{password}@{host}:{port}/{database}".format(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", 5432),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASS", ""),
    database=os.getenv("DB_NAME", "postgres"),
)

# Initialize Starlette app
app = Starlette()

# Initialize Gino instance
db = Gino(app, dsn=PG_URL)


# Definition of table
class User(db.Model):
    __tablename__ = "simple_starlette_demo_users"

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


@app.on_event("startup")
async def create():
    await db.gino.create_all()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "5000")),
    )
