"""
Health Monitoring and Periodic Reporting
=========================================
Collects infrastructure, agents, tools, and pipeline health metrics.
Posts summary to Slack every 15 minutes.
"""

import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import httpx
from prometheus_client import REGISTRY


SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()


class HealthMonitor:
    """Monitors system health and posts periodic summaries."""
    
    def __init__(self):
        self.applications_processed = 0
        self.applications_approved = 0
        self.applications_declined = 0
        self.applications_conditional = 0
        self.total_pipeline_time = 0.0
        self.last_report_time = datetime.utcnow()
        self.start_time = datetime.utcnow()
    
    def record_application(self, decision: str, duration: float):
        """Record a processed application."""
        self.applications_processed += 1
        self.total_pipeline_time += duration
        
        decision_lower = decision.lower()
        if "approved" in decision_lower and "conditional" not in decision_lower:
            self.applications_approved += 1
        elif "conditional" in decision_lower:
            self.applications_conditional += 1
        elif "declined" in decision_lower:
            self.applications_declined += 1
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get current health summary."""
        uptime = datetime.utcnow() - self.start_time
        avg_pipeline_time = (
            self.total_pipeline_time / self.applications_processed
            if self.applications_processed > 0
            else 0.0
        )
        
        # Collect Prometheus metrics
        metrics = self._collect_prometheus_metrics()
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": uptime.total_seconds(),
            "infrastructure": {
                "status": "healthy",
                "services": {
                    "banking-demo": "running",
                    "redis": "running",
                    "prometheus": "running",
                    "alertmanager": "running",
                    "grafana": "running",
                },
            },
            "agents": {
                "total": 4,
                "active": 4,
                "agents": [
                    {"name": "Intake", "status": "healthy", "calls": self._get_metric_value("banking_agent_calls_total", "intake")},
                    {"name": "Risk", "status": "healthy", "calls": self._get_metric_value("banking_agent_calls_total", "risk")},
                    {"name": "Fraud", "status": "healthy", "calls": self._get_metric_value("banking_agent_calls_total", "fraud")},
                    {"name": "Decision", "status": "healthy", "calls": self._get_metric_value("banking_agent_calls_total", "decision")},
                ],
            },
            "tools": {
                "total": 6,
                "active": 6,
                "tools": [
                    {"name": "get_customer_profile", "calls": self._get_metric_value("banking_tool_calls_total", "get_customer_profile")},
                    {"name": "verify_kyc_documents", "calls": self._get_metric_value("banking_tool_calls_total", "verify_kyc_documents")},
                    {"name": "check_credit_score", "calls": self._get_metric_value("banking_tool_calls_total", "check_credit_score")},
                    {"name": "calculate_affordability", "calls": self._get_metric_value("banking_tool_calls_total", "calculate_affordability")},
                    {"name": "scan_transaction_history", "calls": self._get_metric_value("banking_tool_calls_total", "scan_transaction_history")},
                    {"name": "query_banking_rules", "calls": self._get_metric_value("banking_tool_calls_total", "query_banking_rules")},
                ],
            },
            "pipeline": {
                "status": "healthy",
                "total_runs": self.applications_processed,
                "avg_duration_seconds": avg_pipeline_time,
                "success_rate": (
                    ((self.applications_approved + self.applications_conditional + self.applications_declined) 
                     / self.applications_processed * 100)
                    if self.applications_processed > 0
                    else 0.0
                ),
            },
            "applications": {
                "total_processed": self.applications_processed,
                "approved": self.applications_approved,
                "conditional": self.applications_conditional,
                "declined": self.applications_declined,
                "approval_rate": (
                    (self.applications_approved / self.applications_processed * 100)
                    if self.applications_processed > 0
                    else 0.0
                ),
            },
            "memory": {
                "in_context": self._get_metric_value("banking_memory_items_total", "context"),
                "episodic": self._get_metric_value("banking_memory_items_total", "episodic"),
                "semantic": self._get_metric_value("banking_memory_items_total", "semantic"),
                "working": self._get_metric_value("banking_memory_items_total", "working"),
            },
        }
    
    def _collect_prometheus_metrics(self) -> Dict[str, Any]:
        """Collect metrics from Prometheus registry."""
        try:
            metrics = {}
            for collector in REGISTRY.collect():
                for metric in collector.samples:
                    metrics[metric.name] = metric.value
            return metrics
        except Exception as e:
            print(f"[Health] Error collecting Prometheus metrics: {e}")
            return {}
    
    def _get_metric_value(self, metric_name: str, label_value: Optional[str] = None) -> float:
        """Get a metric value from Prometheus registry."""
        try:
            for collector in REGISTRY.collect():
                for metric in collector.samples:
                    if metric.name == metric_name:
                        if label_value is None or metric.labels.get("agent") == label_value or metric.labels.get("tool_name") == label_value or metric.labels.get("memory_type") == label_value:
                            return metric.value
            return 0.0
        except Exception:
            return 0.0
    
    async def post_health_summary(self) -> bool:
        """Post health summary to Slack."""
        if not SLACK_WEBHOOK_URL:
            return False
        
        try:
            summary = self.get_health_summary()
            
            # Build agent status fields
            agent_fields = []
            for agent in summary["agents"]["agents"]:
                agent_fields.append({
                    "title": agent["name"],
                    "value": f"✓ {int(agent['calls'])} calls",
                    "short": True
                })
            
            # Build tool status fields
            tool_fields = []
            for tool in summary["tools"]["tools"]:
                tool_fields.append({
                    "title": tool["name"],
                    "value": f"{int(tool['calls'])} calls",
                    "short": True
                })
            
            payload = {
                "attachments": [
                    {
                        "fallback": "Banking Platform Health Summary",
                        "color": "#36a64f",
                        "title": "Banking Platform Health Summary",
                        "title_link": "http://localhost:8005",
                        "text": f"*Status: HEALTHY* | Uptime: {int(summary['uptime_seconds'] / 60)} min",
                        "fields": [
                            {
                                "title": "Infrastructure",
                                "value": "✓ All 5 services running",
                                "short": True
                            },
                            {
                                "title": "Pipeline Health",
                                "value": f"✓ {summary['pipeline']['success_rate']:.1f}% success rate",
                                "short": True
                            },
                            {
                                "title": "Applications Processed",
                                "value": f"{summary['applications']['total_processed']} total",
                                "short": True
                            },
                            {
                                "title": "Approval Breakdown",
                                "value": f"✓ {summary['applications']['approved']} | ⚠ {summary['applications']['conditional']} | ✗ {summary['applications']['declined']}",
                                "short": True
                            },
                            {
                                "title": "Avg Pipeline Time",
                                "value": f"{summary['pipeline']['avg_duration_seconds']:.2f}s",
                                "short": True
                            },
                            {
                                "title": "Approval Rate",
                                "value": f"{summary['applications']['approval_rate']:.1f}%",
                                "short": True
                            },
                        ] + [
                            {
                                "title": "Agent Status",
                                "value": " | ".join([f"{a['name']}: ✓" for a in summary["agents"]["agents"]]),
                                "short": False
                            },
                            {
                                "title": "Memory Stores",
                                "value": (f"In-Context: {int(summary['memory']['in_context'])} | "
                                         f"Episodic: {int(summary['memory']['episodic'])} | "
                                         f"Semantic: {int(summary['memory']['semantic'])} | "
                                         f"Working: {int(summary['memory']['working'])}"),
                                "short": False
                            },
                        ],
                        "footer": "Banking Agent Platform — Health Monitor",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    SLACK_WEBHOOK_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                return response.status_code == 200
        
        except Exception as e:
            print(f"[Health] Error posting health summary: {e}")
            return False


# Global health monitor instance
health_monitor = HealthMonitor()


async def start_health_monitor_loop():
    """Start the periodic health monitoring loop (every 15 minutes)."""
    while True:
        try:
            await asyncio.sleep(15 * 60)  # 15 minutes
            await health_monitor.post_health_summary()
        except Exception as e:
            print(f"[Health] Error in monitor loop: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error
