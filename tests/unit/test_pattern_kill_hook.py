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
    # review round 2, 2026-10-09: wrapper options that take values, and `-lc`
    "env -i pgrep -f x",
    "nice -n 10 pkill -f x",
    "timeout -s KILL 5 pgrep -f x",
    "bash -lc 'pgrep -f x'",
    "sudo bash -c 'pkill -f x'",
    "watch -n1 'pgrep -f x'",
    "watch -n 1 'pgrep -af x'",
    "ssh host 'cd /x && pkill -f y'",
    "ssh host bash -lc 'pgrep -f x'",
    # review round 3, 2026-10-09: blocked at HEAD, lost by the round-2 regex
    "su -c 'pkill -f x'",
    "su root -c 'pkill -f x'",
    "docker exec c sh -c 'pgrep -f x'",
    "sshpass -p x ssh host 'pkill -f x'",
    "flock /tmp/l -c 'pkill -f x'",
    # ... and missed by HEAD too
    "time -p pgrep -f x",
    "exec -a name pkill -f x",
    "setsid pkill -f x",
    "stdbuf -oL pgrep -f x",
    "ionice -c3 pkill -f x",
    "chrt 1 pkill -f x",
    "systemd-run --user pkill -f x",
    "runuser -u x -- pkill -f y",
    "flock /tmp/l pkill -f x",
    "docker exec -it c pgrep -f x",
    'ssh -t host "bash -lc \'pgrep -f x\'"',
    'echo "$(pgrep -f x)"',
    "bash -o pipefail -c 'pgrep -f x'",
    "pgrep -f x \\",                                    # trailing backslash: shlex raises (fuzz)
    "ssh host 'pkill -f x",                             # unbalanced quote
    # review round 4, 2026-10-09 (one adversarial pass on the tokenizer)
    "ssh -o BatchMode=yes \\\nsadalsuud 'pgrep -f main.py'",   # line continuation
    "pgrep -u me \\\n-f x",
    "function f { pgrep -f x; }",
    "coproc W { pgrep -f x; }",
    "coproc pgrep -f x",
    "xargs -i pkill -f {}",                             # -i: optional ATTACHED value
    "sshpass -e ssh host 'pkill -f x'",                 # -e takes no value
    "watch -d 'pgrep -f x'",
    "watch -n 1 -d 'pgrep -f x'",
    "pgrep 2>/dev/null -f x",                           # a redirection is not a separator
    "2>/dev/null pgrep -f x",
    "pgrep -f x >/dev/null 2>&1",
    "env -S 'pgrep -f x'",
    "docker compose exec svc pgrep -f x",
    "flock /tmp/l pgrep -c -f x",                       # the command's own -c
    "ssh h " * 8 + "'pgrep -f x'",                     # past the nesting limit
    "ssh host bash -s <<EOF\npkill -f x\nEOF",          # a heredoc body that RUNS
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
    # review round 2, 2026-10-09: the loosened ssh branch matched mid-sentence
    'git commit -m "never ssh in and run pgrep -f"',
    'gh issue comment 1 --body "ssh sadalsuud and pkill -f the scorer"',
    "echo run bash -c pgrep -f later",
    "python3 -c 'print(1)'",
    # review round 3, 2026-10-09: a quoted separator no longer starts a command
    'git commit -m "first line; pkill -f was the trap"',
    'gh issue create --body "then pkill -f the thing"',
    "bash script.sh -f",
    # review round 4, 2026-10-09: the commit/issue-body idiom and heredoc'd markdown
    "git commit -m \"$(cat <<'EOF'\nfix: (pkill -f matched its own shell); pgrep -f too\n"
    "| pkill -f | row |\npkill -f at line start\nEOF\n)\"",
    "gh issue comment 1 --body \"$(cat <<EOF\n| \\`pgrep -f\\` | blocked |\nEOF\n)\"",
    "cat > doc.md <<'EOF'\n> pkill -f matches its own shell\nEOF",
    "tee -a notes.md <<'EOF' >/dev/null\npgrep -f x is the trap\nEOF\necho done",
    "pgrep -x -- -f",                                   # -f after `--` is the pattern
    "find . -name '*.py' -exec grep -l x {} \\;",
    "su",
    "ssh host",
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


@pytest.mark.parametrize("unit", ["ssh h ", "ssh h\n", "watch -n1 ", "env -i ",
                                  "sudo -u x env -i nice -n 1 ", "bash -c "])
def test_no_catastrophic_backtracking(unit):
    """Review round 3, 2026-10-09: the round-2 regex took 13 s on 25 x `ssh h ` and 61 s
    on 25 x the sudo/env/nice chain; this hook runs before every Bash call."""
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": unit * 2000}})
    try:  # a subprocess, so a regression fails here instead of hanging the suite
        subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True,
                       text=True, timeout=5)
    except subprocess.TimeoutExpired:
        pytest.fail(f"hook took > 5 s on 2000 x {unit!r}")


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
