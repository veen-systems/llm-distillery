#!/usr/bin/env python3
"""Claude Code PreToolUse hook: refuse `pkill -f` / `pgrep -f` in a Bash command.

The pattern sits on the argv of the shell that runs it, so `pgrep -f` matches the
caller and `pkill -f` kills it (exit 144 mid-script). Five occurrences in
`memory/gotcha-log.md` while the rule was written in CLAUDE.md and
`memory/working-rules.md` — prose did not stop it, so this blocks it.

Only a command in COMMAND POSITION is refused: start of a line, after `;`, `&`, `|`,
`(`, `{`, `!`, `$(` or a shell keyword — NOT a backtick: markdown code spans quote the
command constantly in this repo (a backtick trigger blocked the row describing this hook,
2026-10-09) — or as the remote command of `ssh [options] host ...` / `bash -c '...'`
(the remote shell has the same trap). Wrappers in front of it are seen through
(`sudo [-u x]`, `env`, `nohup`, `exec`, `command`, `nice`, `timeout N`, `xargs`, `watch`,
`VAR=value`, a path such as `/usr/bin/`), since each keeps the pattern on an argv.

⚠️ LEXICAL, and so it cannot tell use from mention in two shapes (review 2026-10-09):
a LINE of a multi-line string or heredoc that starts with the command, and the command
after `;`/`|` inside a quoted string. Both are blocked though nothing would run. Reword
(put a word before it). A mention mid-line passes.

Exit 2 blocks the call and shows stderr to the model; exit 0 lets it through.
Malformed input exits 0: a broken hook must not block every Bash call. The settings
entry also exits 0 when this file is missing (python3 exits 2 on a missing script, and
2 is the blocking code).
"""
import json
import re
import sys

_POSITION = (
    r"""(?:^|[;&|({!]|\$\("""                                       # separators
    r"""|\b(?:until|while|if|elif|then|do|else|time)\s"""           # shell keywords
    r"""|\bssh(?:\s+[^\s'";|&]+)*?\s+(?:--\s+)?['"]?"""             # ssh [opts] host [--] ['"]
    r"""|\s-c\s+['"])"""                                            # bash -c '...'
)
_WRAPPERS = (
    r"""(?:(?:sudo(?:\s+-\S+(?:\s+[^\s-]\S*)?)*|env|nohup|exec|command|nice(?:\s+-\S+)*"""
    r"""|timeout(?:\s+-\S+)*\s+\S+|xargs(?:\s+-\S+)*|watch(?:\s+-\S+(?:\s+\d+)?)*"""
    r"""|\w+=\S*)\s+)*"""
)
PATTERN = re.compile(
    _POSITION + r"""\s*""" + _WRAPPERS + r"""\\?(?:\S*/)?(pkill|pgrep)\b"""
    r"""(?=[^;&|\n]*?\s(?:-[A-Za-z]*f[A-Za-z]*|--full)\b)""",      # with -f / -af / -fl / --full
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
