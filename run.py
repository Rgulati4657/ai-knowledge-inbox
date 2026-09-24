#!/usr/bin/env python3
"""Validate configuration, then run the backend and frontend dev servers together.

Usage:
    python3 run.py
    python3 run.py --backend-port 8001 --frontend-port 5174

Stdlib only -- this script itself needs no dependencies installed to run.
It does require backend/.venv and frontend/node_modules to already exist
(see README.md for the one-time setup steps); it checks for both and tells
you exactly what to run if either is missing, rather than installing things
on its own.
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-port", type=int, default=8000)
    parser.add_argument("--frontend-port", type=int, default=5173)
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"\n[run.py] ERROR: {message}\n", file=sys.stderr)
    sys.exit(1)


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def check_backend_env() -> None:
    env_path = BACKEND / ".env"
    example_path = BACKEND / ".env.example"

    if not env_path.exists():
        fail(
            f"{env_path.relative_to(ROOT)} not found.\n"
            f"  Run:  cp {example_path.relative_to(ROOT)} {env_path.relative_to(ROOT)}\n"
            f"  then open it and fill in the required API key before running again."
        )

    values = parse_env_file(env_path)
    embedding_provider = values.get("EMBEDDING_PROVIDER", "gemini")
    generation_provider = values.get("GENERATION_PROVIDER", "gemini")

    # Which keys are actually required depends on which providers are
    # configured -- "local" needs no key at all, so this isn't a blanket
    # "GEMINI_API_KEY must be set" check.
    required_keys: set[str] = set()
    if "gemini" in (embedding_provider, generation_provider):
        required_keys.add("GEMINI_API_KEY")
    if generation_provider == "groq":
        required_keys.add("GROQ_API_KEY")

    missing = sorted(key for key in required_keys if not values.get(key))
    if missing:
        fail(
            f"backend/.env is missing a value for: {', '.join(missing)}\n"
            f"  (EMBEDDING_PROVIDER={embedding_provider}, GENERATION_PROVIDER={generation_provider})\n"
            f"  Open backend/.env and fill these in -- see README.md for where to get a free key."
        )

    print(
        f"[run.py] backend/.env OK "
        f"(embedding={embedding_provider}, generation={generation_provider})"
    )


def check_backend_deps() -> Path:
    venv_python = BACKEND / ".venv" / "bin" / "python"
    if not venv_python.exists():
        fail(
            "backend/.venv not found.\n"
            "  Run:\n"
            "    cd backend\n"
            "    python3 -m venv .venv\n"
            "    .venv/bin/pip install -r requirements.txt"
        )
    print("[run.py] backend/.venv OK")
    return venv_python


def check_frontend_deps() -> None:
    if not (FRONTEND / "node_modules").exists():
        fail("frontend/node_modules not found.\n  Run:\n    cd frontend\n    npm install")

    frontend_env = FRONTEND / ".env"
    if not frontend_env.exists():
        example = FRONTEND / ".env.example"
        frontend_env.write_text(example.read_text())
        print(f"[run.py] created {frontend_env.relative_to(ROOT)} from .env.example")

    print("[run.py] frontend/node_modules OK")


def main() -> None:
    args = parse_args()

    print("[run.py] Validating environment...\n")
    check_backend_env()
    venv_python = check_backend_deps()
    check_frontend_deps()

    print("\n[run.py] Starting backend and frontend...\n")

    # start_new_session=True puts each child in its own process group. This
    # matters because `npm run dev` spawns vite as a grandchild process --
    # terminating just the npm process leaves vite running as an orphan.
    # Killing the whole group (see _terminate_group) takes both down.
    backend_proc = subprocess.Popen(
        [str(venv_python), "-m", "uvicorn", "app.main:app", "--port", str(args.backend_port)],
        cwd=BACKEND,
        start_new_session=True,
    )
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(args.frontend_port), "--strictPort"],
        cwd=FRONTEND,
        start_new_session=True,
    )

    def _terminate_group(proc: subprocess.Popen) -> None:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass  # already exited

    def shutdown(*_unused: object) -> None:
        print("\n[run.py] Stopping...")
        _terminate_group(backend_proc)
        _terminate_group(frontend_proc)
        backend_proc.wait()
        frontend_proc.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    time.sleep(2)
    print("\n" + "=" * 60)
    print("  AI Knowledge Inbox is running:")
    print(f"    Frontend  ->  http://localhost:{args.frontend_port}")
    print(f"    Backend   ->  http://localhost:{args.backend_port}")
    print(f"    API docs  ->  http://localhost:{args.backend_port}/docs")
    print("  Press Ctrl+C to stop both.")
    print("=" * 60 + "\n")

    while True:
        if backend_proc.poll() is not None:
            print("[run.py] backend process exited unexpectedly")
            shutdown()
        if frontend_proc.poll() is not None:
            print("[run.py] frontend process exited unexpectedly")
            shutdown()
        time.sleep(1)


if __name__ == "__main__":
    main()
