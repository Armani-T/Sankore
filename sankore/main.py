#!/usr/bin/env python3
from pathlib import Path
from typing import NoReturn

from models import get_data, save_data
from views import run_ui

APP_NAME = "Sankore"
DATA_FILE = Path(__file__).joinpath("../../data.json").resolve(strict=True)


def main() -> NoReturn:
    DATA_FILE.touch(exist_ok=True)
    path = DATA_FILE.resolve(strict=True)
    updated_data, exit_code = run_ui(APP_NAME, get_data(path))
    save_data(path, updated_data)
    exit(exit_code)


if __name__ == "__main__":
    main()
