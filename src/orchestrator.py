import yaml
import os
from agent_runner import AgentRunner

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
        self.state = self._initialize_state()
        self.agent_runner = AgentRunner()

    def _load_workflow(self) -> dict:
        workflow_file = self.plan.get("workflow_definition")
        if not workflow_file:
            raise ValueError("Workflow definition not specified in project plan.")

        workflow_path = os.path.join("workflows", workflow_file)
        if not os.path.exists(workflow_path):
            raise FileNotFoundError(f"Workflow definition file not found at {workflow_path}")

        with open(workflow_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _initialize_state(self) -> dict:
        """Initialize the state with the full BMAD context."""
        return {
            "project_name": self.project_name,
            "brief": self.plan.get('brief'),
            "mission": self.plan.get('mission'),
            "audience": self.plan.get('audience'),
            "deliverables_list": self.plan.get('deliverables'),
            "history": []
        }

    def run(self):
        print(f"--- [Orchestrator] Initiating project: {self.project_name} ---")

        for phase in self.workflow.get('phases', []):
            phase_name = phase.get('name')
            print(f"\n{'='*20}\n--- [Orchestrator] Starting Phase: {phase_name} ---\n{'='*20}")

            for step in phase.get('steps', []):
                agent_name = step.get('agent')
                task_description = step.get('task')
                output_key = step.get('output')
                input_keys = step.get('inputs', [])

                print(f"--- [Orchestrator] Delegating task to '{agent_name}': {task_description} ---")

                if agent_name == "HumanReview":
                    self.human_review_step(step.get('prompt', "Do you approve to proceed?"))
                    continue

                context = {key: self.state.get(key) for key in input_keys}
                context['task'] = task_description

                result = self.agent_runner.run_agent(agent_name, context)

                if output_key:
                    print(f"--- [Orchestrator] Storing output in state key: '{output_key}' ---")
                    self.state[output_key] = result
                    self.state["history"].append({"agent": agent_name, "task": task_description, "result": result})

                    deliverable_path = os.path.join(self.deliverables_path, f"{output_key}.md")
                    with open(deliverable_path, 'w', encoding='utf-8') as f:
                        f.write(result)
                    print(f"--- [Orchestrator] Intermediate deliverable saved to {deliverable_path} ---")

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
