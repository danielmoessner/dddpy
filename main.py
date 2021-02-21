from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm.session import Session

from dddpy.domain.book.book_exeption import (
    BookAlreadyExistsError,
    BookNotFoundError,
    BooksNotFoundError,
)
from dddpy.infrastructure.sqlite.book.book_repository import BookRepositoryWithSession
from dddpy.infrastructure.sqlite.database import SessionLocal
from dddpy.presentation.schema.book.book_schema import BookCreateSchema, BookReadSchema
from dddpy.usecase.book.book_usecase import (
    BookUseCase,
    BookUseCaseImpl,
    BookUseCaseUnitOfWork,
)

app = FastAPI()


class ErrorMessage(BaseModel):
    detail: str = Field(example="error message.")


def get_session() -> Session:
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def book_usecase(session: Session = Depends(get_session)) -> BookUseCase:
    uow: BookUseCaseUnitOfWork = BookRepositoryWithSession(session)
    return BookUseCaseImpl(uow)


@app.post(
    "/books",
    response_model=BookReadSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorMessage,
            "description": BookAlreadyExistsError.message,
        },
    },
)
async def create_book(
    data: BookCreateSchema,
    book_usecase: BookUseCase = Depends(book_usecase),
):
    try:
        book = book_usecase.create_book(
            isbn=data.isbn,
            title=data.title,
            page=data.page,
        )
    except BookAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return book


@app.get(
    "/books",
    response_model=List[BookReadSchema],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorMessage,
            "description": BooksNotFoundError.message,
        },
    },
)
async def get_books(
    book_usecase: BookUseCase = Depends(book_usecase),
):
    try:
        books = book_usecase.create_book()
    except BooksNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return books


@app.get(
    "/books/{book_id}",
    response_model=BookReadSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorMessage,
            "description": BookNotFoundError.message,
        },
    },
)
async def get_book(
    book_id: str,
    book_usecase: BookUseCase = Depends(book_usecase),
):
    try:
        book = book_usecase.fetch_book_by_isbn(book_id)
    except BookNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return book


@app.delete(
    "/books/{book_id}",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorMessage,
            "description": BookNotFoundError.message,
        },
    },
)
async def delete_book(
    book_id: str,
    book_usecase: BookUseCase = Depends(book_usecase),
):
    try:
        book_usecase.delete_book_by_isbn(book_id)
    except BookNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
