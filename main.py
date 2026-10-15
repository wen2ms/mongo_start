from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymongo import MongoClient


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", env_file_encoding="utf-8")

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


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
