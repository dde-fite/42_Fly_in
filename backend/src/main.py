from fastapi import FastAPI
from src.core.logging import setup_logging
from src.api import routes

setup_logging()

app = FastAPI()
app.include_router(routes.router, prefix="/api")
