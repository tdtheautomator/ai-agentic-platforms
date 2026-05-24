"""
Structured Logging Module
=========================

Provides enterprise-grade logging with:
- Structured logging via structlog
- Prometheus metrics integration
- JSON output for log aggregation
- Context-aware logging for agents, harness, and memory layers
"""

from .config import configure_logging, get_logger
from .metrics import LogMetrics

__all__ = ["configure_logging", "get_logger", "LogMetrics"]
