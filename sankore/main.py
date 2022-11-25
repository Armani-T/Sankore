#!/usr/bin/env python3
from pathlib import Path
from sqlite3 import connect, Connection
from typing import NoReturn

from views import run_ui

APP_NAME = "sankore"  # NOTE: The app name should always be in lowercase.
DB_FILE = Path(__file__).joinpath(f"../../{APP_NAME}.sqlite3").resolve()
INIT_DB_SCRIPT = Path(__file__).joinpath("../../assets/init.sql").resolve()


def get_cursor(db_file: Path) -> Connection:
    initialise = not db_file.exists()
    db_file.touch(exist_ok=True)
    connection = connect(str(db_file))
    if initialise:
        script_text = INIT_DB_SCRIPT.read_text("utf8")
        init_cursor = connection.cursor()
        init_cursor.executescript(script_text)
        connection.commit()
        init_cursor.close()
    return connection


def main() -> NoReturn:
    cursor = get_cursor(DB_FILE)
    exit_code = run_ui(APP_NAME.title(), cursor)
    exit(exit_code)


if __name__ == "__main__":
    main()
