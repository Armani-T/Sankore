from typing import NoReturn

from views import run_ui


def main() -> NoReturn:
    exit_code = run_ui()
    exit(exit_code)


if __name__ == "__main__":
    main()
