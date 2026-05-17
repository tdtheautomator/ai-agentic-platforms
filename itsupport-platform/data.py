"""
Dummy data for IT Support demo.

Users, ticket templates, knowledge base articles, and diagnostic results.
"""

USERS = [
    {"id": "USR001", "name": "Alex Turner", "dept": "Engineering", "device": "ThinkPad X1 Carbon", "os": "Windows 11 Pro 23H2", "tier": 2},
    {"id": "USR002", "name": "Priya Nair", "dept": "Finance", "device": "MacBook Pro M3", "os": "macOS Sonoma 14.4", "tier": 1},
    {"id": "USR003", "name": "Marcus Webb", "dept": "HR", "device": "Dell Latitude 5540", "os": "Windows 11 Home 22H2", "tier": 1},
    {"id": "USR004", "name": "Sakura Tanaka", "dept": "DevOps", "device": "Ubuntu Workstation", "os": "Ubuntu 24.04 LTS", "tier": 3},
    {"id": "USR005", "name": "Carlos Mendez", "dept": "Sales", "device": "Surface Pro 9", "os": "Windows 11 Pro 22H2", "tier": 1},
]

CATEGORIES = [
    "Network / VPN",
    "Software / Application",
    "Hardware / Peripherals",
    "Account / Access",
    "Performance / Crash",
    "Email / Calendar",
    "Security / Malware"
]

TICKET_TEMPLATES = [
    {"category": "Network / VPN", "priority": "HIGH", "description": "Cannot connect to VPN — error 800 timeout. Working from home. Have tried restarting router."},
    {"category": "Software / Application", "priority": "MEDIUM", "description": "Microsoft Teams crashes on startup after latest Windows update KB5034441. Other apps work fine."},
    {"category": "Account / Access", "priority": "HIGH", "description": "Locked out of Active Directory account after password reset attempt. Need access for client meeting in 2 hours."},
    {"category": "Hardware / Peripherals", "priority": "LOW", "description": "External monitor not detected via USB-C dock. Cable works on another laptop. Driver may be missing."},
    {"category": "Performance / Crash", "priority": "MEDIUM", "description": "Laptop extremely slow since this morning — 100% disk usage in Task Manager, suspected malware or runaway process."},
    {"category": "Email / Calendar", "priority": "LOW", "description": "Outlook calendar not syncing with Google Calendar integration. Missing meetings from last 3 days."},
    {"category": "Security / Malware", "priority": "CRITICAL", "description": "Suspicious pop-ups and browser redirects appearing. Antivirus showing multiple detections. May be compromised."},
]

KB_ARTICLES = [
    "VPN Error 800: Disable firewall on home router temporarily; ensure UDP port 500/4500 open; reinstall Cisco AnyConnect client.",
    "Teams crash after Windows Update: Clear Teams cache at %AppData%/Microsoft/Teams; run as administrator; check event viewer for error code.",
    "AD account lockout: Check lockout source via AD audit log; reset via IT admin portal; verify no auto-login scripts retrying old password.",
    "USB-C dock display issue: Update DisplayLink driver v10.2+; disable then re-enable display adapter; check dock firmware version.",
    "100% disk usage: Run 'chkdsk /f /r' on next reboot; disable Windows Search indexing; check for svchost.exe malware variant.",
    "Outlook calendar sync: Revoke and re-grant Google Calendar OAuth token; clear Outlook profile cache; check Exchange hybrid config.",
    "Malware infection protocol: Isolate machine from network immediately; boot from rescue USB; run Malwarebytes offline scan; reimage if rootkit detected.",
    "Remote desktop connection refused: Enable RDP in system properties; check Windows Firewall rule for port 3389; verify NLA settings.",
    "Printer spooler crash: Stop Print Spooler service; delete files in C:/Windows/System32/spool/PRINTERS; restart spooler.",
    "Blue screen IRQL_NOT_LESS_OR_EQUAL: Update or rollback recently installed driver; run memory diagnostics; check minidump in WinDbg.",
    "SSO login loop: Clear browser cookies and cache; disable browser extensions; check SAML assertion in network trace.",
    "OneDrive sync stuck: Sign out and back in; run 'onedrive /reset'; check for files with restricted characters in filename.",
    "Slow network on WiFi: Run 'netsh wlan show profile'; forget and reconnect; update wireless driver; check for 2.4GHz vs 5GHz band.",
    "Email stuck in Outbox: Check attachment size limits (25MB); repair Outlook profile; check SMTP authentication settings.",
    "Webcam not detected: Update USB controller drivers; check Device Manager for unknown devices; try different USB port.",
]

DIAG_RESULTS = {
    "Network / VPN": {"ping_gw": "OK", "dns": "FAIL", "vpn_service": "STOPPED", "last_event": "AuthenticationFailed", "uptime_h": 0.5},
    "Software / Application": {"cpu_pct": 45, "mem_pct": 62, "crash_log": "0xC0000005 ACCESS_VIOLATION", "last_update": "KB5034441", "pending_restart": True},
    "Account / Access": {"lockout_count": 5, "lockout_src": "WKSTN-SALES-03", "last_login": "2h ago", "pwd_expiry_days": 3, "mfa_enrolled": True},
    "Hardware / Peripherals": {"driver_ver": "9.8.0", "driver_latest": "10.2.1", "usb_events": 3, "display_adapter": "DisplayLink USB 4K"},
    "Performance / Crash": {"cpu_pct": 98, "disk_pct": 100, "top_proc": "SearchIndexer.exe", "malware_sigs": 0, "temp_c": 89},
    "Email / Calendar": {"oauth_valid": False, "last_sync": "72h ago", "inbox_count": 1203, "calendar_events_missing": 14},
    "Security / Malware": {"av_detections": 7, "quarantined": 3, "network_connections": 42, "suspicious_procs": ["svchost-fake.exe", "cryptominer.tmp"], "severity": "CRITICAL"},
}
