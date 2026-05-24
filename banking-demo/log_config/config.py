"""
Enterprise-grade structured logging configuration.

Integrates with Prometheus for metrics and provides JSON output
for log aggregation systems.
"""

import logging
import sys
from typing import Any

import structlog
from prometheus_client import Counter

# Prometheus metrics for logging
log_events_counter = Counter(
    "app_log_events_total",
    "Total log events emitted",
    ["level", "logger"],
)


def add_log_level(logger: Any, method_name: str, event_dict: dict) -> dict:
    """
    Add log level to event dict.
    
    Args:
        logger: The logger instance.
        method_name: The name of the called method (e.g., 'info', 'warning').
        event_dict: The event dictionary to be logged.
        
    Returns:
        Modified event dictionary with log level added.
    """
    event_dict["level"] = method_name.upper()
    return event_dict


def increment_prometheus_counter(logger: Any, method_name: str, event_dict: dict) -> dict:
    """
    Increment Prometheus counter for log events.
    
    Args:
        logger: The logger instance.
        method_name: The name of the called method.
        event_dict: The event dictionary to be logged.
        
    Returns:
        Unmodified event dictionary.
    """
    level = method_name.upper()
    logger_name = event_dict.get("logger", "unknown")
    log_events_counter.labels(level=level, logger=logger_name).inc()
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structlog with JSON output and Prometheus integration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    # Configure Python's standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            add_log_level,
            increment_prometheus_counter,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: The name of the logger (typically __name__).
        
    Returns:
        A structlog BoundLogger instance.
    """
    return structlog.get_logger(name)
