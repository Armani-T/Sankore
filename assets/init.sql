CREATE TABLE books (
  title TEXT PRIMARY KEY,
  author TEXT NOT NULL,
  pages INTEGER NOT NULL,
  rating INTEGER DEFAULT null
);

CREATE TABLE quotes (
  text_ TEXT PRIMARY KEY,
  author TEXT NOT NULL,
  update_date TEXT NOT NULL
);

CREATE TABLE finished_reads (
  book_title TEXT NOT NULL,
  start TEXT,
  end_ TEXT,

  PRIMARY KEY (book_title, start, end_),
  FOREIGN KEY (book_title) REFERENCES books (title)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

CREATE TABLE ongoing_reads (
  book_title TEXT PRIMARY KEY,
  start TEXT NOT NULL,
  page INTEGER DEFAULT 1,

  FOREIGN KEY (book_title) REFERENCES books (title)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);
