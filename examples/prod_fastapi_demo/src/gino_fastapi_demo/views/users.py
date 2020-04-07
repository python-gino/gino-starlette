from fastapi import APIRouter
from pydantic import BaseModel

from ..models.users import User

router = APIRouter()


class UserModel(BaseModel):
    name: str


@router.get("/users/{uid}")
async def get_user(uid: int):
    q = User.query.where(User.id == uid)
    return (await q.gino.first_or_404()).to_dict()


@router.post("/users")
async def add_user(user: UserModel):
    u = await User.create(nickname=user.name)
    return u.to_dict()


def init_app(app):
    app.include_router(router)
