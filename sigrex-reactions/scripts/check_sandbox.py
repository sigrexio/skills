#!/usr/bin/env python3
"""Lint Sigrex Code Strategy / Code Reaction source before uploading it.

The Sigrex sandbox rejects code that contains a forbidden identifier anywhere
in the source, including comments, and may suspend the strategy. This checker
scans the raw text (code, comments and strings) and reports:

  error    an exact, case-sensitive forbidden identifier (e.g. `close`, `fetch`)
  warning  a case variant or camelCase prefix (e.g. `Close`, `closePrice`);
           the exact matching rule is not published, so rename these too
  warning  more than one $.Strategy.action call, $.Price use, missing awaits

Source of the identifier list: https://docs.sigrex.io/startegies/code.md
Requires Python 3.8+ (standard library only).
"""

import argparse
import json
import re
import sys

EPILOG = """examples:
  scripts/check_sandbox.py strategy.js
  scripts/check_sandbox.py --format text strategy.js reaction.js
  cat strategy.js | scripts/check_sandbox.py -

output:
  json (default): {"ok": bool, "files": [{"file", "ok", "errors": [...], "warnings": [...]}]}
  text: one "file:line:col: ERROR|WARN message" line per finding

exit codes:
  0  no forbidden identifiers (warnings may exist)
  1  at least one forbidden identifier found
  2  usage error (bad arguments or unreadable file)
"""

FORBIDDEN = {
    "Networking & communication": [
        "fetch", "WebSocket", "EventSource", "Worker", "SharedWorker", "XMLHttpRequest",
        "navigator", "location", "postMessage", "onmessage", "onmessageerror",
        "MessageChannel", "BroadcastChannel", "import", "importScripts", "close",
    ],
    "Dynamic code execution": ["eval", "Function", "AsyncFunction", "generatorFunction", "constructor"],
    "Global objects": ["globalThis", "window", "self", "frames", "parent", "top", "document"],
    "Timers": ["setTimeout", "setInterval", "setImmediate", "clearTimeout", "clearInterval",
               "clearImmediate", "queueMicrotask"],
    "Crypto, performance & parallelism": ["crypto", "performance", "structuredClone", "Atomics",
                                           "SharedArrayBuffer"],
    "Reflection": ["Reflect", "Proxy"],
    "Node.js / Deno": ["process", "require", "module", "exports", "export", "global", "Deno"],
    "Encoding": ["atob", "btoa"],
    "Interaction & debugging": ["alert", "confirm", "prompt", "console", "Intl",
                                "FinalizationRegistry", "WeakRef"],
}

WORD_TO_GROUP = {w: g for g, words in FORBIDDEN.items() for w in words}
LOWER_TO_WORD = {w.lower(): w for w in WORD_TO_GROUP}
IDENT = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
ASYNC_CALL = re.compile(
    r"(?<!await )(?<!await\s)\$\.(Strategy\.action|Storage\.(?:get|set)|Http\.(?!createApiClient)\w+|getExchangeRate)\s*\(")

SUGGEST = {
    "close": "use a name like lastPx / exitPos; read kline index 4 instead of a .close key",
    "fetch": "use $.Http.get / $.Http.post",
    "console": "write debug values into $.Storage instead",
    "alert": "use a word like notice / signalMsg",
    "top": "use a word like highest / upper",
    "self": "use a word like own / me",
    "parent": "use a word like owner / root",
    "prompt": "use a word like instruction / text",
    "global": "use a word like shared / allScope",
    "module": "use a word like part / unit",
    "constructor": "avoid `class` bodies; use plain objects and arrow functions",
    "crypto": "use a word like coin / asset",
    "performance": "use a word like pnl / result",
    "process": "use a word like handle / run",
    "import": "inline the logic; modules cannot be loaded",
    "export": "nothing can be exported; just write top-level code",
    "location": "use a word like place / venue",
}


def scan(text):
    errors, warnings = [], []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in IDENT.finditer(line):
            token, col = match.group(0), match.start() + 1
            if token in WORD_TO_GROUP:
                errors.append({
                    "line": lineno, "column": col, "identifier": token,
                    "category": WORD_TO_GROUP[token],
                    "hint": SUGGEST.get(token, "rename or remove it (comments and strings included)"),
                })
                continue
            lower = token.lower()
            if lower in LOWER_TO_WORD:
                warnings.append({"line": lineno, "column": col, "message":
                                 f"`{token}` is a case variant of the forbidden `{LOWER_TO_WORD[lower]}`; "
                                 "rename to be safe"})
                continue
            prefix = re.match(r"([a-z]+)(?=[A-Z0-9_])", token)
            if prefix and prefix.group(1) in WORD_TO_GROUP:
                warnings.append({"line": lineno, "column": col, "message":
                                 f"`{token}` starts with the forbidden `{prefix.group(1)}`; "
                                 "matching rules are unpublished, rename to be safe"})

    actions = len(re.findall(r"\$\.Strategy\.action\s*\(", text))
    if actions > 1:
        warnings.append({"line": None, "column": None, "message":
                         f"{actions} `$.Strategy.action` calls; only one action may run per execution, "
                         "so make the branches mutually exclusive"})
    for call in ASYNC_CALL.finditer(text):
        lineno = text.count("\n", 0, call.start()) + 1
        warnings.append({"line": lineno, "column": None, "message":
                         f"`$.{call.group(1)}(...)` is async; add `await`"})
    if re.search(r"\$\.Price\b", text):
        warnings.append({"line": None, "column": None, "message":
                         "`$.Price` is deprecated and only set when `use_price` is enabled; prefer "
                         "`await $.getExchangeRate($.Exchange.BINANCE, \"btcusdt\")`"})
    return errors, warnings


def print_text(results):
    for result in results:
        name = result["file"]
        for err in result["errors"]:
            print(f"{name}:{err['line']}:{err['column']}: ERROR `{err['identifier']}` is forbidden "
                  f"({err['category']}); {err['hint']}")
        for warn in result["warnings"]:
            where = f"{name}:{warn['line']}" if warn["line"] else name
            if warn["column"]:
                where += f":{warn['column']}"
            print(f"{where}: WARN {warn['message']}")
        status = "OK" if result["ok"] else "FAIL"
        print(f"{name}: {status} ({len(result['errors'])} errors, {len(result['warnings'])} warnings)")


def main(argv):
    parser = argparse.ArgumentParser(
        prog="check_sandbox.py", description=__doc__.split("\n\n")[0],
        epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+", metavar="FILE", help="JavaScript file(s) to lint; '-' reads stdin")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                        help="output format (default: json)")
    args = parser.parse_args(argv)

    results = []
    for path in args.files:
        try:
            if path == "-":
                name, text = "<stdin>", sys.stdin.read()
            else:
                name = path
                with open(path, encoding="utf-8") as handle:
                    text = handle.read()
        except OSError as error:
            print(f"Error: cannot read {path}: {error.strerror}. Pass a readable .js file or '-' for stdin.",
                  file=sys.stderr)
            return 2
        errors, warnings = scan(text)
        results.append({"file": name, "ok": not errors, "errors": errors, "warnings": warnings})

    all_ok = all(result["ok"] for result in results)
    if args.format == "json":
        print(json.dumps({"ok": all_ok, "files": results}, indent=2))
    else:
        print_text(results)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
