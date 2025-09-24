import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

class AgentRunner:
    def __init__(self):
        self.model_provider = os.getenv("MODEL_PROVIDER", "openai").lower()
        model_name = ""

        if self.model_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key: raise ValueError("ANTHROPIC_API_KEY not set in .env for selected provider 'anthropic'")
            model_name = os.getenv("ANTHROPIC_MODEL_NAME", "claude-3-opus-20240229")
            self.llm = ChatAnthropic(model=model_name, temperature=0.1, api_key=api_key)
        else: # Default to OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key: raise ValueError("OPENAI_API_KEY not set in .env for selected provider 'openai'")
            model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4-turbo")
            self.llm = ChatOpenAI(model=model_name, temperature=0.1, api_key=api_key)

        print(f"[AgentRunner] Initialized with model: {self.model_provider}/{model_name}")

    def _find_agent_prompt_path(self, agent_name: str) -> str:
        """Finds the prompt file for the given agent name."""
        for core in ["fused", "bmad_core", "n8n_mcp_core"]:
            prompt_path = os.path.join("agents", core, f"{agent_name}.md")
            if os.path.exists(prompt_path):
                return prompt_path
        raise FileNotFoundError(f"Prompt file for agent '{agent_name}' not found in any core directory.")

    def run_agent(self, agent_name: str, context: dict) -> str:
        prompt_path = self._find_agent_prompt_path(agent_name)
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()

        human_prompt = """
        Here is the context for your task:
        ---CONTEXT---
        {context}
        ---END CONTEXT---

        Your task is: {task}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt.format(context=context, task=context.get('task')))
        ]

        print(f"--- [AgentRunner] Running agent '{agent_name}' ---")
        response = self.llm.invoke(messages)
        print(f"--- [AgentRunner] Agent '{agent_name}' finished. ---")
        return response.content