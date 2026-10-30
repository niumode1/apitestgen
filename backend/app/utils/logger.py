"""Logging configuration using loguru."""

import sys

from loguru import logger

from app.config import settings


def setup_logging() -> None:
    """Configure loguru for structured logging."""
    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        format=log_format,
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
    )

    # Always write to file
    logger.add(
        settings.data_path / "logs" / "app_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="DEBUG",
        rotation="00:00",
        retention=f"{settings.REPORTS_RETENTION_DAYS} days",
        compression="gz",
    )


__all__ = ["logger", "setup_logging"]
