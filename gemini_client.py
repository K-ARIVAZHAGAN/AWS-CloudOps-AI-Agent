"""
Gemini API Wrapper — Natural Language Intent Parsing.

Uses google-genai SDK to interpret user requests into structured JSON.
Includes fallback keyword parser in case of API failure, quota limits, or missing credentials.
"""

import json
import logging
import re
import warnings
from typing import Dict, Any

# Suppress noisy Pydantic & SDK warnings
warnings.filterwarnings("ignore")

import config

logger = logging.getLogger("gemini_client")

SYSTEM_PROMPT = """You are the natural-language understanding layer of an AWS CloudOps AI Agent.

Your ONLY job is to parse a user's CloudOps request and output a single JSON object — nothing else, no markdown, no preamble, no explanation.

You must classify the request into exactly one of these actions:
- READ_EC2
- READ_S3
- READ_ACCOUNT
- STOP_EC2
- START_EC2
- TERMINATE_EC2
- DELETE_S3
- DELETE_ACCOUNT
- GREETING
- UNKNOWN

Rules:
1. If the user is saying hello, greeting you, or asking who you are (e.g. "hi", "hello", "hey", "who are you", "help"), classify as GREETING.
2. If the request is ambiguous or doesn't match a known AWS CloudOps action or greeting, return UNKNOWN.
3. Extract any resource identifier or name mentioned (e.g. "test server", "prod bucket") into "target", or null if none given.
4. Never decide whether an action is allowed or safe — that is NOT your job. You only classify intent. A downstream policy engine handles authorization and risk.
5. Do not invent AWS resource IDs, account numbers, or data. Only extract what the user actually said.
6. Output strictly valid JSON in this exact schema:

{
  "action": "READ_EC2 | READ_S3 | READ_ACCOUNT | STOP_EC2 | START_EC2 | TERMINATE_EC2 | DELETE_S3 | DELETE_ACCOUNT | GREETING | UNKNOWN",
  "target": "string or null",
  "raw_request": "the original user text",
  "confidence": "high | medium | low"
}

Return ONLY the JSON object. No code fences, no commentary."""


def _fallback_keyword_parser(user_text: str) -> Dict[str, Any]:
    """
    Fallback parser using regex / keyword rules.
    Ensures the demo application never crashes if the API is unreachable or rate-limited.
    """
    text = user_text.strip()
    text_lower = text.lower()

    action = "UNKNOWN"
    target = None

    # 1. Greetings
    if text_lower in ["hi", "hello", "hey", "greetings", "who are you", "help", "hi there"] or any(text_lower.startswith(g) for g in ["hi ", "hello ", "hey "]):
        action = "GREETING"
    
    # 2. Critical Destructive Actions (Checked BEFORE Read operations)
    elif ("delete" in text_lower or "remove" in text_lower or "destroy" in text_lower) and ("s3" in text_lower or "bucket" in text_lower):
        action = "DELETE_S3"
    elif ("terminate" in text_lower or "destroy" in text_lower) and ("ec2" in text_lower or "server" in text_lower or "instance" in text_lower):
        action = "TERMINATE_EC2"
    elif ("delete" in text_lower or "terminate" in text_lower or "destroy" in text_lower) and "account" in text_lower:
        action = "DELETE_ACCOUNT"
        
    # 3. High Risk Actions
    elif "stop" in text_lower:
        action = "STOP_EC2"
    elif "start" in text_lower:
        action = "START_EC2"
        
    # 4. Low Risk Read Operations
    elif any(k in text_lower for k in ["s3", "bucket"]):
        action = "READ_S3"
    elif any(k in text_lower for k in ["ec2", "server", "instance", "virtual machine"]):
        action = "READ_EC2"
    elif any(k in text_lower for k in ["account", "whoami", "identity"]):
        action = "READ_ACCOUNT"

    # Extraction heuristic for target
    words = text.split()
    for i, w in enumerate(words):
        if w.lower() in ["server", "instance", "bucket", "target"] and i + 1 < len(words):
            target = words[i + 1]

    return {
        "action": action,
        "target": target,
        "raw_request": user_text,
        "confidence": "high" if action == "GREETING" else ("medium" if action != "UNKNOWN" else "low"),
        "fallback_used": True
    }


def _extract_response_text(response) -> str:
    """Extract clean response text without triggering SDK text-parts UserWarning."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if getattr(response, "candidates", None) and response.candidates:
            candidate = response.candidates[0]
            if getattr(candidate, "content", None) and getattr(candidate.content, "parts", None):
                text_parts = [part.text for part in candidate.content.parts if getattr(part, "text", None)]
                if text_parts:
                    return "".join(text_parts).strip()
        if getattr(response, "text", None):
            return response.text.strip()
    return ""


def interpret_request(user_text: str) -> Dict[str, Any]:
    """
    Calls Gemini API using google-genai SDK to parse request into structured JSON.
    Enforces application/json output response mime type.
    Falls back gracefully to keyword parser if API key is invalid or request fails.
    """
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your_key_here":
        return _fallback_keyword_parser(user_text)

    candidate_models = [config.GEMINI_MODEL_NAME, "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.5-flash"]
    candidate_models = list(dict.fromkeys(candidate_models))

    last_error = None

    for model_name in candidate_models:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=config.GEMINI_API_KEY)

                response = client.models.generate_content(
                    model=model_name,
                    contents=user_text,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.0
                    )
                )

                raw_content = _extract_response_text(response)
                
                if raw_content.startswith("```"):
                    raw_content = re.sub(r"^```(?:json)?\n?", "", raw_content)
                    raw_content = re.sub(r"\n?```$", "", raw_content)

                if raw_content:
                    parsed_json = json.loads(raw_content)
                    parsed_json["raw_request"] = user_text
                    parsed_json["fallback_used"] = False
                    return parsed_json

        except Exception as e:
            last_error = e

    return _fallback_keyword_parser(user_text)
