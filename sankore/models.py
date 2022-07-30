from dataclasses import dataclass
from typing import Iterable, MutableMapping

ALL_BOOKS = "All Books"


@dataclass
class Book:
    title: str
    author: str
    pages: int
    current_page: int = 0

    def __hash__(self):
        return hash(self.title)


@dataclass
class Library:
    description: str = ""
    books: Iterable[Book] = ()


already_read = Library(
    "The books that I haven't read yet but I intend to.",
    (
        Book("The Gallic War", "Julius Caesar", 470, 470),
        Book("The Civil War", "Julius Caesar", 368, 368),
        Book("Meditations", "Marcus Aurelius", 254, 254),
    ),
)
currently_reading = Library(
    "The books I am going through right now.",
    (
        Book("On The Ideal Orator", "Marcus Cicero", 384, 21),
        Book("Peace of Mind", "Lucius Seneca", 44, 22),
    ),
)
paused_reading = Library(
    "Books I stopped reading but that I'll get back to reading later.",
    (
        Book("Metamorphoses", "Ovid", 723, 551),
        Book("Aeneid", "Virgil", 442, 400),
    ),
)
to_read = Library(
    "The books that I haven't read yet but intend to.",
    (
        Book("On The Laws", "Marcus Cicero", 544),
        Book("History of the Peloponnesian War", "Thucydides", 648),
    ),
)

LIBRARIES: MutableMapping[str, Iterable[Book]] = {
    "To Read": (
        Book("On The Laws", "Marcus Cicero", 544),
        Book("History of the Peloponnesian War", "Thucydides", 648),
    ),
    "Already Read": (
        Book("The Gallic War", "Julius Caesar", 470, 470),
        Book("The Civil War", "Julius Caesar", 368, 368),
        Book("Meditations", "Marcus Aurelius", 254, 254),
    ),
    "Currently Reading": (
        Book("On The Ideal Orator", "Marcus Cicero", 384, 21),
        Book("Peace of Mind", "Lucius Seneca", 44, 22),
    ),
    "Reading Paused": (
        Book("Metamorphoses", "Ovid", 723),
        Book("Aeneid", "Virgil", 442),
    ),
}


def create_book(lib_name: str, new_book: Book) -> None:
    LIBRARIES[lib_name] = (*get_books(lib_name), new_book)


def change_library(old_lib: str, new_lib: str, book: Book) -> None:
    LIBRARIES[old_lib] = tuple(item for item in get_books(old_lib) if item != book)
    create_book(new_lib, book)


def get_book(title: str) -> Book:
    for book in get_books(ALL_BOOKS):
        if book.title == title:
            return book
    raise ValueError(f'No book with title "{title}" was found.')


def get_books(name) -> Iterable[Book]:
    return sum(LIBRARIES.values(), ()) if name == ALL_BOOKS else LIBRARIES[name]


def get_libraries(all_: bool = True) -> Iterable[str]:
    names = list(LIBRARIES.keys())
    if all_:
        names.insert(0, ALL_BOOKS)
    return names


def update_book(lib_name: str, old_title: str, new_book: Book) -> None:
    LIBRARIES[lib_name] = tuple(
        new_book if book.title == old_title else book for book in LIBRARIES[lib_name]
    )
