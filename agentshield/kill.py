"""
AgentShield Kill Switch
=======================
Instant emergency stop for ALL AI agent activity on this machine.

Usage:
    python -m agentshield kill              # Shows what would be killed (dry run)
    python -m agentshield kill --confirm    # Actually kills processes (SIGTERM)
    python -m agentshield kill --confirm --force  # Force kill (SIGKILL)
    python -m agentshield kill --json       # JSON output for programmatic use

What it does:
    1. Scans for known AI agent processes (Claude, GPT, LangChain, Hermes, etc.)
    2. Lists each process with PID, name, and command
    3. Without --confirm: shows what WOULD be killed (dry run)
    4. With --confirm: sends SIGTERM (or SIGKILL with --force) to each process
    5. Prints a summary: killed count, PIDs, next steps

Safety:
    - Never kills the current Python process
    - Never kills system processes (PID < 100)
    - Never kills terminal/shell/windowing processes
    - Always shows a dry run first unless --confirm is passed
"""

import os
import sys
import signal
import subprocess
import json
from datetime import datetime, timezone

# Process patterns that indicate AI agent activity
AGENT_PATTERNS = [
    "claude", "gpt", "openai", "anthropic", "langchain", "llama",
    "hermes", "autogpt", "crewai", "babyagi", "agent-",
    "autogen", "camel", "chatdev", "devin", "ghostwriter",
    "python.*openai", "python.*anthropic", "python.*langchain",
    "python.*llm", "python.*agent", "python.*crewai",
    "node.*openai", "node.*langchain",
    "cli_agent", "agent_runner", "task_executor", "tool_runner",
]

# Process patterns to NEVER kill (safety)
PROTECTED_PATTERNS = [
    "agentshield", "terminal", "bash", "zsh", "fish", "sh",
    "ssh", "sshd", "login", "init", "launchd", "systemd",
    "kernel", "windowserver", "dock", "finder",
    "ControlCenter", "SystemUIServer",
]

PROTECTED_PIDS = {0, 1, os.getpid()}


def find_agent_processes():
    """Find all running processes that look like AI agents."""
    processes = []

    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.strip().split('\n'):
                parts = line.strip('"').split('","')
                if len(parts) >= 2:
                    name = parts[0]
                    pid = int(parts[1])
                    if pid not in PROTECTED_PIDS and pid > 100:
                        cmd = name
                        for pattern in AGENT_PATTERNS:
                            if pattern.lower() in cmd.lower():
                                processes.append({"pid": pid, "name": name, "cmd": cmd})
                                break
        except Exception:
            pass
    else:
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.strip().split('\n')[1:]:
                parts = line.split(None, 10)
                if len(parts) < 11:
                    continue
                user = parts[0]
                pid = int(parts[1])
                cmd = parts[10]

                if pid in PROTECTED_PIDS or pid < 100:
                    continue

                cmd_lower = cmd.lower()
                if any(p.lower() in cmd_lower for p in PROTECTED_PATTERNS):
                    continue

                for pattern in AGENT_PATTERNS:
                    if pattern.lower() in cmd_lower:
                        processes.append({
                            "pid": pid,
                            "name": cmd.split()[0] if cmd.split() else "unknown",
                            "cmd": cmd[:200],
                            "user": user
                        })
                        break
        except Exception:
            pass

    return processes


def kill_process(pid, force=False):
    """Kill a process by PID. Returns True on success."""
    try:
        if force:
            os.kill(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGTERM)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return False
    except Exception:
        return False


def main():
    """Run the kill switch."""
    confirm = "--confirm" in sys.argv or "-y" in sys.argv
    force = "--force" in sys.argv or "-f" in sys.argv
    json_output = "--json" in sys.argv

    processes = find_agent_processes()

    if json_output:
        output = {
            "mode": "kill" if confirm else "dry-run",
            "force": force,
            "found": len(processes),
            "processes": processes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if confirm:
            killed = []
            for p in processes:
                success = kill_process(p["pid"], force=force)
                p["killed"] = success
                if success:
                    killed.append(p["pid"])
            output["killed"] = len(killed)
            output["killed_pids"] = killed
        print(json.dumps(output, indent=2))
        return

    print()
    print("=" * 60)
    print("  AGENTSHIELD KILL SWITCH")
    print("=" * 60)
    print()

    if not processes:
        print("  [OK] No AI agent processes found.")
        print("  Your machine is clear of known agent activity.")
        print()
        return

    prefix = "[!]" if not confirm else "[X]"
    print(f"  {prefix} Found {len(processes)} AI agent process(es):")
    print()

    for i, p in enumerate(processes, 1):
        print(f"  {i}. PID {p['pid']:6} | {p['cmd'][:80]}")
    print()

    if not confirm:
        print("  DRY RUN -- No processes were killed.")
        print("  To kill: python -m agentshield kill --confirm")
        print()
        return

    killed_count = 0
    for p in processes:
        success = kill_process(p["pid"], force=force)
        status = "[KILLED]" if success else "[FAILED]"
        print(f"  {status} PID {p['pid']:6} | {p['cmd'][:60]}")
        if success:
            killed_count += 1

    print()
    sig = "SIGKILL (force)" if force else "SIGTERM (graceful)"
    print(f"  {killed_count}/{len(processes)} agent process(es) terminated via {sig}.")
    print()
    print("  Next steps:")
    print("    1. Check API dashboards for recent spend")
    print("    2. Review agent logs for runaway activity causes")
    print("    3. Prevent recurrence:")
    print("       pip install agentshield-spend")
    print("       python -m agentshield.emergency")
    print()
    print("  https://agentshield.sipiteno.com")
    print("=" * 60)


if __name__ == "__main__":
    main()
