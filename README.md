# AWS CloudOps AI Agent (Gemini-powered)

An AI-driven CloudOps assistant that interprets natural-language infrastructure requests, classifies risk levels, enforces security policies deterministically, requires human operator approval for high-risk operations, strictly blocks critical/destructive actions, and logs all events to an immutable audit trail.

---

## 🏗️ Architecture Overview

```
                          +-------------------------+
                          |   User Natural Request  |
                          +------------+------------+
                                       |
                                       v
                          +-------------------------+
                          |   gemini_client.py      |
                          |  (google-genai SDK)     |
                          +------------+------------+
                                       | Extract Action & Target (JSON)
                                       v
                          +-------------------------+
                          |    policy_engine.py     |
                          |  (Risk Classification)  |
                          +------------+------------+
                                       |
            +--------------------------+--------------------------+
            |                          |                          |
    LOW Risk (Auto)            HIGH Risk (Approval)      CRITICAL Risk (Block)
            |                          |                          |
            v                          v                          v
    +---------------+          +---------------+          +---------------+
    | Execute Tool  |          | Operator y/n  |          | 🚨 BLOCKED     |
    +-------+-------+          +-------+-------+          +---------------+
            |                          |                          |
            +--------------------------+--------------------------+
                                       |
                                       v
                          +-------------------------+
                          |     audit_log.py        |
                          | (audit_log.txt & .jsonl)|
                          +-------------------------+
```

### Key Security & Design Principles

1. **LLM as Intent Parser, Not Decision Maker**: Gemini (`gemini_client.py`) is restricted strictly to parsing intent into structured JSON. It **never** decides permissions or risk levels.
2. **Deterministic Policy Engine**: `policy_engine.py` classifies risk and evaluates permissions strictly by code logic, decoupling security from LLM hallucination risks.
3. **Mocked Cloud Operations**: `tools.py` provides mock implementations for EC2, S3, and AWS Account queries. In production, this layer is designed to be swapped with `boto3` calls backed by AWS IAM least-privilege roles.
4. **Comprehensive Audit Trail**: Every request—whether executed, approved, rejected, or blocked—is recorded in both `audit_log.jsonl` and `audit_log.txt`.

---

## 🚦 Risk & Policy Matrix

| Action | Risk Level | Policy Decision | Action Description |
|---|---|---|---|
| `READ_EC2` | **LOW** | `EXECUTE` | Read EC2 instance states |
| `READ_S3` | **LOW** | `EXECUTE` | Read list of S3 buckets |
| `READ_ACCOUNT` | **LOW** | `EXECUTE` | Read AWS account details |
| `STOP_EC2` | **HIGH** | `REQUIRE_APPROVAL` | Stop an EC2 instance |
| `START_EC2` | **HIGH** | `REQUIRE_APPROVAL` | Start an EC2 instance |
| `TERMINATE_EC2` | **CRITICAL** | `BLOCK` | Terminate an EC2 instance (Forbidden) |
| `DELETE_S3` | **CRITICAL** | `BLOCK` | Delete an S3 bucket (Forbidden) |
| `DELETE_ACCOUNT` | **CRITICAL** | `BLOCK` | Terminate AWS Account (Forbidden) |
| `GREETING` | **LOW** | `EXECUTE` | Respond to greetings / role queries |
| `EXPLAIN_AWS` | **LOW** | `EXECUTE` | Explain AWS concepts / definition queries |
| `UNKNOWN` | **N/A** | `CLARIFY` | Request user clarification |

---

## 📦 Project Structure

```
c:\Users\ariva\Downloads\AWS CloudOps AI-Agent\
├── main.py                # Entry point, interactive CLI REPL
├── agent.py                # Core agent orchestrator
├── gemini_client.py        # Gemini API wrapper (system prompt + JSON schema)
├── policy_engine.py        # Risk classification + safety rules engine
├── tools.py                 # Mocked AWS operations layer
├── audit_log.py            # Audit logger writing to .jsonl and .txt
├── config.py                # Environment & configuration loader
├── .env                     # Contains GEMINI_API_KEY
├── .env.example             # Example environment template
├── requirements.txt         # Dependencies (google-genai, python-dotenv)
├── audit_log.jsonl          # Generated structured audit log
└── audit_log.txt            # Generated human-readable audit log
```

---

## 🚀 Quickstart Guide

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file (or copy `.env.example`):

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run the CLI Agent

```bash
python main.py
```

---

## 💻 Interactive Demo Script & Example Queries

Run `python main.py` and test the following inputs:

### Scenario 1: Low-Risk Operation (Auto-Executed)
```text
> Show me the EC2 instances
✅ SUCCESS (LOW Risk Auto-Executed):
  • id: i-demo001, name: Web-Server, state: running, type: t3.micro
  • id: i-demo002, name: Test-Server, state: stopped, type: t3.micro
```

### Scenario 2: High-Risk Operation (Operator Approval Required)
```text
> Stop the test server

⚠️  HIGH RISK ACTION DETECTED: STOP_EC2 (Target: Test-Server)
Approve this action (STOP_EC2)? (y/n): y
✅ APPROVED & EXECUTED (HIGH Risk):
  status: SUCCESS
  action: STOP_EC2
  target: Test-Server
  message: EC2 instance 'Test-Server' has been stopped successfully.
```

### Scenario 3: Critical-Risk Operation (Strictly Blocked)
```text
> Terminate the EC2 server

🚨 BLOCKED — CRITICAL risk action denied by policy.
   Action 'TERMINATE_EC2' is strictly prohibited by security policy rules under all circumstances.
```

---

## 🔒 Audit Log Output Example (`audit_log.txt`)

```text
[2026-08-24T16:55:00.123456+00:00] ID: 550e8400-e29b-41d4-a716-446655440000 | Request: "Show me the EC2 instances" | Action: READ_EC2 | Target: None | Risk: LOW | Decision: EXECUTE | ApprovedBy: None | Executed: True
[2026-08-24T16:55:12.654321+00:00] ID: 6fa459a7-ee8a-4548-9686-234b46c68e1a | Request: "Stop the test server" | Action: STOP_EC2 | Target: test server | Risk: HIGH | Decision: REQUIRE_APPROVAL | ApprovedBy: operator | Executed: True
[2026-08-24T16:55:25.987654+00:00] ID: 7c9e6679-7425-40de-944b-e07fc1f90ae7 | Request: "Terminate the EC2 server" | Action: TERMINATE_EC2 | Target: EC2 server | Risk: CRITICAL | Decision: BLOCK | ApprovedBy: None | Executed: False
```

---

## 🔌 Swapping Bedrock / Real AWS Production Services

To deploy in production:
1. **Model Layer**: Replace `gemini_client.py` with AWS Bedrock SDK (`boto3.client('bedrock-runtime')`) using Claude / Nova models.
2. **AWS Operations Layer**: Replace mock calls in `tools.py` with `boto3.client('ec2')` / `boto3.client('s3')` bound to an AWS IAM Role with minimal least-privilege IAM policies.
3. **Audit Trail**: Redirect `audit_log.py` outputs to AWS CloudWatch Logs or AWS CloudTrail.
