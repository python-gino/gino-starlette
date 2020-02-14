from main import app


@app.get("/")
async def index():
    return {"message": "Hello, world!"}
