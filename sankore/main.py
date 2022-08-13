from pathlib import Path
from typing import NoReturn

from models import get_data
from views import run_ui

APP_NAME = "Sankore"
DATA_FILE = Path(__file__).joinpath("../../data.json").resolve(strict=True)


def main() -> NoReturn:
    DATA_FILE.touch(exist_ok=True)
    data = get_data(DATA_FILE.resolve(strict=True))
    exit_code = run_ui(APP_NAME, data)
    exit(exit_code)


if __name__ == "__main__":
    main()
