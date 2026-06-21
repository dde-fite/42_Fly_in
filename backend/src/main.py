import src.models._rebuild
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core import setup_logging, config
from src.api import routes

setup_logging()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_URL,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(routes.router, prefix="/api")


def main() -> None:
    print(
        "Server is intended to be run with the following command:\n"
        "fastapi run src/"
    )


if __name__ == "__main__":
    main()
