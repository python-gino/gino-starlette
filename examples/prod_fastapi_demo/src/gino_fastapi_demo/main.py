import logging
import click

from fastapi import FastAPI

from .models import db

try:
    from importlib.metadata import entry_points
except ImportError:  # pragma: no cover
    from importlib_metadata import entry_points

logger = logging.getLogger(__name__)


def get_app():
    app = FastAPI()
    db.init_app(app)
    for ep in entry_points()["gino_fastapi_demo.modules"]:
        logger.info(
            "Loading module: %s",
            ep.name,
            extra={
                "color_message": "Loading module: "
                + click.style("%s", fg="cyan")
            },
        )
        mod = ep.load()
        init_app = getattr(mod, "init_app", None)
        if init_app:
            init_app(app)
    return app
