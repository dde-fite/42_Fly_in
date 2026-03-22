from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


def main() -> None:
    print(
        "\nDo not run this file directly!\n"
        " - For DEVELOPMENT use: fastapi dev\n"
        " - For PRODUCTION use: fastapi run"
    )


if __name__ == "__main__":
    main()
