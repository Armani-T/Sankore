from typing import NoReturn

from views import start_ui


def main() -> NoReturn:
    exit_code = start_ui()
    exit(exit_code)


if __name__ == "__main__":
    main()
