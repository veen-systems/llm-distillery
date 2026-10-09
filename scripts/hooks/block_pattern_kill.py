#!/usr/bin/env python3
"""Claude Code PreToolUse hook: refuse `pkill -f` / `pgrep -f` in a Bash command.

The pattern sits on the argv of the shell that runs it, so `pgrep -f` matches the
caller and `pkill -f` kills it (exit 144 mid-script). Five occurrences in
`memory/gotcha-log.md` while the rule was written in CLAUDE.md and
`memory/working-rules.md` — prose did not stop it, so this blocks it.

A TOKENIZER, not a regex (review round 3, 2026-10-09): the regex this replaces nested a
repeated ssh-options group inside a repeated wrapper group and backtracked exponentially
(25 repeats of `ssh h ` took 13 s, and this runs before every Bash call). `shlex` splits
the command into words, a separator (`;`, `&`, `|`, `(`, `)`, `<`, `>`, newline) starts a
new command, and each command is read left to right in one pass:

- leading shell keywords (`if`, `then`, `do`, `!`, `{` ...) and `VAR=value` are skipped;
- a LAUNCHER and its options are peeled off, values included (`sudo -u x`, `env -i`,
  `nice -n 10`, `timeout -s KILL 5`, `exec -a name`, `time -p`, `xargs -n 1`, `ionice -c3`,
  `setsid`, `stdbuf -oL`, `chrt 1`, `flock FILE`, `docker exec -it C`, ...);
- a command STRING handed to a shell is read again as a command: `bash -c` / `-lc`,
  `su [user] -c`, `flock FILE -c`, the remote command of `ssh [options] host [--] ...`
  and `sshpass -p x ssh ...`, the command of `watch -n1 '...'`, and anything after `$(`;
- then the command is refused if its name (any path, e.g. `/usr/bin/`) is `pkill` or
  `pgrep` and a later word in the same command is `-f`, a cluster holding `f`, or `--full`.

So a QUOTED mention passes (`git commit -m "... ssh in and pgrep -f ..."`), and so does a
mention mid-sentence. NOT a backtick: markdown code spans quote the command constantly in
this repo (a backtick trigger blocked the row describing this hook, 2026-10-09).

⚠️ Still lexical in two shapes: a LINE of an unquoted heredoc body that starts with the
command is read as a command (shlex does not know heredocs), and `$(` inside single quotes
is read as a substitution. Both are blocked though nothing would run; reword. A command
with unbalanced quotes is re-read with its quote characters removed, so it errs toward
blocking. Not seen through: `eval`, `bash <<<'...'`, and launchers not listed above.

Exit 2 blocks the call and shows stderr to the model; exit 0 lets it through.
Malformed input exits 0: a broken hook must not block every Bash call. The settings
entry also exits 0 when this file is missing (python3 exits 2 on a missing script, and
2 is the blocking code).
"""
import json
import re
import shlex
import sys

TARGETS = {"pkill", "pgrep"}
KEYWORDS = {"if", "then", "elif", "else", "do", "while", "until", "!", "{", "}"}
_SEPARATOR_CHARS = "();<>|&\n"
_ASSIGNMENT = re.compile(r"^[A-Za-z_]\w*=")
_FULL_FLAG = re.compile(r"^-[A-Za-z]*f[A-Za-z]*$")
_MAX_DEPTH = 6

# name: (short options that take a value, long options that take a value without `=`,
#        positional words before the command, how the command is handed over)
# mode "argv": the command follows as words; "string": it is ONE word re-read as a
#        command (after a `-c` cluster); "rest": every remaining word, joined, is re-read.
_LAUNCHERS = {
    "sudo": ("ugCDhprtUT", {"--user", "--group", "--host", "--prompt", "--chdir"}, 0, "argv"),
    "env": ("uCS", {"--unset", "--chdir"}, 0, "argv"),
    "nohup": ("", set(), 0, "argv"),
    "exec": ("a", set(), 0, "argv"),
    "command": ("", set(), 0, "argv"),
    "builtin": ("", set(), 0, "argv"),
    "time": ("fo", {"--format", "--output"}, 0, "argv"),
    "nice": ("n", {"--adjustment"}, 0, "argv"),
    "timeout": ("sk", {"--signal", "--kill-after"}, 1, "argv"),
    "xargs": ("IinPLsdaE", {"--max-args", "--max-procs", "--delimiter", "--arg-file"}, 0, "argv"),
    "setsid": ("", set(), 0, "argv"),
    "stdbuf": ("ioe", {"--input", "--output", "--error"}, 0, "argv"),
    "ionice": ("cnp", {"--class", "--classdata", "--pid"}, 0, "argv"),
    "chrt": ("", set(), 1, "argv"),
    "taskset": ("", set(), 1, "argv"),
    "systemd-run": ("pEu", {"--property", "--setenv", "--unit"}, 0, "argv"),
    "sshpass": ("pfdeP", set(), 0, "argv"),
    "watch": ("nd", {"--interval"}, 0, "rest"),
    "ssh": ("bcDEeFIiJLlmOopQRSWw", set(), 1, "rest"),
    "flock": ("wEn", {"--timeout", "--conflict-exit-code"}, 1, "string"),
    "su": ("gsGw", {"--group", "--shell", "--supp-group"}, 0, "string"),
    "runuser": ("ugsGw", {"--user", "--group", "--shell"}, 0, "string"),
    **{sh: ("oO", set(), 0, "string") for sh in ("sh", "bash", "dash", "zsh", "ksh")},
}
# `docker exec [opts] CONTAINER cmd ...`: a launcher only with its subcommand.
_EXEC_LAUNCHERS = {
    "docker": ("euw", {"--env", "--env-file", "--user", "--workdir"}, 1),
    "podman": ("euw", {"--env", "--env-file", "--user", "--workdir"}, 1),
    "kubectl": ("cn", {"--container", "--namespace"}, 1),
}

MESSAGE = (
    "Blocked: `{cmd} -f` matches the shell that carries its own pattern "
    "(memory/gotcha-log.md, the pkill entry; CLAUDE.md working rules). "
    "Instead: `ps -eo pid,etime,args | grep -v grep | grep <pattern>`, PRINT the matching "
    "line, then `kill <pid>` by PID. For services: `systemctl list-units 'nexusmind*' --all`."
)


def _words(command: str) -> list[str]:
    def lex(text):
        lx = shlex.shlex(text, posix=True, punctuation_chars=_SEPARATOR_CHARS)
        lx.whitespace = " \t\r"
        lx.whitespace_split = True
        lx.commenters = ""
        return list(lx)

    try:
        return lex(command)
    except ValueError:  # unbalanced quotes or a trailing `\`: drop them, err toward blocking
        return lex(re.sub(r"[\"'\\]", " ", command))


def _commands(words: list[str]):
    current: list[str] = []
    for w in words:
        if w and all(c in _SEPARATOR_CHARS for c in w):
            if current:
                yield current
            current = []
        else:
            current.append(w)
    if current:
        yield current


def _skip_options(words, i, short_values, long_values, c_is_command=False):
    """Advance past option words (and their values). Returns (index, -c string index or None)."""
    while i < len(words) and words[i].startswith("-") and words[i] != "-":
        w = words[i]
        if w == "--":
            return i + 1, None
        if w.startswith("--"):
            i += 2 if ("=" not in w and w in long_values) else 1
            continue
        letters = w[1:]
        for k, c in enumerate(letters):
            if c == "c" and c_is_command:
                return i + 1, i + 1        # a -c cluster: the next word is a command string
            if c in short_values:
                i += 1 if k + 1 < len(letters) else 2
                break
        else:
            i += 1
    return i, None


def _check_command(words: list[str], depth: int):
    if depth < _MAX_DEPTH:
        for w in words:                            # a substitution inside any (quoted) word
            if "$(" in w:
                hit = offending(w.split("$(", 1)[1], depth + 1)
                if hit:
                    return hit
    i = 0
    while i < len(words):
        w = words[i]
        name = w.lstrip("\\").rsplit("/", 1)[-1]
        if w in KEYWORDS or _ASSIGNMENT.match(w):
            i += 1
            continue
        if name in TARGETS:
            return name if any(_FULL_FLAG.match(a) or a == "--full" for a in words[i + 1:]) else None
        spec = _LAUNCHERS.get(name)
        if spec is None and name in _EXEC_LAUNCHERS and words[i + 1:i + 2] == ["exec"]:
            short, long_, npos = _EXEC_LAUNCHERS[name]
            spec, i = (short, long_, npos, "argv"), i + 1
        if spec is None:
            return None                            # some other command: a mention at most
        short, long_, npos, mode = spec
        i, cstring = _skip_options(words, i + 1, short, long_, mode == "string")
        if cstring is None and mode == "string":
            # `su root -c ...` / `flock FILE -c ...`: the -c may follow positionals
            for j in range(i, len(words)):
                if words[j].startswith("-") and not words[j].startswith("--") and "c" in words[j]:
                    cstring = j + 1
                    break
        if cstring is not None:
            if depth >= _MAX_DEPTH or cstring >= len(words):
                return None
            return offending(words[cstring], depth + 1)
        if mode == "string" and name not in ("flock", "runuser"):
            return None                            # `bash script.sh`, an interactive `su`
        i += npos
        i, _ = _skip_options(words, i, short, long_)   # ssh accepts options after the host
        if mode == "rest":
            # The remote shell sees the words joined by spaces; shlex.join also keeps a quoted
            # word whole (`ssh h bash -lc '...'`). Either reading blocks.
            if depth >= _MAX_DEPTH:
                return None
            rest = words[i:]
            return offending(" ".join(rest), depth + 1) or offending(shlex.join(rest), depth + 1)
    return None


def offending(command: str, depth: int = 0):
    for words in _commands(_words(command)):
        hit = _check_command(words, depth)
        if hit:
            return hit
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
        command = data.get("tool_input", {}).get("command", "")
    except (ValueError, AttributeError):
        return 0
    try:
        cmd = offending(command or "")
    except Exception:  # a tokenizer bug must not break every Bash call
        return 0
    if cmd:
        print(MESSAGE.format(cmd=cmd), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
