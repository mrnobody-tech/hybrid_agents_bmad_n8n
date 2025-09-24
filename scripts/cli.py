import argparse
import os
from pathlib import Path

from mcp_client import MCPClient, MCPClientError
from orchestrator import Orchestrator


def cmd_check(args: argparse.Namespace) -> int:
    client = MCPClient.from_env()
    if not client:
        print("MCP not configured. Set N8N_MCP_URL and MCP_AUTH_TOKEN.")
        return 2
    try:
        client.initialize({"name": "bmad-cli", "version": "0.1"})
        tools = list(client.list_tools())
        print(f"OK: MCP reachable (mode={client.mode}), tools: {len(tools)}")
        if args.require_management:
            client.require_tools(["n8n_create_workflow", "n8n_update_partial_workflow"]) 
        return 0
    except MCPClientError as exc:
        print(f"ERROR: {exc}")
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    orch = Orchestrator(plan_path=args.plan)
    orch.run()
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    orch = Orchestrator(plan_path=args.plan)
    orch.run()
    return 0


def cmd_package(args: argparse.Namespace) -> int:
    import zipfile
    project = args.project or "unnamed_project"
    src_dir = Path("deliverables") / project
    if not src_dir.exists():
        print(f"No deliverables for project '{project}' at {src_dir}")
        return 2
    out = Path(args.output or f"package-{project}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in src_dir.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(src_dir.parent))
    print(f"Wrote {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bmad", description="BMAD-MCP CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("check", help="Verify MCP connectivity and tools")
    pc.add_argument("--require-management", action="store_true")
    pc.set_defaults(func=cmd_check)

    pr = sub.add_parser("run", help="Run orchestrator on a plan")
    pr.add_argument("--plan", required=True)
    pr.set_defaults(func=cmd_run)

    prr = sub.add_parser("resume", help="Resume using state checkpoints")
    prr.add_argument("--plan", required=True)
    prr.set_defaults(func=cmd_resume)

    pp = sub.add_parser("package", help="Zip deliverables for transport")
    pp.add_argument("--project")
    pp.add_argument("--output")
    pp.set_defaults(func=cmd_package)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
