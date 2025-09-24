import argparse
from orchestrator import Orchestrator
from dotenv import load_dotenv
import os

def main():
    """
    Main entry point for the BMAD-MCP application.
    Parses command-line arguments and starts the Orchestrator.
    """
    load_dotenv()

    if not os.getenv("MODEL_PROVIDER"):
        print("Warning: MODEL_PROVIDER is not set in .env. Defaulting to 'openai'.")

    # Basic check for API keys
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("\nERROR: No AI provider API key found in .env file.")
        print("Please set either OPENAI_API_KEY or ANTHROPIC_API_KEY.\n")
        return

    parser = argparse.ArgumentParser(
        description="BMAD-MCP: A Fused Multi-Agent Framework for n8n Workflow Development",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--plan",
        required=True,
        help="Path to the master project_plan.yml file."
    )

    args = parser.parse_args()

    try:
        orchestrator = Orchestrator(plan_path=args.plan)
        orchestrator.run()
    except FileNotFoundError as e:
        print(f"\nERROR: A required file was not found.")
        print(f"Details: {e}\n")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()