import uvicorn
from fastapi import FastAPI

from config import BaseConfig
from gino_starlette import Gino

# Initialize FastAPI app
app = FastAPI()

# Initialize Gino object
db = Gino(dsn=BaseConfig.PG_URL)
db.init_app(app)

from views import *

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
