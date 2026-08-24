"""
Structured Audit Trail Logger.

Logs every CloudOps request event to both:
- audit_log.jsonl (Machine-readable JSON lines format)
- audit_log.txt   (Human-readable structured text format)
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

JSONL_FILE = Path("audit_log.jsonl")
TXT_FILE = Path("audit_log.txt")


def log_event(entry: Dict[str, Any]) -> None:
    """
    Logs an audit event record to audit_log.jsonl and audit_log.txt.
    
    Expected entry fields:
      - raw_request: str
      - action: str
      - target: str or None
      - risk: str
      - decision: str
      - approved_by: str or None
      - executed: bool
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    request_id = str(uuid.uuid4())

    log_record = {
        "timestamp": timestamp,
        "request_id": request_id,
        "raw_request": entry.get("raw_request", ""),
        "action": entry.get("action", "UNKNOWN"),
        "target": entry.get("target"),
        "risk": entry.get("risk", "UNKNOWN"),
        "decision": entry.get("decision", "UNKNOWN"),
        "approved_by": entry.get("approved_by"),
        "executed": entry.get("executed", False)
    }

    # 1. Append structured JSON line
    with open(JSONL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_record) + "\n")

    # 2. Append human-readable log line
    human_line = (
        f"[{timestamp}] ID: {request_id} | Request: \"{log_record['raw_request']}\" | "
        f"Action: {log_record['action']} | Target: {log_record['target']} | "
        f"Risk: {log_record['risk']} | Decision: {log_record['decision']} | "
        f"ApprovedBy: {log_record['approved_by']} | Executed: {log_record['executed']}\n"
    )
    with open(TXT_FILE, "a", encoding="utf-8") as f:
        f.write(human_line)
