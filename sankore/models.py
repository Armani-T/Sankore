from typing import Iterable, MutableMapping, NamedTuple

Book = NamedTuple("Book", (("title", str), ("author", str), ("pages", int)))

ALL_BOOKS = "All Books"

LIBRARIES: MutableMapping[str, Iterable[Book]] = {
    "To Read": (
        Book("On The Laws", "Marcus Cicero", 544),
        Book("History of the Peloponnesian War", "Thucydides", 648),
    ),
    "Already Read": (
        Book("The Gallic War", "Julius Caesar", 470),
        Book("The Civil War", "Julius Caesar", 368),
        Book("Meditations", "Marcus Aurelius", 254),
    ),
    "Currently Reading": (
        Book("On The Ideal Orator", "Marcus Cicero", 384),
        Book("Peace of Mind", "Lucius Seneca", 44),
    ),
    "Reading Paused": (
        Book("Metamorphoses", "Ovid", 723),
        Book("Aeneid", "Virgil", 442),
    ),
}


def create_book(lib_name: str, title: str, author: str, pages: int) -> None:
    new_book = Book(title, author, pages)
    LIBRARIES[lib_name] = (*get_book_list(lib_name), new_book)


def get_book(title: str) -> Book:
    for book in get_book_list(ALL_BOOKS):
        if book.title == title:
            return book
    raise ValueError(f'No book with title "{title}" was found.')


def get_book_list(name) -> Iterable[Book]:
    return sum(LIBRARIES.values(), ()) if name == ALL_BOOKS else LIBRARIES[name]


def get_library_names(all_: bool = True) -> Iterable[str]:
    names = list(LIBRARIES.keys())
    if all_:
        names.insert(0, ALL_BOOKS)
    return names
