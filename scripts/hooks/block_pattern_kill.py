#!/usr/bin/env python3
"""Claude Code PreToolUse hook: refuse `pkill -f` / `pgrep -f` in a Bash command.

The pattern sits on the argv of the shell that runs it, so `pgrep -f` matches the
caller and `pkill -f` kills it (exit 144 mid-script). Five occurrences in
`memory/gotcha-log.md` while the rule was written in CLAUDE.md and
`memory/working-rules.md` — prose did not stop it, so this blocks it.

A TOKENIZER, not a regex (review round 3, 2026-10-09): the regex this replaces nested a
repeated ssh-options group inside a repeated wrapper group and backtracked exponentially
(25 repeats of `ssh h ` took 13 s, and this runs before every Bash call). Before lexing,
a line continuation (`\\` + newline) is joined, an escaped separator (`\\;`) becomes a word,
and the BODY of a `cat`/`tee` heredoc is dropped (it is text, not commands: the
`git commit -m "$(cat <<'EOF' ...)"` idiom). Then `shlex` splits the command into words,
a separator (`;`, `&`, `|`, `(`, `)`, newline) starts a new command, a redirection
(`>`, `2>&1`, `<<EOF`) is dropped with its target, and each command is read left to right:

- leading shell keywords (`if`, `then`, `do`, `!`, `{`, `function NAME`, `coproc [NAME]`
  ...) and `VAR=value` are skipped;
- a LAUNCHER and its options are peeled off, values included (`sudo -u x`, `env -i`,
  `nice -n 10`, `timeout -s KILL 5`, `exec -a name`, `time -p`, `xargs -n 1`, `ionice -c3`,
  `setsid`, `stdbuf -oL`, `chrt 1`, `flock FILE`, `docker [compose] exec -it C`, ...);
- a command STRING handed to a shell is read again as a command: `bash -c` / `-lc`,
  `su [user] -c`, `flock FILE -c`, `env -S`, the remote command of `ssh [options] host
  [--] ...` and `sshpass -p x ssh ...`, the command of `watch -n1 '...'`, anything after `$(`;
- then the command is refused if its name (any path, e.g. `/usr/bin/`) is `pkill` or
  `pgrep` and a later word before `--` is `-f`, a cluster holding `f`, or `--full`.
  Past the nesting limit, any such pair of words anywhere in the string is refused.

So a QUOTED mention passes (`git commit -m "... ssh in and pgrep -f ..."`), and so does a
mention mid-sentence.

⚠️ Not seen (measured by the 2026-10-09 review, kept as known gaps): a real backtick
substitution (excluded on purpose: markdown code spans quote the command constantly here,
and a backtick trigger blocked the row describing this hook), `eval`, `bash <<<'...'`,
`kubectl -n ns exec`, and launchers not listed above (`tmux`, `script -c`, `doas`, ...).
Still blocked though nothing would run: a line of a NON-cat heredoc body that starts with
the command (shlex does not know heredocs; `ssh host bash -s <<EOF` bodies DO run), `$(`
inside single quotes, and text after `#` (comments are not stripped). Reword. A command
with unbalanced quotes is re-read with its quote characters removed, so it errs toward
blocking.

Exit 2 blocks the call and shows stderr to the model; exit 0 lets it through.
Malformed input, or any internal error, exits 0: a broken hook must not block every Bash
call. The settings entry also exits 0 when this file is missing (python3 exits 2 on a
missing script, and 2 is the blocking code).
"""
import json
import re
import shlex
import sys

TARGETS = {"pkill", "pgrep"}
KEYWORDS = {"if", "then", "elif", "else", "do", "while", "until", "!", "{", "}"}
_PUNCTUATION = "();<>|&\n"
_ASSIGNMENT = re.compile(r"^[A-Za-z_]\w*=")
_FULL_FLAG = re.compile(r"^-[A-Za-z]*f[A-Za-z]*$")
_CAT_HEREDOC = re.compile(r"""(?:^|[\s;&|(])(?:cat|tee)\b[^\n]*?<<-?\s*(['"]?)([A-Za-z_]\w*)\1""")
_MAX_DEPTH = 6

# name: (short options that take a SEPARATE value, long options that take a value without
#        `=`, positional words before the command, how the command is handed over)
# mode "argv": the command follows as words; "string": it is ONE word re-read as a
#        command (after a `-c` cluster); "rest": every remaining word, joined, is re-read.
# ⚠️ An option whose value is OPTIONAL and attached (`xargs -i`, `watch -d`) must NOT be
# listed: it would swallow the command word (review 2026-10-09).
_LAUNCHERS = {
    "sudo": ("ugCDhprtUT", {"--user", "--group", "--host", "--prompt", "--chdir"}, 0, "argv"),
    "env": ("uC", {"--unset", "--chdir"}, 0, "argv"),
    "nohup": ("", set(), 0, "argv"),
    "exec": ("a", set(), 0, "argv"),
    "command": ("", set(), 0, "argv"),
    "builtin": ("", set(), 0, "argv"),
    "time": ("fo", {"--format", "--output"}, 0, "argv"),
    "nice": ("n", {"--adjustment"}, 0, "argv"),
    "timeout": ("sk", {"--signal", "--kill-after"}, 1, "argv"),
    "xargs": ("InPLsdaE", {"--max-args", "--max-procs", "--delimiter", "--arg-file"}, 0, "argv"),
    "setsid": ("", set(), 0, "argv"),
    "stdbuf": ("ioe", {"--input", "--output", "--error"}, 0, "argv"),
    "ionice": ("cnp", {"--class", "--classdata", "--pid"}, 0, "argv"),
    "chrt": ("", set(), 1, "argv"),
    "taskset": ("", set(), 1, "argv"),
    "systemd-run": ("pEu", {"--property", "--setenv", "--unit", "--description"}, 0, "argv"),
    "sshpass": ("pfdP", set(), 0, "argv"),
    "watch": ("n", {"--interval"}, 0, "rest"),
    "ssh": ("bcDEeFIiJLlmOopQRSWw", set(), 1, "rest"),
    "flock": ("wEn", {"--timeout", "--conflict-exit-code"}, 1, "string"),
    "su": ("gsGw", {"--group", "--shell", "--supp-group"}, 0, "string"),
    "runuser": ("ugsGw", {"--user", "--group", "--shell"}, 0, "string"),
    **{sh: ("oO", set(), 0, "string") for sh in ("sh", "bash", "dash", "zsh", "ksh")},
}
# `docker [compose] exec [opts] CONTAINER cmd ...`: a launcher only with its subcommand.
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


def _drop_cat_heredoc_bodies(text: str) -> str:
    """Remove the body lines of `cat <<EOF` / `tee f <<'EOF'` heredocs (text, not commands)."""
    out, delim = [], None
    for line in text.split("\n"):
        if delim is not None:
            if line.strip() == delim:
                delim = None
                out.append(line)
            continue
        out.append(line)
        m = _CAT_HEREDOC.search(line)
        if m:
            delim = m.group(2)
    return "\n".join(out)


def _words(command: str) -> list[str]:
    def lex(text):
        lx = shlex.shlex(text, posix=True, punctuation_chars=_PUNCTUATION)
        lx.whitespace = " \t\r"
        lx.whitespace_split = True
        lx.commenters = ""
        return list(lx)

    text = _drop_cat_heredoc_bodies(command)
    text = text.replace("\\\n", " ")                      # a line continuation is not a separator
    text = re.sub(r"\\([;&|<>()])", r"_\1_", text)        # nor is an escaped one (`-exec ... \;`)
    try:
        return lex(text)
    except ValueError:  # unbalanced quotes or a trailing `\`: drop them, err toward blocking
        return lex(re.sub(r"[\"'\\]", " ", text))


def _commands(words: list[str]):
    current: list[str] = []
    skip_target = False
    for w in words:
        if skip_target:                                   # the file of a redirection
            skip_target = False
            continue
        if w and all(c in _PUNCTUATION for c in w):
            if "(" in w or ")" in w or not any(c in "<>" for c in w):
                if current:
                    yield current
                current = []
            else:                                         # `>`, `2>&1`, `<<`, `&>`: a redirection
                skip_target = True
                if current and current[-1].isdigit():     # its fd (`2>`), lexed as a word
                    current.pop()
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
            if c == "S" and c_is_command is None:
                return i + 1, i + 1        # env -S 'cmd args'
            if c in short_values:
                i += 1 if k + 1 < len(letters) else 2
                break
        else:
            i += 1
    return i, None


def _has_full_flag(args):
    for a in args:
        if a == "--":
            return False                   # after `--` a `-f` is the pattern, not the flag
        if _FULL_FLAG.match(a) or a == "--full":
            return True
    return False


def _crude(words):
    """Past the nesting limit: refuse any target followed anywhere by a full-match flag."""
    for k, w in enumerate(words):
        name = w.rsplit("/", 1)[-1]
        if name in TARGETS and _has_full_flag(words[k + 1:]):
            return name
    return None


def _check_command(words: list[str], depth: int):
    for w in words:                                        # a substitution inside any (quoted) word
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
        if w == "function":                                # `function NAME {`
            i += 2
            continue
        if w == "coproc":                                  # `coproc [NAME] { ...; }` / `coproc cmd`
            i += 2 if words[i + 2:i + 3] == ["{"] else 1
            continue
        if name in TARGETS:
            return name if _has_full_flag(words[i + 1:]) else None
        spec = _LAUNCHERS.get(name)
        if spec is None and name in _EXEC_LAUNCHERS:
            sub = words[i + 1:i + 3]
            hop = 1 if sub[:1] == ["exec"] else 2 if sub == ["compose", "exec"] else 0
            if hop:
                short, long_, npos = _EXEC_LAUNCHERS[name]
                spec, i = (short, long_, npos, "argv"), i + hop
        if spec is None:
            return None                            # some other command: a mention at most
        short, long_, npos, mode = spec
        c_mode = True if mode == "string" else (None if name == "env" else False)
        i, cstring = _skip_options(words, i + 1, short, long_, c_mode)
        if cstring is None and mode == "string":
            # `su root -c ...` / `flock FILE -c ...`: the -c follows ONE positional at most,
            # so the command's own `-c` (`flock F <pgrep> -c -f x`) is not mistaken for it
            for j in range(i, min(i + 2, len(words))):
                if words[j].startswith("-") and not words[j].startswith("--") and "c" in words[j]:
                    cstring = j + 1
                    break
        if cstring is not None:
            return offending(words[cstring], depth + 1) if cstring < len(words) else None
        if mode == "string" and name not in ("flock", "runuser"):
            return None                            # `bash script.sh`, an interactive `su`
        i += npos
        i, _ = _skip_options(words, i, short, long_)   # ssh accepts options after the host
        if mode == "rest":
            # The remote shell sees the words joined by spaces; shlex.join also keeps a quoted
            # word whole (`ssh h bash -lc '...'`). Either reading blocks.
            rest = words[i:]
            return offending(" ".join(rest), depth + 1) or offending(shlex.join(rest), depth + 1)
    return None


def offending(command: str, depth: int = 0):
    words = _words(command)
    if depth > _MAX_DEPTH:
        return _crude(words)
    for cmd in _commands(words):
        hit = _check_command(cmd, depth)
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
