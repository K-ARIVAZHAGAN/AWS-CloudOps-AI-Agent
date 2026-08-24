"""
AWS CloudOps AI Agent — CLI Loop.

Entry point for interactive CLI session.
"""

import sys
import warnings

# Suppress all noisy Pydantic & SDK warnings globally
warnings.filterwarnings("ignore")

# Configure stdout & stdin UTF-8 encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent import CloudOpsAgent


def main():
    print("=" * 60)
    print("       AWS CloudOps AI Agent (Gemini-powered)")
    print("=" * 60)
    print("AWS CloudOps AI Agent — type your request ('exit' to quit)\n")

    agent = CloudOpsAgent()

    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting AWS CloudOps AI Agent. Goodbye!")
                break

            agent.handle_request(user_input)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting AWS CloudOps AI Agent. Goodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    main()
