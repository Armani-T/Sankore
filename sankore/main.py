#!/usr/bin/env python3
from pathlib import Path
from typing import NoReturn
import json

from models import Book
from views import run_ui

APP_NAME = "Sankore"
DATA_FILE = Path(__file__).joinpath("../../data.json").resolve()


def main() -> NoReturn:
    try:
        DATA_FILE.touch(exist_ok=True)
        json_data = json.load(DATA_FILE.open())
        data = [Book(**obj) for obj in json_data.get("books", ())]
        updated_data, exit_code = run_ui(APP_NAME, data)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        exit(1)
    else:
        string = json.dumps({"books": [book.to_dict() for book in updated_data]})
        DATA_FILE.write_text(string, "utf8")
        exit(exit_code)


if __name__ == "__main__":
    main()
