from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from pymongo.errors import DuplicateKeyError

from models import Book, BookUpdate

router = APIRouter()


@router.post("/", response_description="Create a new book", status_code=status.HTTP_201_CREATED)
def create_book(request: Request, book: Book) -> Book:
    document = jsonable_encoder(book, by_alias=True)
    try:
        new_book = request.app.state.database["books"].insert_one(document)
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Book already exists.") from exc
    created_book = request.app.state.database["books"].find_one({"_id": new_book.inserted_id})
    return created_book


@router.get("/", response_description="List all books")
def list_books(request: Request) -> list[Book]:
    books = list(request.app.state.database["books"].find(limit=100))
    return books


@router.get("/{id}", response_description="Get a single book by id")
def find_book(id: str, request: Request) -> Book:
    if (book := request.app.state.database["books"].find_one({"_id": id})) is not None:
        return book
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book with ID {id} not found")


@router.put("/{id}", response_description="Update a book")
def update_book(id: str, request: Request, book: BookUpdate) -> Book:
    updated_book = book.model_dump(exclude_unset=True)
    if updated_book:
        update_result = request.app.state.database["books"].update_one({"_id": id}, {"$set": updated_book})
        if update_result.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book with ID {id} not found")
    if (existing_book := request.app.state.database["books"].find_one({"_id": id})) is not None:
        return existing_book
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book with ID {id} not found")


@router.delete("/{id}", response_description="Delete a book")
def delete_book(id: str, request: Request, response: Response) -> Response:
    delete_result = request.app.state.database["books"].delete_one({"_id": id})
    if delete_result.deleted_count == 1:
        response.status_code = status.HTTP_204_NO_CONTENT
        return response
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book with ID {id} not found")
