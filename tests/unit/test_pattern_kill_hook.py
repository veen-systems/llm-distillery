"""Seeded cases for scripts/hooks/block_pattern_kill.py (the pkill/pgrep -f hook).

Each BLOCK case is a command shape that has, or would, match its own shell. Each PASS
case is a mention or a safe form that a lexical guard must not refuse.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HOOK = REPO / "scripts" / "hooks" / "block_pattern_kill.py"
SETTINGS = REPO / ".claude" / "settings.json"

BLOCK = [
    'pkill -f -- "-L 11435:localhost:11434"',          # the 2026-08-21 occurrence
    "pgrep -f main.py",
    "pgrep -af scorer",
    "pkill -9 -f train.py",
    "pkill --full train.py",
    "sudo pkill -f nexusmind",
    "cd /x && pkill -f foo",
    "echo start; pgrep -fl python",
    "ssh sadalsuud 'pkill -f main.py'",
    'ssh b650-gpu "pgrep -f ollama"',
    "until ! pgrep -f main.py; do sleep 10; done",
    "x=$(pgrep -f main.py)",
    "ls\npkill -f foo",
]

PASS = [
    "ps -eo pid,etime,args | grep -v grep | grep main.py",
    "kill 12345",
    "pkill ollama",                                     # no -f: matches the process name only
    "pgrep -x python",
    'git commit -m "the pkill -f trap killed its own shell"',
    "grep -n 'pgrep -f' CLAUDE.md",
    "echo use pkill -f carefully",
    # 2026-10-09: a backtick trigger blocked the heredoc writing this hook's own table row
    "python3 - <<'EOF'\nrow = '| `pkill -f` / `pgrep -f` matches its own shell |'\nEOF",
    "systemctl list-units 'nexusmind*' --all",
    "",
]


def run(command):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True)


@pytest.mark.parametrize("command", BLOCK)
def test_blocks(command):
    r = run(command)
    assert r.returncode == 2, command
    assert "Blocked" in r.stderr


@pytest.mark.parametrize("command", PASS)
def test_passes(command):
    r = run(command)
    assert r.returncode == 0, (command, r.stderr)


def test_malformed_input_does_not_block():
    r = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True)
    assert r.returncode == 0


def test_hook_is_wired_into_project_settings():
    hooks = json.loads(SETTINGS.read_text())["hooks"]["PreToolUse"]
    cmds = [h["command"] for entry in hooks if entry.get("matcher") == "Bash" for h in entry["hooks"]]
    assert any("block_pattern_kill.py" in c for c in cmds)
