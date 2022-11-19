#!/usr/bin/env python3
from pathlib import Path
from typing import NoReturn

from models import get_cursor
from views import run_ui

APP_NAME = "sankore"  # NOTE: The app name should always be in lowercase.
DB_FILE = Path(__file__).joinpath(f"../../{APP_NAME}.sqlite3").resolve()


def main() -> NoReturn:
    cursor = get_cursor(DB_FILE)
    exit_code = run_ui(APP_NAME.title(), cursor)
    exit(exit_code)


if __name__ == "__main__":
    main()
