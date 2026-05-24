#!/usr/bin/env python3
"""
Banking Demo Traffic Generator
==============================
Generates random loan applications to test performance, metrics, and alerts.

Usage:
    python generate_traffic.py 20      # Generate 20 transactions
    python generate_traffic.py 30      # Generate 30 transactions
    python generate_traffic.py 50      # Generate 50 transactions

This script:
- Uses existing banking-demo API endpoints
- Generates random customer profiles, loan amounts, terms, and purposes
- Measures end-to-end performance metrics
- Displays decision distribution and throughput statistics
- Populates Prometheus metrics for dashboard visualization
"""

import asyncio
import httpx
import json
import sys
import time
import os
from datetime import datetime
from typing import Optional

# Fix Unicode encoding on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
BANKING_DEMO_URL = "http://localhost:8005"
VALID_COUNTS = [20, 30, 50]


class TrafficGenerator:
    """Generate random loan application traffic for the banking demo."""
    
    def __init__(self, base_url: str = BANKING_DEMO_URL):
        self.base_url = base_url
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=300.0)
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.aclose()
    
    async def generate_traffic(self, count: int) -> dict:
        """Generate random transactions via the API."""
        if count not in VALID_COUNTS:
            raise ValueError(f"Invalid count. Must be one of {VALID_COUNTS}. Got {count}")
        
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        print(f"\n{'='*70}")
        print(f"[TRAFFIC GENERATOR] Banking Demo Traffic Generator")
        print(f"{'='*70}")
        print(f"Target: {self.base_url}")
        print(f"Transactions: {count}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        # Call the traffic generation endpoint
        try:
            url = f"{self.base_url}/api/generate-traffic/{count}"
            print(f"[API] Calling: {url}")
            print(f"[WAIT] This may take a few minutes...\n")
            
            response = await self.session.get(url)
            response.raise_for_status()
            
            results = response.json()
            
            # Display results
            self._display_results(results)
            
            return results
            
        except httpx.HTTPError as e:
            print(f"[HTTP_ERROR] HTTP Error: {e}")
            raise
        except Exception as e:
            print(f"[ERROR] Error: {e}")
            raise
    
    def _display_results(self, results: dict):
        """Display traffic generation results in a formatted table."""
        print(f"\n{'='*70}")
        print(f"[RESULTS] Traffic Generation Results")
        print(f"{'='*70}\n")
        
        # Summary statistics
        print(f"Total Transactions:        {results['total']}")
        print(f"Successful:                {results['total'] - results['errors']}")
        print(f"Errors:                    {results['errors']}\n")
        
        # Timing metrics
        print(f"Total Time:                {results['total_time_seconds']}s")
        print(f"Avg Time per Transaction:  {results['avg_time_per_transaction']}s")
        print(f"Throughput:                {results['transactions_per_second']} tx/sec\n")
        
        # Decision distribution
        print(f"{'Decision Distribution:':<30}")
        print(f"  [APPROVED]   Approved:   {results['approved']:>4} ({results['approval_rate']:>6.2f}%)")
        print(f"  [DECLINED]   Declined:   {results['declined']:>4} ({results['decline_rate']:>6.2f}%)")
        print(f"  [CONDITIONAL] Conditional: {results['conditional']:>4} ({results['conditional_rate']:>6.2f}%)\n")
        
        # Sample applications
        if results['applications']:
            print(f"{'='*70}")
            print(f"[APPS] Sample Applications (first 10)")
            print(f"{'='*70}\n")
            
            for i, app in enumerate(results['applications'][:10], 1):
                decision_icon = {
                    "APPROVED": "[OK]",
                    "DECLINED": "[NO]",
                    "CONDITIONALLY APPROVED": "[?]",
                    "UNKNOWN": "[?]",
                }.get(app['decision'], "[?]")
                
                print(f"{i:2d}. {app['app_id']:<35} | {app['customer']:<20} | GBP{app['amount']:>7,} | {app['term_months']:>2}mo | {decision_icon} {app['decision']}")
            
            if len(results['applications']) > 10:
                print(f"... and {len(results['applications']) - 10} more applications\n")
        
        print(f"\n{'='*70}")
        print(f"[SUCCESS] Traffic generation complete!")
        print(f"{'='*70}\n")
        
        print(f"[NEXT] Next Steps:")
        print(f"   1. Open Grafana: http://localhost:3000")
        print(f"   2. View dashboards to see performance metrics")
        print(f"   3. Check alerts in AlertManager: http://localhost:9093")
        print(f"   4. View Prometheus: http://localhost:9090\n")


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(f"Usage: python generate_traffic.py <count>")
        print(f"Valid counts: {', '.join(map(str, VALID_COUNTS))}")
        print(f"\nExample:")
        print(f"  python generate_traffic.py 20")
        print(f"  python generate_traffic.py 30")
        print(f"  python generate_traffic.py 50")
        sys.exit(1)
    
    try:
        count = int(sys.argv[1])
    except ValueError:
        print(f"[ERROR] Invalid count: {sys.argv[1]}. Must be an integer.")
        sys.exit(1)
    
    if count not in VALID_COUNTS:
        print(f"[ERROR] Invalid count: {count}. Must be one of {VALID_COUNTS}")
        sys.exit(1)
    
    try:
        async with TrafficGenerator() as generator:
            results = await generator.generate_traffic(count)
            
            # Exit with success
            sys.exit(0)
    
    except Exception as e:
        print(f"\n[ERROR] Traffic generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
