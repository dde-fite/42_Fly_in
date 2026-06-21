from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles

app = Starlette()
app.mount("/", StaticFiles(directory="dist", html=True))


def main() -> None:
    print(
        "Server is intended to be run with the following command:\n"
        "granian --port 3000 --interface asgi main:app"
    )


if __name__ == "__main__":
    main()
