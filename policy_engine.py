"""
Policy Engine — Security & Risk Enforcement Layer.

This layer NEVER calls Gemini or any LLM. It works purely off the structured
'action' string parsed by gemini_client.py.

LLMs only extract intent; deterministic software policies enforce authorization and safety.
"""

from typing import Dict, Any, Optional

# Hardcoded Risk Classification Table
RISK_TABLE: Dict[str, str] = {
    "READ_EC2": "LOW",
    "READ_S3": "LOW",
    "READ_ACCOUNT": "LOW",
    "STOP_EC2": "HIGH",
    "START_EC2": "HIGH",
    "TERMINATE_EC2": "CRITICAL",
    "DELETE_S3": "CRITICAL",
    "DELETE_ACCOUNT": "CRITICAL",
    "GREETING": "LOW",
    "EXPLAIN_AWS": "LOW",
    "UNKNOWN": "N/A"
}

# Decision Mapping based on Risk Level
DECISION_MAP: Dict[str, str] = {
    "LOW": "EXECUTE",
    "HIGH": "REQUIRE_APPROVAL",
    "CRITICAL": "BLOCK",
    "N/A": "CLARIFY"
}


def classify(action: str) -> str:
    """
    Classifies the risk level of an action.
    Returns: 'LOW', 'HIGH', 'CRITICAL', or 'N/A'
    """
    clean_action = action.upper() if action else "UNKNOWN"
    return RISK_TABLE.get(clean_action, "N/A")


def enforce(action: str, target: Optional[str] = None) -> Dict[str, Any]:
    """
    Enforces security policy for a given action and target.
    
    Returns a dictionary:
    {
        "decision": "EXECUTE" | "REQUIRE_APPROVAL" | "BLOCK" | "CLARIFY",
        "risk": "LOW" | "HIGH" | "CRITICAL" | "N/A",
        "action": str,
        "target": str or None
    }
    """
    clean_action = action.upper() if action else "UNKNOWN"
    risk = classify(clean_action)
    decision = DECISION_MAP.get(risk, "CLARIFY")

    return {
        "action": clean_action,
        "target": target,
        "risk": risk,
        "decision": decision
    }
