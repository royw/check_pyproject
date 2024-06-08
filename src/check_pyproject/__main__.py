import sys
from pathlib import Path
from loguru import logger
from check_pyproject.check_pyproject_toml import validate_pyproject_toml_file

# Default loguru format for colorized output
LOGURU_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
# removed the timestamp from the logs
LOGURU_MEDIUM_FORMAT = "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
# just the colorized message in the logs
LOGURU_SHORT_FORMAT = "<level>{message}</level>"


def main(args: list[str] = None) -> None:  # pragma: no cover
    """main function
    If 1 or more arguments are given, they will be passed to `validate_pyproject_toml_file`.
    Else, `validate_pyproject_toml_file` will be called with `$CWD/pyproject.toml`.
    """
    number_of_problems: int = 0
    logger.remove(None)
    logger.add(sys.stderr, level="DEBUG", format=LOGURU_SHORT_FORMAT)
    if not args:
        args: list[str] = sys.argv
    if len(args) == 1:
        args.append(str(Path.cwd() / "pyproject.toml"))
    for arg in args[1:]:
        if "--version" == arg:
            print(f"{__package__}: {sys.modules['check_pyproject'].version}")
        else:
            logger.info(f'Checking: "{arg}"')
            number_of_problems += validate_pyproject_toml_file(Path(arg))
    exit(number_of_problems)


if __name__ == "__main__":
    main()  # pragma: no cover
