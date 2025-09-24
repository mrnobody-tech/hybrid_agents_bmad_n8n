import yaml
import os
from agent_runner import AgentRunner
from mcp_client import MCPClient

class Orchestrator:
    def __init__(self, plan_path: str):
        if not os.path.exists(plan_path):
            raise FileNotFoundError(f"Project plan not found at {plan_path}")
        with open(plan_path, 'r', encoding='utf-8') as f:
            self.plan = yaml.safe_load(f)

        self.project_name = self.plan.get("project_name", "unnamed_project")
        self.deliverables_path = os.path.join("deliverables", self.project_name)
        os.makedirs(self.deliverables_path, exist_ok=True)

        self.workflow = self._load_workflow()
        self.state = self._load_or_initialize_state()

        self.mcp_client = MCPClient.from_env()
        if self.mcp_client:
            print("[Orchestrator] MCP client detected and will be used for tool augmentation.")
        else:
            print("[Orchestrator] MCP client not configured. Set N8N_MCP_URL and MCP_AUTH_TOKEN to enable.")

        self.agent_runner = AgentRunner(mcp_client=self.mcp_client)

    def _load_workflow(self) -> dict:
        workflow_file = self.plan.get("workflow_definition")
        if not workflow_file:
            raise ValueError("Workflow definition not specified in project plan.")

        workflow_path = os.path.join("workflows", workflow_file)
        if not os.path.exists(workflow_path):
            raise FileNotFoundError(f"Workflow definition file not found at {workflow_path}")

        with open(workflow_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_or_initialize_state(self) -> dict:
        """Load checkpoint if present; else initialize a fresh state."""
        state_path = os.path.join(self.deliverables_path, "state.json")
        if os.path.exists(state_path):
            try:
                import json
                with open(state_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        state = {
            "project_name": self.project_name,
            "brief": self.plan.get('brief'),
            "mission": self.plan.get('mission'),
            "audience": self.plan.get('audience'),
            "deliverables_list": self.plan.get('deliverables'),
            "history": [],
            "completed": []
        }
        return state

    def run(self):
        print(f"--- [Orchestrator] Initiating project: {self.project_name} ---")

        import json
        state_path = os.path.join(self.deliverables_path, "state.json")
        completed = set(self.state.get("completed", []))

        for phase_index, phase in enumerate(self.workflow.get('phases', [])):
            phase_name = phase.get('name')
            print(f"\n{'='*20}\n--- [Orchestrator] Starting Phase: {phase_name} ---\n{'='*20}")

            for step_index, step in enumerate(phase.get('steps', [])):
                agent_name = step.get('agent')
                task_description = step.get('task')
                output_key = step.get('output')
                input_keys = step.get('inputs', [])
                step_id = f"{phase_index}:{step_index}:{agent_name}:{output_key}"

                if step_id in completed:
                    print(f"--- [Orchestrator] Skipping completed step {step_id}")
                    continue

                print(f"--- [Orchestrator] Delegating task to '{agent_name}': {task_description} ---")

                if agent_name == "HumanReview":
                    self.human_review_step(step.get('prompt', "Do you approve to proceed?"))
                    continue

                context = {key: self.state.get(key) for key in input_keys}
                context['task'] = task_description

                mcp_tools = step.get('mcp_tools') if self.mcp_client else None
                result = self.agent_runner.run_agent(agent_name, context, mcp_tools=mcp_tools)

                if output_key:
                    print(f"--- [Orchestrator] Storing output in state key: '{output_key}' ---")
                    self.state[output_key] = result
                    self.state["history"].append({"agent": agent_name, "task": task_description, "result": result})

                    deliverable_path = os.path.join(self.deliverables_path, f"{output_key}.md")
                    with open(deliverable_path, 'w', encoding='utf-8') as f:
                        f.write(result)
                    print(f"--- [Orchestrator] Intermediate deliverable saved to {deliverable_path} ---")

                # checkpoint
                completed.add(step_id)
                self.state["completed"] = sorted(list(completed))
                try:
                    with open(state_path, 'w', encoding='utf-8') as f:
                        json.dump(self.state, f, indent=2)
                except Exception:
                    pass

        print(f"\n--- [Orchestrator] Project '{self.project_name}' completed successfully! ---")
        print(f"--- [Orchestrator] Final deliverables are in: {self.deliverables_path} ---")

    def human_review_step(self, prompt_text: str):
        print(f"\n--- [Orchestrator] PAUSING for Human Review ---")
        print("--- Review generated deliverables in the deliverables folder. ---")

        while True:
            action = input(f"{prompt_text} (y/n): ").lower()
            if action == 'y':
                print("--- [Orchestrator] Approval received. Resuming workflow. ---")
                self.state["history"].append({"agent": "HumanReview", "result": "Approved"})
                return
            elif action == 'n':
                print("--- [Orchestrator] Project aborted by user. ---")
                self.state["history"].append({"agent": "HumanReview", "result": "Rejected"})
                exit()
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
