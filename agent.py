"""
CloudOpsAgent — Main Orchestrator.

Orchestrates intent parsing, policy engine security checks, tool execution, and audit logging.
"""

import sys
from typing import Dict, Any, Optional, Callable

# Configure stdout UTF-8 encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import gemini_client
import policy_engine
import tools
import audit_log


class CloudOpsAgent:
    def __init__(self):
        pass

    def handle_request(
        self,
        user_text: str,
        approval_prompt_fn: Optional[Callable[[str, Optional[str]], bool]] = None
    ) -> Dict[str, Any]:
        """
        Processes a natural language CloudOps request.
        
        Steps:
        1. Parse intent via Gemini API (gemini_client.py)
        2. Evaluate policy risk & decision (policy_engine.py)
        3. Execute or enforce rules (tools.py)
        4. Write audit trail (audit_log.py)
        """
        # Step 1: Interpret Request via Gemini layer
        intent = gemini_client.interpret_request(user_text)
        action = intent.get("action", "UNKNOWN")
        target = intent.get("target")

        # Step 2: Enforce Security Policy
        policy = policy_engine.enforce(action, target)
        decision = policy["decision"]
        risk = policy["risk"]

        executed = False
        approved_by = None
        tool_output = None

        # Step 3: Branch on Policy Decision
        if decision == "EXECUTE":
            tool_output = self._execute_tool(action, target)
            executed = True
            if action == "GREETING":
                print(f"\n👋 {tool_output}")
            else:
                print(f"\n✅ SUCCESS ({risk} Risk Auto-Executed):")
                self._print_tool_output(action, tool_output)

        elif decision == "REQUIRE_APPROVAL":
            print(f"\n⚠️  HIGH RISK ACTION DETECTED: {action} (Target: {target or 'None'})")
            
            approved = False
            if approval_prompt_fn:
                approved = approval_prompt_fn(action, target)
            else:
                ans = input(f"Approve this action ({action})? (y/n): ").strip().lower()
                approved = ans in ["y", "yes"]

            if approved:
                approved_by = "operator"
                tool_output = self._execute_tool(action, target)
                executed = True
                print(f"✅ APPROVED & EXECUTED ({risk} Risk):")
                self._print_tool_output(action, tool_output)
            else:
                approved_by = "rejected"
                print(f"❌ DENIED: Action {action} was rejected by operator.")

        elif decision == "BLOCK":
            print(f"\n🚨 BLOCKED — CRITICAL risk action denied by policy.")
            print(f"   Action '{action}' is strictly prohibited by security policy rules under all circumstances.")

        elif decision == "CLARIFY":
            print(f"\n❓ UNKNOWN INTENT: Could not determine a valid AWS CloudOps action from your request.")
            print("   Please rephrase your request (e.g. 'Show me the EC2 instances', 'Stop the test server', 'List S3 buckets').")

        # Step 4: Record Audit Trail (Always called regardless of outcome)
        log_entry = {
            "raw_request": user_text,
            "action": action,
            "target": target,
            "risk": risk,
            "decision": decision,
            "approved_by": approved_by,
            "executed": executed
        }
        audit_log.log_event(log_entry)

        return {
            "intent": intent,
            "policy": policy,
            "executed": executed,
            "tool_output": tool_output
        }

    def _execute_tool(self, action: str, target: Optional[str]) -> Any:
        clean_action = action.upper()
        if clean_action == "GREETING":
            return "Hello! I am your AWS CloudOps AI Assistant. I can help you inspect EC2 instances, list S3 buckets, start/stop servers, or view account info. How can I assist you today?"
        elif clean_action == "READ_EC2":
            return tools.read_ec2()
        elif clean_action == "READ_S3":
            return tools.read_s3()
        elif clean_action == "READ_ACCOUNT":
            return tools.read_account()
        elif clean_action == "STOP_EC2":
            return tools.stop_ec2(target)
        elif clean_action == "START_EC2":
            return tools.start_ec2(target)
        elif clean_action == "TERMINATE_EC2":
            return tools.terminate_ec2(target)
        elif clean_action == "DELETE_S3":
            return tools.delete_s3(target)
        elif clean_action == "DELETE_ACCOUNT":
            return tools.delete_account(target)
        return None

    def _print_tool_output(self, action: str, output: Any) -> None:
        if output is None:
            return
        if isinstance(output, list):
            for item in output:
                if isinstance(item, dict):
                    formatted_fields = ", ".join(f"{k}: {v}" for k, v in item.items())
                    print(f"  • {formatted_fields}")
                else:
                    print(f"  • {item}")
        elif isinstance(output, dict):
            for k, v in output.items():
                print(f"  {k}: {v}")
        else:
            print(f"  {output}")
