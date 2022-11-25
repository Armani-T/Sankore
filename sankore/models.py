from sqlite3 import Cursor
from typing import Any, Optional, Sequence, Union


class Book:
    def __init__(self, title: str, author: str, pages: int, rating: int) -> None:
        self.title = title
        self.author = author
        self.pages = pages
        self.rating = rating

    def current_run(self, cursor: Cursor) -> Optional[dict[str, Union[str, int]]]:
        run_info = cursor.execute(
            "SELECT start, page FROM ongoing_reads WHERE book_title = ?;",
            (self.title,),
        ).fetchone()
        return (
            {"start": run_info[0], "page": run_info[1]}
            if run_info is not None
            else None
        )

    def reads(self, cursor: Cursor) -> Sequence[dict[str, str]]:
        cursor.execute(
            "SELECT start, end_ FROM finished_reads WHERE book_title = ?;",
            (self.title,),
        )
        return [{"start": start, "end": end} for (start, end) in cursor.fetchall()]

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "author": self.author,
            "pages": self.pages,
            "rating": self.rating,
        }

    def to_tuple(self) -> tuple[str, str, int, int]:
        return (self.title, self.author, self.pages, self.rating)
