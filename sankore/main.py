from typing import NoReturn

from views import run_ui

APP_NAME = "Sankore"


def main() -> NoReturn:
    exit_code = run_ui(APP_NAME)
    exit(exit_code)


if __name__ == "__main__":
    main()
