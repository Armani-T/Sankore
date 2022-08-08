from pathlib import Path
from typing import NoReturn

from models import get_db
from views import run_ui

APP_NAME = "Sankore"
DB_FILE = Path(__file__).joinpath("../../data/libraries.dbm").resolve(strict=True)


def main() -> NoReturn:
    db = get_db(str(DB_FILE))
    exit_code = run_ui(APP_NAME, db)
    exit(exit_code)


if __name__ == "__main__":
    main()
