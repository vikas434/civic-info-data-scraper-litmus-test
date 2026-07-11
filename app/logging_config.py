"""Structlog configuration for the civic info benchmark."""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog for human-readable console output.

    Call once at application startup before any logging occurs.

    Args:
        log_level: Minimum log level to emit (DEBUG, INFO, WARNING, ERROR).
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=False),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.ExceptionRenderer(),
            structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )
