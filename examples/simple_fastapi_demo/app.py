import os

from fastapi import FastAPI
from gino.ext.starlette import Gino
from pydantic import BaseModel

app = FastAPI()
db = Gino(
    app,
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", 5432),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASS", ""),
    database=os.getenv("DB_NAME", "postgres"),
)


class User(db.Model):
    __tablename__ = "simple_fastapi_demo_users"

    id = db.Column(db.BigInteger(), primary_key=True)
    nickname = db.Column(db.Unicode(), default="unnamed")


class UserModel(BaseModel):
    name: str


@app.get("/")
async def index():
    return {"message": "Hello, world!"}


@app.get("/users/{uid}")
async def get_user(uid: int):
    q = User.query.where(User.id == uid)
    return (await q.gino.first_or_404()).to_dict()


@app.post("/users")
async def add_user(user: UserModel):
    u = await User.create(nickname=user.name)
    return u.to_dict()


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
