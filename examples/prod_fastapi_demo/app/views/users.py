from main import app
from models.users import User


@app.get("/")
async def index():
    return {"message": "Hello, world!"}


@app.get("/users/{uid}")
async def get_user(uid: int):
    q = User.query.where(User.id == uid)
    return (await q.gino.first_or_404()).to_dict()


@app.post("/users")
async def add_user(nickname: str):
    u = await User.create(nickname=nickname)
    return u.to_dict()
