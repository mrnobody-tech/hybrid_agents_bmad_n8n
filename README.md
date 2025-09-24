# BMAD-MCP: A Fused Multi-Agent Framework for n8n Workflow Development

## 1. Project Overview

BMAD-MCP is a sophisticated, local-first AI development environment that synergistically fuses the **BMAD-METHOD** and **n8n-mcp**. It creates a powerful, multi-agent system capable of managing the entire lifecycle of complex n8n automation workflow development, from high-level planning to low-level implementation and testing.

This framework leverages the strategic, process-oriented strengths of BMAD's generic development agents and marries them with the tactical, tool-aware expertise of n8n-mcp's specialized agents. The result is a highly efficient, scalable, and structured system for building robust n8n solutions.

## 2. Core Architecture: Hybrid Hierarchical Model

The system operates on a Hybrid Hierarchical Model. A master **Orchestrator** agent reads a high-level `project_plan.yml` and directs a team of specialist agents.

- **Strategic Layer (BMAD-based):** Agents like the `pm` and the fused `n8n_architect` handle the "what" and "how" of the project, creating detailed requirements and architectural blueprints.
- **Tactical Layer (n8n-mcp-based):** The fused `n8n_developer` agent, along with `code-reviewer` and `n8n-mcp-tester` agents, execute the blueprint, interacting directly with a live n8n instance via the Model Context Protocol (MCP).

## 3. Getting Started

### Prerequisites
- Python 3.10+
- Poetry
- Docker
- A running n8n instance with the `n8n-mcp` server component active

### Installation & Setup
1. **Navigate to the project directory:**
   ```bash
   cd ~/Desktop/BMAD-MCP
   ```
2. **Install dependencies:**
   ```bash
   poetry install
   ```
3. **Configure environment:**
   - Copy `.env.example` to `.env`.
   - Fill in your `MODEL_PROVIDER`, API key (for example `OPENAI_API_KEY`), and the URL for your running `N8N_MCP_URL`.

### Running a Project
1. **Define a project:**
   - Copy `project_plans/template_project_plan.yml` to a new file (for example `project_plans/invoice_automation.yml`).
   - Fill out the BMAD sections (Brief, Mission, Audience, Deliverables).
2. **Launch the Orchestrator:**
   ```bash
   poetry run python src/main.py --plan project_plans/invoice_automation.yml
   ```

The Orchestrator will now execute the plan as defined in the associated workflow YAML. Each step can optionally invoke n8n-MCP tools (see below) and the results are persisted to `deliverables/<project_name>/`.

## 4. Integrating with the n8n-MCP Server

The project now speaks the MCP JSON-RPC API directly. Configure the following variables in your `.env`:

```
N8N_MCP_URL=http://localhost:3000
MCP_AUTH_TOKEN=replace-with-your-token
MCP_MODE=real          # or "simulation"
MCP_SIMULATION_FIXTURES=tests/simulations/mcp_responses.json
```

Run the health check script to verify the connection:

```bash
poetry run python scripts/mcp_sanity_check.py
```

### Supplying MCP tool calls from a workflow

Workflow steps can request MCP tool results before the LLM agent runs. Add an `mcp_tools` block to a step, for example:

```yaml
- agent: "n8n_architect"
  task: "Design the workflow architecture"
  inputs: ["prd_content"]
  mcp_tools:
    - name: "get_node_essentials"
      arguments:
        nodeType: "nodes-base.httpRequest"
      alias: "http_request_reference"
  output: "architecture_content"
```

The tool responses are injected into the agent context under `MCP_RESULTS` so prompts can cite accurate node metadata.

### Simulation Mode

Set `MCP_MODE=simulation` and point `MCP_SIMULATION_FIXTURES` at `tests/simulations/mcp_responses.json` to run without a live container. The fixtures ship with a minimal response set and can be extended for richer test scenarios.

## 5. Environment File Handling

- Template `.env` files live under `~/Desktop/KEYS_TOTATE` on this machine and remain outside version control.
- The repository includes `.env.example` for reference only. Real credentials must never be committed; the pre-commit hook blocks accidental `.env` entries while allowing `.env.example`.
