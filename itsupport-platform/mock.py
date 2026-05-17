"""
Mock responses for IT Support demo.

Deterministic fallback responses when LLM is unavailable.
"""

from data import DIAG_RESULTS


def _mock_response(agent_id: str, ctx: dict) -> str:
    """Generate mock response for agent based on context."""
    cat = ctx.get("category", "Unknown")
    prio = ctx.get("priority", "MEDIUM").upper()  # Normalize to uppercase
    user = ctx.get("user_name", "the user")
    diag = ctx.get("diag", {})
    outage = ctx.get("outage", False)
    sla_warn = ctx.get("sla_warn", False)
    tier = ctx.get("tier", 1)

    if agent_id == "triage":
        sev = "a P1 incident" if prio == "CRITICAL" else f"a {prio}-priority ticket"
        cause = {
            "Network / VPN": "VPN client or DNS failure",
            "Software / Application": "post-update application conflict",
            "Account / Access": "AD lockout from failed authentication",
            "Hardware / Peripherals": "missing or outdated device driver",
            "Performance / Crash": "runaway process or disk I/O saturation",
            "Email / Calendar": "OAuth token expiry or sync service failure",
            "Security / Malware": "active malware infection"
        }.get(cat, "unknown root cause")
        return (f"Ticket from {user} classified as {sev} under '{cat}'. "
                f"Most likely root cause: {cause}.")

    if agent_id == "diagnostic":
        if cat == "Network / VPN":
            return ("DNS resolution failure confirmed — DNS service returning NXDOMAIN for corporate domain. "
                    "VPN service stopped on client; root cause likely recent Windows Defender update blocking AnyConnect driver. Confidence: HIGH.")
        if cat == "Security / Malware":
            procs = diag.get("suspicious_procs", ["unknown"])
            return (f"Active malware detected: {procs[0] if procs else 'unknown process'} identified as cryptocurrency miner variant. "
                    f"{diag.get('av_detections', 0)} antivirus detections; machine should be isolated immediately. Confidence: HIGH.")
        if cat == "Performance / Crash":
            return (f"Disk I/O saturation at {diag.get('disk_pct', 100)}% caused by {diag.get('top_proc', 'SearchIndexer.exe')}. "
                    f"CPU temperature {diag.get('temp_c', 89)}C indicates thermal throttling contributing to sluggishness. Confidence: HIGH.")
        return (f"Diagnostic scan completed for {cat} issue on {ctx.get('device', 'device')}. "
                f"Primary failure point identified in {cat.lower()} subsystem. Confidence: MEDIUM.")

    if agent_id == "resolution":
        steps = {
            "Network / VPN": "1. Run 'ipconfig /flushdns && ipconfig /release && ipconfig /renew' in admin CMD. 2. Reinstall Cisco AnyConnect from the IT portal. 3. Reconnect VPN and verify with 'nslookup corp.internal'. Expected: VPN connects within 60 seconds.",
            "Software / Application": "1. Close Teams, clear cache at %AppData%/Microsoft/Teams. 2. Right-click Teams shortcut and run as administrator. 3. If crash persists, uninstall Teams and reinstall from Microsoft Store. Expected: Teams launches without crash.",
            "Account / Access": "1. IT admin unlocks account via AD Users and Computers. 2. User resets password via self-service portal (id.company.com). 3. Clear saved credentials in Windows Credential Manager. Expected: Login succeeds immediately.",
            "Hardware / Peripherals": "1. Download DisplayLink Driver 10.2.1 from IT software portal. 2. Uninstall old driver in Device Manager, reboot. 3. Install new driver and reconnect dock. Expected: Monitor detected within 30 seconds of reconnect.",
            "Performance / Crash": "1. Open Task Manager and end SearchIndexer.exe process tree. 2. Run 'services.msc', disable Windows Search service, reboot. 3. Run Malwarebytes quick scan to rule out malware. Expected: Disk usage drops below 30% within 2 minutes.",
            "Email / Calendar": "1. In Outlook, go to File > Account Settings and remove Google Calendar integration. 2. Re-add integration and grant all calendar permissions. 3. Run 'Send/Receive All Folders' (F9). Expected: Missing events appear within 5 minutes.",
            "Security / Malware": "1. Disconnect machine from network (unplug LAN, disable WiFi). 2. Boot from IT rescue USB and run offline Malwarebytes scan. 3. Submit scan report to security team; await reimage decision. Expected: Threat contained; await security team sign-off.",
        }
        return steps.get(cat,
                         f"1. Restart the affected service or application. 2. Apply latest patches from Windows Update. 3. Contact L2 support if issue persists after restart. Expected: Issue resolved or escalated within SLA window.")

    if agent_id == "escalation":
        if prio == "CRITICAL" or cat == "Security / Malware":
            return (f"EMERGENCY PROTOCOL: Security incident requires immediate L3 SOC engagement and machine isolation. "
                    f"Escalate to security team now; do not wait for user confirmation.")
        if sla_warn or outage:
            return (f"ESCALATE L3: SLA clock running — notify incident manager and affected user's manager now.")
        if outage:
            return (f"ESCALATE L3: Pattern detected across {ctx.get('affected', 0)} users suggests service-level outage — "
                    f"infrastructure team must investigate VPN concentrator or DNS server.")
        if tier >= 2 and prio in ("HIGH", "MEDIUM"):
            return (f"ESCALATE L2: Resolution steps provided but tier-{tier} user requires hands-on assistance. "
                    f"Assign to on-call L2 engineer; SLA {'WARNING — ' if sla_warn else ''}{'breach imminent' if sla_warn else 'within target'}.")
        return (f"AUTO-RESOLVE: Resolution steps have been sent to {user} via email and ticket portal. "
                f"Auto-close in 48 hours if no response; CSAT survey will be triggered on closure.")

    return f"[{agent_id}] Analysis complete for ticket {ctx.get('ticket_id', 'N/A')}."
