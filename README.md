# BMAD-MCP: A Fused Multi-Agent Framework for n8n Workflow Development

## 1. Project Overview

BMAD-MCP is a sophisticated, local-first AI development environment that synergistically fuses the **BMAD-METHOD** and **n8n-mcp**. It creates a powerful, multi-agent system capable of managing the entire lifecycle of complex n8n automation workflow development, from high-level planning to low-level implementation and testing.

This framework leverages the strategic, process-oriented strengths of BMAD's generic development agents and marries them with the tactical, tool-aware expertise of n8n-mcp's specialized agents. The result is a highly efficient, scalable, and structured system for building robust n8n solutions.



## 2. Core Architecture: Hybrid Hierarchical Model

The system operates on a Hybrid Hierarchical Model. A master **Orchestrator** agent reads a high-level `project_plan.yml` and directs a team of specialist agents.

-   **Strategic Layer (BMAD-based):** Agents like the `PM` and a fused `n8n Architect` handle the "what" and "how" of the project, creating detailed requirements and architectural blueprints.
-   **Tactical Layer (n8n-mcp-based):** A fused `n8n Developer` agent, along with `QA` and `Code Reviewer` agents, execute the blueprint, interacting directly with a live n8n instance via the Model Context Protocol (MCP).

## 3. Getting Started

### Prerequisites
-   Python 3.10+
-   Poetry
-   Docker
-   A running n8n instance with the `n8n-mcp` server component active.

### Installation & Setup
1.  **Clone the repository:**
    ```bash
    git clone <this-repo-url>
    cd BMAD-MCP
    ```
2.  **Install dependencies:**
    ```bash
    poetry install
    ```
3.  **Configure environment:**
    -   Copy `.env.example` to `.env`.
    -   Fill in your `OPENAI_API_KEY` (or other provider) and the `N8N_MCP_URL` for your running `n8n-mcp` instance.

### Running a Project
1.  **Define a project:**
    -   Copy `project_plans/template_project_plan.yml` to a new file (e.g., `project_plans/invoice_automation.yml`).
    -   Fill out the BMAD sections (Brief, Mission, Audience, Deliverables).
2.  **Launch the Orchestrator:**
    ```bash
    poetry run python src/main.py --plan project_plans/invoice_automation.yml
    ```

The Orchestrator will now execute the plan as defined in the associated workflow YAML.