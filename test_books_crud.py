from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymongo import MongoClient

from routes import router as book_router


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.test", env_file_encoding="utf-8")

    ATLAS_URI: str
    RETRY_WRITES: str
    DB_NAME: str


settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    client = MongoClient(settings.ATLAS_URI)

    try:
        client.admin.command("ping")
        app.state.mongodb_client = client
        app.state.database = client[settings.DB_NAME]
        print("Connected to the MongoDB database!")
        yield
    finally:
        client.close()
        print("MongoDB client closed.")


app = FastAPI(lifespan=lifespan)

app.include_router(book_router, tags=["books"], prefix="/book")


def test_create_book() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/book/", json={"title": "Don Quixote", "author": "Miguel de Cervantes", "synopsis": "..."}
        )
        assert response.status_code == 201
        body = response.json()
        assert body.get("title") == "Don Quixote"
        assert body.get("author") == "Miguel de Cervantes"
        assert body.get("synopsis") == "..."
        assert "_id" in body


def test_create_book_missing_title() -> None:
    with TestClient(app) as client:
        response = client.post("/book/", json={"author": "Miguel de Cervantes", "synopsis": "..."})
        assert response.status_code == 422


def test_create_book_missing_author() -> None:
    with TestClient(app) as client:
        response = client.post("/book/", json={"title": "Don Quixote", "author": "Miguel de Cervantes"})
        assert response.status_code == 422


def test_get_book() -> None:
    with TestClient(app) as client:
        new_book = client.post(
            "/book/", json={"title": "Don Quixote", "author": "Miguel de Cervantes", "synopsis": "..."}
        ).json()

        get_book_response = client.get("/book/" + new_book.get("_id"))
        assert get_book_response.status_code == 200
        assert get_book_response.json() == new_book


def test_get_book_unexisting() -> None:
    with TestClient(app) as client:
        get_book_response = client.get("/book/unexisting_id")
        assert get_book_response.status_code == 404


def test_update_book() -> None:
    with TestClient(app) as client:
        new_book = client.post(
            "/book/", json={"title": "Don Quixote", "author": "Miguel de Cervantes", "synopsis": "..."}
        ).json()

        response = client.put("/book/" + new_book.get("_id"), json={"title": "Don Quixote 1"})
        assert response.status_code == 200
        assert response.json().get("title") == "Don Quixote 1"


def test_update_book_unexisting() -> None:
    with TestClient(app) as client:
        get_book_response = client.put("/book/unexisting_id", json={"title": "Don Quixote 1"})
        assert get_book_response.status_code == 404


def test_delete_book() -> None:
    with TestClient(app) as client:
        new_book = client.post(
            "/book/", json={"title": "Don Quixote", "author": "Miguel de Cervantes", "synopsis": "..."}
        ).json()

        delete_book_response = client.delete("/book/" + new_book.get("_id"))
        assert delete_book_response.status_code == 204


def test_delete_book_unexisting() -> None:
    with TestClient(app) as client:
        delete_book_response = client.delete("/book/unexisting_id")
        assert delete_book_response.status_code == 404
