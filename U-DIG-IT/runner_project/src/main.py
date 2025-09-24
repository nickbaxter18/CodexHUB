"""Command-line entry point for the runner."""

from __future__ import annotations

import argparse
import asyncio
from typing import List

import uvicorn

from .agents.orchestrator import Orchestrator
from .types import CommandRequest, GitActionRequest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probabilistic Multi-Agent Runner")
    parser.add_argument(
        "--command",
        nargs="+",
        help="Run a whitelisted command (e.g. --command ls -la)",
    )
    parser.add_argument(
        "--git",
        nargs="+",
        help="Run a git action (e.g. --git status)",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the FastAPI server",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


async def run_command(orchestrator: Orchestrator, command_args: List[str]) -> None:
    request = CommandRequest(command=command_args[0], args=command_args[1:])
    creation = await orchestrator.schedule_command(request)
    task = await orchestrator.task_manager.wait_for(creation.task_id)
    if task is None:
        print("Task not found")
        return
    print(task.result)


async def run_git(orchestrator: Orchestrator, git_args: List[str]) -> None:
    request = GitActionRequest(action=git_args[0], args=git_args[1:])
    creation = await orchestrator.schedule_git_action(request)
    task = await orchestrator.task_manager.wait_for(creation.task_id)
    if task is None:
        print("Task not found")
        return
    print(task.result)


async def main_async() -> None:
    args = parse_args()
    orchestrator = Orchestrator()

    if args.serve:
        uvicorn.run("src.api.server:app", host=args.host, port=args.port, reload=False)
        return

    if args.command:
        await run_command(orchestrator, args.command)
    elif args.git:
        await run_git(orchestrator, args.git)
    else:
        print("No action provided. Use --serve, --command, or --git.")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
