import logging


def configure_logging():
    # Log event names/IDs only. Never log update bodies, prompts, tokens, or SQL parameters.
    logging.basicConfig(
        level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    for name in ("httpx", "httpcore", "aiogram.event", "sqlalchemy.engine", "pypdf"):
        logging.getLogger(name).setLevel(logging.ERROR)
