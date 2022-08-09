from pathlib import Path
from typing import NoReturn

from models import get_db
from views import run_ui

APP_NAME = "Sankore"
DATA_FILE = Path(__file__).joinpath("../../data.json").resolve(strict=True)


def main() -> NoReturn:
    data = get_data(DATA_FILE)
    exit_code = run_ui(APP_NAME, data)
    exit(exit_code)


if __name__ == "__main__":
    main()
