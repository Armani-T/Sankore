#!/usr/bin/env python3
from pathlib import Path
from typing import NoReturn

from models import get_data, save_data
from views import run_ui

APP_NAME = "Sankore"
DATA_FILE = Path(__file__).joinpath("../../data.json").resolve()


def main() -> NoReturn:
    DATA_FILE.touch(exist_ok=True)
    updated_data, exit_code = run_ui(APP_NAME, get_data(DATA_FILE))
    save_data(DATA_FILE, updated_data)
    exit(exit_code)


if __name__ == "__main__":
    main()
