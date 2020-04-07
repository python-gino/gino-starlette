from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def index():
    return {"message": "Hello, world!"}


def init_app(app):
    app.include_router(router)
