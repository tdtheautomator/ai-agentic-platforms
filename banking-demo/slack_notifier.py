"""
Slack Notification Integration for Banking Demo
================================================
Posts application outcomes and agent timing to Slack webhook.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any
from datetime import datetime


SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()


async def post_application_outcome(
    app_id: str,
    customer_name: str,
    decision: str,
    reason: str,
    agent_timings: Dict[str, float],
    total_time: float,
    loan_amount: int,
    loan_term: int,
    loan_purpose: str,
    credit_score: int,
) -> bool:
    """
    Post application outcome to Slack with agent timing breakdown.
    
    Args:
        app_id: Application ID
        customer_name: Customer name
        decision: Decision outcome (APPROVED, CONDITIONAL, DECLINED)
        reason: Decision reason
        agent_timings: Dict of agent names to duration in seconds
        total_time: Total pipeline execution time
        loan_amount: Loan amount in GBP
        loan_term: Loan term in months
        loan_purpose: Loan purpose
        credit_score: Customer credit score
    
    Returns:
        True if posted successfully, False otherwise
    """
    if not SLACK_WEBHOOK_URL:
        return False
    
    try:
        # Determine color based on decision
        color_map = {
            "APPROVED": "#36a64f",      # Green
            "CONDITIONAL": "#ff9900",   # Orange
            "DECLINED": "#e74c3c",      # Red
        }
        color = color_map.get(decision, "#95a5a6")
        
        # Build agent timing fields
        timing_fields = []
        for agent_name, duration in agent_timings.items():
            timing_fields.append({
                "title": f"{agent_name.title()} Agent",
                "value": f"{duration:.2f}s",
                "short": True
            })
        
        # Build Slack message
        payload = {
            "attachments": [
                {
                    "fallback": f"Loan Application {app_id}: {decision}",
                    "color": color,
                    "title": f"Loan Application {app_id}",
                    "title_link": f"http://localhost:8005",
                    "text": f"*Decision: {decision}*",
                    "fields": [
                        {
                            "title": "Customer",
                            "value": customer_name,
                            "short": True
                        },
                        {
                            "title": "Credit Score",
                            "value": str(credit_score),
                            "short": True
                        },
                        {
                            "title": "Loan Amount",
                            "value": f"£{loan_amount:,}",
                            "short": True
                        },
                        {
                            "title": "Loan Term",
                            "value": f"{loan_term} months",
                            "short": True
                        },
                        {
                            "title": "Purpose",
                            "value": loan_purpose[:50],
                            "short": False
                        },
                        {
                            "title": "Reason",
                            "value": reason[:200],
                            "short": False
                        },
                        {
                            "title": "Total Pipeline Time",
                            "value": f"{total_time:.2f}s",
                            "short": True
                        },
                    ] + timing_fields + [
                        {
                            "title": "Timestamp",
                            "value": datetime.utcnow().isoformat() + "Z",
                            "short": False
                        }
                    ],
                    "footer": "Banking Agent Platform",
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
        print(f"[Slack] Error posting notification: {e}")
        return False


async def post_pipeline_error(
    app_id: str,
    customer_name: str,
    error_message: str,
    agent: Optional[str] = None,
) -> bool:
    """
    Post pipeline error to Slack.
    
    Args:
        app_id: Application ID
        customer_name: Customer name
        error_message: Error details
        agent: Agent that failed (optional)
    
    Returns:
        True if posted successfully, False otherwise
    """
    if not SLACK_WEBHOOK_URL:
        return False
    
    try:
        payload = {
            "attachments": [
                {
                    "fallback": f"Pipeline Error for {app_id}",
                    "color": "#e74c3c",
                    "title": f"Pipeline Error - Application {app_id}",
                    "text": "*Status: ERROR*",
                    "fields": [
                        {
                            "title": "Customer",
                            "value": customer_name,
                            "short": True
                        },
                        {
                            "title": "Failed Agent",
                            "value": agent or "Unknown",
                            "short": True
                        },
                        {
                            "title": "Error Details",
                            "value": error_message[:200],
                            "short": False
                        },
                        {
                            "title": "Timestamp",
                            "value": datetime.utcnow().isoformat() + "Z",
                            "short": False
                        }
                    ],
                    "footer": "Banking Agent Platform",
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
        print(f"[Slack] Error posting error notification: {e}")
        return False
