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
    # review 2026-10-09: forms the first version missed (each keeps the pattern on an argv)
    "ssh -o BatchMode=yes -o ConnectTimeout=5 sadalsuud 'pgrep -f main.py'",
    "ssh -i key host 'pkill -f x'",
    "ssh host pkill -f x",
    "ssh host -- 'pgrep -f x'",
    "timeout 5 pgrep -f x",
    "nohup pkill -f x",
    "env pgrep -f x",
    "xargs pkill -f",
    "sudo -u jeroen pkill -f x",
    "FOO=1 pgrep -f x",
    "/usr/bin/pgrep -f x",
    "if true; then :; elif pgrep -f x; then :; fi",
    "{ pkill -f x; }",
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


def _settings_command():
    hooks = json.loads(SETTINGS.read_text())["hooks"]["PreToolUse"]
    cmds = [h for entry in hooks if entry.get("matcher") == "Bash" for h in entry["hooks"]
            if "block_pattern_kill.py" in h.get("command", "")]
    assert len(cmds) == 1 and cmds[0].get("type") == "command", cmds
    return cmds[0]["command"]


def _run_settings_command(project_dir, command):
    import os
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project_dir))
    return subprocess.run(["bash", "-c", _settings_command()], input=payload,
                          capture_output=True, text=True, env=env)


def test_hook_is_wired_into_project_settings_and_blocks_through_it():
    """The settings entry itself, executed as Claude Code executes it, must block."""
    r = _run_settings_command(REPO, "pgrep -f x")
    assert r.returncode == 2 and "Blocked" in r.stderr
    assert _run_settings_command(REPO, "ls").returncode == 0


def test_missing_script_does_not_block_every_bash_call(tmp_path):
    """Review 2026-10-09: python3 exits 2 on a missing script, and 2 is the BLOCKING
    code, so a moved script would have blocked every Bash call."""
    r = _run_settings_command(tmp_path, "pgrep -f x")
    assert r.returncode == 0, r.stderr
