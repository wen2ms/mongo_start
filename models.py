import uuid

from pydantic import BaseModel, ConfigDict, Field


class Book(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    title: str
    author: str
    synopsis: str

    model_config = ConfigDict(
        validate_by_name=True,
        validate_by_alias=True,
        json_schema_extra={
            "example": {
                "_id": "066de609-b04a-4b30-b46c-32537c7f1f6e",
                "title": "Don Quixote",
                "author": "Miguel de Cervantes",
                "synopsis": "...",
            },
        },
    )


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    synopsis: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Don Quixote",
                "author": "Miguel de Cervantes",
                "synopsis": "Don Quixote is a Spanish novel by Miguel de Cervantes...",
            },
        },
    )
