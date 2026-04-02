# parse-man.py

A command-line tool that parses a command's man page and generates a
`data/<command>.json` file for use with **what-the-shell**.

## Dependencies

The script requires only **Python 3** (3.6+) and the standard `man` utility,
both of which are pre-installed on virtually every Linux and macOS system.

No third-party Python packages are needed.

### Verify your environment

```bash
python3 --version   # should print Python 3.6 or later
man --version       # should print a version string without error
```

If `man` is not installed, install it with your system package manager:

| OS / distro | Install command |
|---|---|
| Debian / Ubuntu | `sudo apt-get install man-db` |
| Fedora / RHEL | `sudo dnf install man-db` |
| macOS (Homebrew) | built-in; or `brew install man-db` |

## Usage

Run the script from the repository root, passing the name of the command you
want to document:

```bash
python3 tools/parse-man.py <command>
```

The script will:

1. Fetch the plain-text man page for `<command>`.
2. Parse the `OPTIONS` (or `DESCRIPTION`) section for flag entries.
3. Write the result to `data/<command>.json`.

### Examples

Generate a data file for `grep`:

```bash
python3 tools/parse-man.py grep
# Fetching man page for 'grep'…
# Wrote 84 options to /path/to/repo/data/grep.json
```

Generate a data file for `find`:

```bash
python3 tools/parse-man.py find
```

### Output format

The generated file follows the schema used by every other file in `data/`:

```json
{
  "command": "grep",
  "source": "man grep",
  "options": {
    "-E": "Interpret PATTERNS as extended regular expressions (EREs).",
    "--extended-regexp": "Interpret PATTERNS as extended regular expressions (EREs).",
    "-i": "Ignore case distinctions in patterns and input data.",
    "--ignore-case": "Ignore case distinctions in patterns and input data."
  }
}
```

## Notes

- The script overwrites an existing `data/<command>.json` without prompting.
- If the man page has no recognisable `OPTIONS` section the script falls back
  to the `DESCRIPTION` section (common for GNU coreutils such as `ls`).
- A warning is printed to stderr if no options could be extracted, which
  usually means the man page uses an unusual format.
- After generating the file, add the command to the `COMMANDS_WITH_DATA` set
  in `index.html` so the web app loads its flag data.
