#!/usr/bin/env python3
"""
parse-man.py - Parse a command's man page and generate a what-the-shell data file.

Usage:
    python3 tools/parse-man.py <command>

The generated file is written to data/<command>.json in the repo root.
"""

import json
import os
import re
import subprocess
import sys


def get_man_page(command):
    """Return the plain-text man page for *command*."""
    env = {**os.environ, "MANPAGER": "cat", "MANWIDTH": "200"}
    result = subprocess.run(
        ["man", "--", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env=env,
    )
    if result.returncode != 0:
        raise SystemExit(f"Error: no man page found for '{command}'")
    # Strip overstrike formatting (char + backspace + char = bold/underline in terminals)
    text = re.sub(r".\x08", "", result.stdout)
    return text


def _section_lines(text, *preferred_sections):
    """
    Return the lines that belong to the first matching section heading.

    Falls back to DESCRIPTION if none of *preferred_sections* are found.
    Top-level headings are lines with no leading whitespace that consist of
    uppercase letters (and spaces/hyphens), e.g. "OPTIONS" or "DESCRIPTION".
    """
    lines = text.splitlines()
    heading_re = re.compile(r"^[A-Z][A-Z _-]+$")

    sections = {}  # name -> (start_index, end_index)
    current = None
    for i, line in enumerate(lines):
        if heading_re.match(line.rstrip()):
            heading = line.strip()
            if current is not None:
                sections[current][1] = i
            sections[heading] = [i + 1, len(lines)]
            current = heading

    for name in (*preferred_sections, "DESCRIPTION"):
        if name in sections:
            start, end = sections[name]
            return lines[start:end]

    return lines  # fall back to entire document


def _clean_description(raw_lines):
    """Join and normalise whitespace in a multi-line description."""
    return re.sub(r"\s+", " ", " ".join(raw_lines)).strip()


def parse_options(text):
    """
    Parse flag → description pairs from *text*.

    Returns an ordered dict whose keys are flag strings (e.g. "-a",
    "--all") and whose values are single-line descriptions.
    """
    lines = _section_lines(text, "OPTIONS")

    # A flag-entry line starts with 4+ spaces then a dash.
    flag_line_re = re.compile(r"^( {4,})(-\S.*)")

    options = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        m = flag_line_re.match(line)
        if not m:
            i += 1
            continue

        flag_indent = len(m.group(1))
        raw_header = m.group(2)

        flags, inline_desc = _parse_flag_header(raw_header)
        if not flags:
            i += 1
            continue

        # Collect description from subsequent more-indented lines
        i += 1
        desc_parts = []
        while i < len(lines):
            dl = lines[i]
            if not dl.strip():
                # blank line ends the description block
                i += 1
                break
            dl_indent = len(dl) - len(dl.lstrip())
            if dl_indent <= flag_indent:
                # Same or lesser indent → new option or section sub-header
                break
            desc_parts.append(dl.strip())
            i += 1

        # Prefer multi-line description; fall back to inline description
        description = _clean_description(desc_parts) or inline_desc
        if not description:
            continue

        for flag in flags:
            options[flag] = description

    return options


def _parse_flag_header(text):
    """
    Split a flag-entry header into (flags, inline_description).

    Handles forms like:
      "-a, --all"                     → (["-a", "--all"], "")
      "-I, --ignore=PATTERN"          → (["-I", "--ignore"], "")
      "--color[=WHEN]"                → (["--color"], "")
      "--help Output a usage message" → (["--help"], "Output a usage message")
      "-C     list entries by column" → (["-C"], "list entries by column")
      "-e PATTERNS, --regexp=PATTERNS"→ (["-e", "--regexp"], "")
    """
    flags = []
    pos = 0
    text = text.strip()

    while pos < len(text):
        # Skip commas and spaces (flag separators)
        while pos < len(text) and text[pos] in ", ":
            pos += 1

        if pos >= len(text):
            break

        if text[pos] == "-":
            # Match a flag token: -x, -1, --word[=ARG] or --word=ARG.
            # Digits are intentionally allowed as the first character to
            # support flags like ls -1.
            m = re.match(r"(-{1,2}[a-zA-Z0-9][a-zA-Z0-9_-]*)(?:[=\[][^\s,]*)?", text[pos:])
            if m:
                flags.append(m.group(1))
                pos += m.end()
                continue
            # Unrecognised dash pattern – stop here
            break

        # Not a flag start. Check if it's an all-caps argument placeholder
        # (e.g. PATTERNS in "-e PATTERNS, --regexp=PATTERNS").
        # These are uppercase-only words followed by a comma+flag or end of flags.
        m = re.match(r"[A-Z][A-Z0-9_]*(?=\s*(?:,\s*-|$))", text[pos:])
        if m:
            pos += m.end()
            continue

        # Anything else is the start of an inline description
        break

    inline_desc = text[pos:].strip().lstrip(",").strip()
    return flags, inline_desc


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} <command>", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if not re.match(r"^[a-zA-Z0-9._-]+$", command):
        raise SystemExit(
            f"Error: invalid command name '{command}'. "
            "Only letters, digits, '.', '_', and '-' are allowed."
        )

    print(f"Fetching man page for '{command}'…")
    man_text = get_man_page(command)

    options = parse_options(man_text)

    if not options:
        print(
            f"Warning: no options were extracted for '{command}'. "
            "The man page may use an unusual format.",
            file=sys.stderr,
        )

    data = {
        "command": command,
        "source": f"man {command}",
        "options": options,
    }

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(repo_root, "data", f"{command}.json")

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")

    print(f"Wrote {len(options)} options to {out_path}")

    commands_path = os.path.join(repo_root, "data", "commands.json")
    if os.path.exists(commands_path):
        with open(commands_path, encoding="utf-8") as fh:
            commands = json.load(fh)
    else:
        commands = []

    added = command not in commands
    commands = sorted(set(commands) | {command})
    with open(commands_path, "w", encoding="utf-8") as fh:
        fh.write("[\n")
        for i, cmd in enumerate(commands):
            suffix = "," if i < len(commands) - 1 else ""
            fh.write(f'  "{cmd}"{suffix}\n')
        fh.write("]\n")
    if added:
        print(f"Added '{command}' to {commands_path}")


if __name__ == "__main__":
    main()
