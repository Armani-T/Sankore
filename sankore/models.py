from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Cursor
from typing import Any, Iterable, Optional, Sequence, TypedDict

INIT_DB_SCRIPT = Path(__file__) / "../../assets/init.sql"

Data = Sequence["Book"]
Run = TypedDict("Run", {"start": Optional[str], "page": int})
Read = TypedDict("Read", {"start": Optional[str], "end": Optional[str]})


@dataclass(frozen=True, kw_only=True, slots=True, unsafe_hash=True)
class Book:
    title: str
    author: str
    pages: int
    rating: int

    def current_run(self, cursor: Cursor) -> Optional[Run]:
        run_info = cursor.execute(
            "SELECT (start, page) FROM ongoing_reads WHERE title = ?",
            (self.title,),
        ).fetchone()
        return (
            {"start": run_info[0], "page": run_info[1]}
            if run_info is not None
            else None
        )

    def reads(self, cursor: Cursor) -> Sequence[Read]:
        cursor.execute(
            "SELECT (start, end_) FROM finished_reads WHERE book_title = ?",
            (self.title,),
        )
        return [{"start": line[0], "end": line[1]} for line in cursor.fetchall()]

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "author": self.author,
            "pages": self.pages,
            "rating": self.rating,
        }

    def to_tuple(self) -> tuple[str, str, int, int]:
        return (self.title, self.author, self.pages, self.rating)
