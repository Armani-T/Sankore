from collections import namedtuple

Book = namedtuple("Book", ("title", "author", "pages"))

ALL_BOOKS = "All Books"

libraries = {
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

get_book_list = lambda name: (
    sum(libraries.values(), ()) if name == ALL_BOOKS else libraries[name]
)


def create_book(lib_name, title, author, pages):
    new_book = Book(title, author, pages)
    libraries[lib_name] = (*get_book_list(lib_name), new_book)


def get_library_names(all_=True):
    names = list(libraries.keys())
    if all_:
        names.insert(0, ALL_BOOKS)
    return names


def get_book(title):
    for book in get_book_list(ALL_BOOKS):
        if book.title == title:
            return book
    raise ValueError(f'No book with title "{title}" was found.')
