"""Transaction summary and Slack notification service."""

import json
import requests
from datetime import datetime
from typing import Optional
import os


class TransactionSummary:
    """Captures and formats transaction execution summaries."""
    
    def __init__(self, slack_webhook_url: Optional[str] = None):
        """Initialize transaction summary service.
        
        Args:
            slack_webhook_url: Slack webhook URL for notifications
        """
        self.slack_webhook_url = slack_webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.summaries = {}
    
    def capture(
        self,
        order_id: str,
        customer: dict,
        cart: list,
        subtotal: float,
        final_total: float,
        discount: float,
        shipping: float,
        final_status: str,
        warehouse: str,
        agent_timings: dict,
        tool_timings: dict,
        fraud_check: dict,
        promo: dict,
        dispatch_reasoning: str,
        validation_reasoning: str,
        fulfilment_reasoning: str,
        pricing_reasoning: str,
    ) -> dict:
        """Capture transaction summary.
        
        Args:
            order_id: Order ID
            customer: Customer data
            cart: Cart items
            subtotal: Subtotal amount
            final_total: Final total amount
            discount: Discount amount
            shipping: Shipping cost
            final_status: Final order status (confirmed/held_for_review/cancelled)
            warehouse: Warehouse used
            agent_timings: Dict of agent names to execution times
            tool_timings: Dict of tool names to execution times
            fraud_check: Fraud check result
            promo: Promotion result
            dispatch_reasoning: Reasoning from dispatch agent
            validation_reasoning: Reasoning from validation agent
            fulfilment_reasoning: Reasoning from fulfilment agent
            pricing_reasoning: Reasoning from pricing agent
            
        Returns:
            Transaction summary dict
        """
        summary = {
            "order_id": order_id,
            "timestamp": datetime.utcnow().isoformat(),
            "customer": {
                "id": customer.get("id"),
                "name": customer.get("name"),
                "tier": customer.get("tier"),
            },
            "input": {
                "items": cart,
                "item_count": len(cart),
                "subtotal": subtotal,
            },
            "output": {
                "discount": discount,
                "shipping": shipping,
                "final_total": final_total,
                "status": final_status,
                "warehouse": warehouse,
            },
            "reasoning": {
                "validation": validation_reasoning,
                "fulfilment": fulfilment_reasoning,
                "pricing": pricing_reasoning,
                "dispatch": dispatch_reasoning,
            },
            "fraud_check": {
                "score": fraud_check.get("score", 0),
                "requires_review": fraud_check.get("requires_review", False),
                "reason": fraud_check.get("reason", ""),
            },
            "promotion": {
                "code": promo.get("promo_code", "NONE"),
                "saving": promo.get("saving", 0),
            },
            "execution_times": {
                "agents": agent_timings,
                "tools": tool_timings,
                "total_agent_time": sum(agent_timings.values()),
                "total_tool_time": sum(tool_timings.values()),
            },
        }
        
        self.summaries[order_id] = summary
        return summary
    
    def send_to_slack(self, summary: dict) -> bool:
        """Send transaction summary to Slack.
        
        Args:
            summary: Transaction summary dict
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.slack_webhook_url:
            return False
        
        try:
            # Format Slack message
            message = self._format_slack_message(summary)
            
            # Send to Slack
            response = requests.post(
                self.slack_webhook_url,
                json=message,
                timeout=5
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending to Slack: {e}")
            return False
    
    def _format_slack_message(self, summary: dict) -> dict:
        """Format transaction summary as Slack message.
        
        Args:
            summary: Transaction summary dict
            
        Returns:
            Slack message dict
        """
        order = summary
        status = order["output"]["status"]
        
        # Color based on status
        color_map = {
            "confirmed": "#36a64f",  # Green
            "held_for_review": "#ff9900",  # Orange
            "cancelled": "#ff0000",  # Red
        }
        color = color_map.get(status, "#808080")
        
        # Status emoji
        emoji_map = {
            "confirmed": "✅",
            "held_for_review": "⚠️",
            "cancelled": "❌",
        }
        emoji = emoji_map.get(status, "ℹ️")
        
        # Format agent timings
        agent_timings_str = "\n".join([
            f"  • {agent}: {time:.3f}s"
            for agent, time in order["execution_times"]["agents"].items()
        ])
        
        # Format tool timings
        tool_timings_str = "\n".join([
            f"  • {tool}: {time:.3f}s"
            for tool, time in order["execution_times"]["tools"].items()
        ])
        
        # Format cart items
        items_str = "\n".join([
            f"  • {item['sku']}: {item['qty']} unit(s)"
            for item in order["input"]["items"]
        ])
        
        message = {
            "channel": "#ecommerce-demo",
            "username": "Order Processor",
            "attachments": [
                {
                    "fallback": f"Order {order['order_id']} - {status.upper()}",
                    "color": color,
                    "title": f"{emoji} Order {order['order_id']} - {status.upper().replace('_', ' ')}",
                    "title_link": f"http://localhost:8007/api/events/{order['order_id']}",
                    "fields": [
                        {
                            "title": "Customer",
                            "value": f"{order['customer']['name']} ({order['customer']['tier']})",
                            "short": True
                        },
                        {
                            "title": "Warehouse",
                            "value": order["output"]["warehouse"],
                            "short": True
                        },
                        {
                            "title": "Items",
                            "value": items_str or "No items",
                            "short": False
                        },
                        {
                            "title": "Pricing",
                            "value": f"Subtotal: £{order['input']['subtotal']:.2f}\nDiscount: £{order['output']['discount']:.2f}\nShipping: £{order['output']['shipping']:.2f}\n*Total: £{order['output']['final_total']:.2f}*",
                            "short": False
                        },
                        {
                            "title": "Fraud Check",
                            "value": f"Score: {order['fraud_check']['score']}\nReview Required: {order['fraud_check']['requires_review']}\nReason: {order['fraud_check']['reason']}",
                            "short": False
                        },
                        {
                            "title": "Promotion",
                            "value": f"Code: {order['promotion']['code']}\nSaving: £{order['promotion']['saving']:.2f}",
                            "short": False
                        },
                        {
                            "title": "Decision Reasoning",
                            "value": f"*Dispatch:* {order['reasoning']['dispatch'][:200]}...",
                            "short": False
                        },
                        {
                            "title": "Agent Execution Times",
                            "value": agent_timings_str,
                            "short": False
                        },
                        {
                            "title": "Tool Execution Times",
                            "value": tool_timings_str,
                            "short": False
                        },
                        {
                            "title": "Total Processing Time",
                            "value": f"Agents: {order['execution_times']['total_agent_time']:.3f}s\nTools: {order['execution_times']['total_tool_time']:.3f}s",
                            "short": False
                        },
                    ],
                    "footer": "E-Commerce Demo",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }
        
        return message
    
    def get_summary(self, order_id: str) -> Optional[dict]:
        """Get transaction summary by order ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Transaction summary dict or None if not found
        """
        return self.summaries.get(order_id)
