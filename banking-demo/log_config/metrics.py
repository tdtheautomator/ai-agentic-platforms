"""
Logging Metrics Module
======================

Tracks logging events and integrates with Prometheus for observability.
"""

from prometheus_client import Counter

class LogMetrics:
    """Centralized logging metrics."""
    
    # Log event counters
    log_events_total = Counter(
        "logging_events_total",
        "Total log events emitted",
        ["level", "logger", "component"]
    )
    
    # Agent-specific logging
    agent_logs_total = Counter(
        "agent_logs_total",
        "Agent-related log events",
        ["agent", "level", "event_type"]
    )
    
    # Harness-specific logging
    harness_logs_total = Counter(
        "harness_logs_total",
        "Harness-related log events",
        ["session_id", "level", "event_type"]
    )
    
    # Memory-specific logging
    memory_logs_total = Counter(
        "memory_logs_total",
        "Memory layer log events",
        ["memory_type", "level", "operation"]
    )
    
    # Tool-specific logging
    tool_logs_total = Counter(
        "tool_logs_total",
        "Tool execution log events",
        ["tool_name", "level", "status"]
    )
    
    @staticmethod
    def log_event(level: str, logger: str, component: str):
        """Record a log event."""
        LogMetrics.log_events_total.labels(
            level=level,
            logger=logger,
            component=component
        ).inc()
    
    @staticmethod
    def log_agent_event(agent: str, level: str, event_type: str):
        """Record an agent log event."""
        LogMetrics.agent_logs_total.labels(
            agent=agent,
            level=level,
            event_type=event_type
        ).inc()
    
    @staticmethod
    def log_harness_event(session_id: str, level: str, event_type: str):
        """Record a harness log event."""
        LogMetrics.harness_logs_total.labels(
            session_id=session_id,
            level=level,
            event_type=event_type
        ).inc()
    
    @staticmethod
    def log_memory_event(memory_type: str, level: str, operation: str):
        """Record a memory layer log event."""
        LogMetrics.memory_logs_total.labels(
            memory_type=memory_type,
            level=level,
            operation=operation
        ).inc()
    
    @staticmethod
    def log_tool_event(tool_name: str, level: str, status: str):
        """Record a tool execution log event."""
        LogMetrics.tool_logs_total.labels(
            tool_name=tool_name,
            level=level,
            status=status
        ).inc()
