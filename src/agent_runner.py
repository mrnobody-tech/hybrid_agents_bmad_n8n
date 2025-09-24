import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from mcp_client import MCPClient, MCPClientError

class AgentRunner:
    def __init__(self, mcp_client: MCPClient | None = None):
        self.model_provider = os.getenv("MODEL_PROVIDER", "openai").lower()
        model_name = ""

        if self.model_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set for 'anthropic'")
            model_name = os.getenv("ANTHROPIC_MODEL_NAME", "claude-3-opus-20240229")
            self.llm = ChatAnthropic(model=model_name, temperature=0.1, api_key=api_key)
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set for 'openai'")
            model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4-turbo")
            self.llm = ChatOpenAI(model=model_name, temperature=0.1, api_key=api_key)

        print(f"[AgentRunner] Initialized with model: {self.model_provider}/{model_name}")

        self.mcp_client = mcp_client
        if self.mcp_client:
            mode = self.mcp_client.mode
            print(f"[AgentRunner] MCP client enabled (mode={mode})")
            try:
                self.mcp_client.initialize({"name": "bmad-mcp", "version": "0.1"})
            except MCPClientError as exc:
                print(f"[AgentRunner] MCP initialize failed: {exc}")
        else:
            print("[AgentRunner] MCP client not configured. Set N8N_MCP_URL and MCP_AUTH_TOKEN to enable.")

    def _find_agent_prompt_path(self, agent_name: str) -> str:
        """Finds the prompt file for a given agent name."""
        agent_dirs = ["agents/fused", "agents/bmad_core", "agents/n8n_mcp_core"]
        for directory in agent_dirs:
            path = os.path.join(directory, f"{agent_name}.md")
            if os.path.exists(path):
                return path
        raise FileNotFoundError(f"Prompt file for agent '{agent_name}' not found.")

    def run_agent(self, agent_name: str, context: dict, mcp_tools: list[dict] | None = None) -> str:
        """Runs a specific agent with the given context."""
        prompt_path = self._find_agent_prompt_path(agent_name)
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()

        enriched_context = dict(context)

        if self.mcp_client and mcp_tools:
            enriched_context["mcp_results"] = self._collect_mcp_results(mcp_tools)

        human_message_content = self._format_human_message(enriched_context)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_message_content),
        ]

        print(f"--- Invoking LLM for agent '{agent_name}' ---")
        response = self.llm.invoke(messages)
        print(f"--- LLM invocation complete for '{agent_name}' ---")

        return response.content

    def _format_human_message(self, context: dict) -> str:
        """Formats the context into a string for the human message."""
        message = "Here is the context for your current task:\n\n"
        for key, value in context.items():
            if value:
                message += f"--- {key.upper()} ---\n"
                if isinstance(value, list):
                    message += "\n".join(f"- {item}" for item in value)
                else:
                    message += str(value)
                message += "\n\n"

        message += "Please perform your task now based on this context and your core instructions."
        return message

    def _collect_mcp_results(self, mcp_tools: list[dict]) -> dict:
        results: dict[str, str] = {}
        for entry in mcp_tools:
            name = entry.get("name")
            if not name:
                continue
            alias = entry.get("alias") or name
            arguments = entry.get("arguments") or {}
            try:
                text = self.mcp_client.call_tool_text(name, arguments)
                results[alias] = text
            except MCPClientError as exc:
                results[alias] = f"MCP error for {name}: {exc}"
        return results
