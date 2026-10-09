#!/usr/bin/env python3
"""Claude Code PreToolUse hook: refuse `pkill -f` / `pgrep -f` in a Bash command.

The pattern sits on the argv of the shell that runs it, so `pgrep -f` matches the
caller and `pkill -f` kills it (exit 144 mid-script). Five occurrences in
`memory/gotcha-log.md` while the rule was written in CLAUDE.md and
`memory/working-rules.md` — prose did not stop it, so this blocks it.

Only a command in COMMAND POSITION is refused: start of a line, after `;`, `&`, `|`,
`(`, `!`, `$(` or a shell keyword — NOT a backtick: markdown code spans quote the
command constantly in this repo (a backtick trigger blocked the row describing this hook,
2026-10-09) — or as the quoted command of `ssh host '...'`
/ `bash -c '...'` (the remote shell has the same trap). A mention mid-sentence or inside
another command's quoted argument (a commit message, `grep 'pgrep -f'`) passes.

Exit 2 blocks the call and shows stderr to the model; exit 0 lets it through.
Malformed input exits 0: a broken hook must not block every Bash call.
"""
import json
import re
import sys

PATTERN = re.compile(
    r"""(?:^|[;&|(!]|\$\(|\b(?:until|while|if|then|do|else|time)\s"""  # command position,
    r"""|(?:\bssh\s+(?:-\S+\s+)*[\w.@-]+|\s-c)\s+['"])"""               # or a remote/-c shell
    r"""\s*(?:sudo\s+)?(pkill|pgrep)\b"""
    r"""(?=[^;&|\n]*?\s(?:-[A-Za-z]*f[A-Za-z]*|--full)\b)""",  # with -f / -af / -fl / --full
    re.MULTILINE,
)

MESSAGE = (
    "Blocked: `{cmd} -f` matches the shell that carries its own pattern "
    "(memory/gotcha-log.md, the pkill entry; CLAUDE.md working rules). "
    "Instead: `ps -eo pid,etime,args | grep -v grep | grep <pattern>`, PRINT the matching "
    "line, then `kill <pid>` by PID. For services: `systemctl list-units 'nexusmind*' --all`."
)


def offending(command: str):
    m = PATTERN.search(command)
    return m.group(1) if m else None


def main() -> int:
    try:
        data = json.load(sys.stdin)
        command = data.get("tool_input", {}).get("command", "")
    except (ValueError, AttributeError):
        return 0
    cmd = offending(command or "")
    if cmd:
        print(MESSAGE.format(cmd=cmd), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
