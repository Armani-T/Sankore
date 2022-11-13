CREATE TABLE books (
  title TEXT NOT NULL,
  author TEXT NOT NULL,
  pages INTEGER NOT NULL,
  rating INTEGER DEFAULT 1,

  PRIMARY KEY (title, author)
);

CREATE TABLE quotes (
  text_ TEXT NOT NULL,
  book_title TEXT NOT NULL,

  PRIMARY KEY (text_, book_title),
  FOREIGN KEY (book_title) REFERENCES books (title)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

CREATE TABLE finished_reads (
  start TEXT,
  end_ TEXT,
  book_title TEXT NOT NULL,

  PRIMARY KEY (start, end_, book_title),
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
