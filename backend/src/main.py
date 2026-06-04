import src.models._rebuild
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.logging import setup_logging
from src.api import routes

setup_logging()

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(routes.router, prefix="/api")
