#!/usr/bin/env python3
"""Lint Sigrex Code Strategy / Code Reaction source before uploading it.

The Sigrex sandbox rejects code that contains a forbidden identifier anywhere
in the source, including comments, and may suspend the strategy. On create and
update the API also checks the code rules (see SKILL.md, Code Rules) and
answers 400 when one is broken. This checker reports:

  error    an exact, case-sensitive forbidden identifier (e.g. `close`, `fetch`),
           scanned in the raw text (code, comments and strings)
  error    a broken code rule, scanned in the code without comments and strings:
           a loop whose condition is always true or missing, a change to a
           built-in or $.Ta, RegExp, prototype access, arguments, with,
           debugger, a size over 1,000,000, a loop bound over 10,000,000, a
           regular expression with nested quantifiers, code over 100,000 chars
  warning  a case variant or camelCase prefix (e.g. `Close`, `closePrice`);
           the exact matching rule is not published, so rename these too
  warning  likely rule breaks this script can't confirm without a parser: an
           assignment to a name never declared, `this` outside a class
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
  0  no forbidden identifiers or broken code rules (warnings may exist)
  1  at least one forbidden identifier or broken code rule found
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

# Code rules (same limits as the API)
MAX_CODE_LENGTH = 100_000
MAX_SIZE = 1_000_000          # Array(n), typed arrays, Array.from({length: n}), repeat/padStart/padEnd(n)
MAX_LOOP_BOUND = 10_000_000   # constant a loop condition may compare against

BUILTINS = ("Object|Array|String|Number|Boolean|Symbol|BigInt|Math|JSON|Date|Promise|Map|Set|WeakMap|WeakSet|"
            "Error|TypeError|RangeError|parseInt|parseFloat|isNaN|isFinite|URL|URLSearchParams")
TYPED_ARRAYS = ("(?:Int8|Uint8|Uint8Clamped|Int16|Uint16|Int32|Uint32|Float16|Float32|Float64|BigInt64|BigUint64)"
                "Array")
NUMBER = r"(?:0[xX][0-9a-fA-F_]+|\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?)"
# a number, optionally combined with one more: `1e9`, `2 ** 30`, `1 << 30`, `1e5 * 1e5`
NUMBER_EXPR = rf"({NUMBER})(?:\s*(\*\*|\*|<<)\s*({NUMBER}))?"
COMPARISON = r"(?:<=?|>=?|!==?)"

RULES = [
    (re.compile(rf"(?<![\w$.])(?:{BUILTINS})(?:\s*\.\s*[\w$]+|\s*\[[^\]]*\])*\s*(?:\*\*|<<|>>>?|&&|\|\||\?\?|[-+*/%&|^])?=(?!=)"),
     "assignment to a built-in", "built-ins are read-only; keep helpers in your own object"),
    (re.compile(rf"(?<![\w$.])delete\s+(?:{BUILTINS})\b"), "`delete` on a built-in", "built-ins are read-only"),
    (re.compile(rf"\bObject\s*\.\s*assign\s*\(\s*(?:(?:{BUILTINS})\b|\$\s*\.\s*Ta\b)"), "`Object.assign` into a built-in",
     "assign into your own object, e.g. `Object.assign({}, a, b)`"),
    (re.compile(r"\$\s*\.\s*Ta(?:\s*\.\s*[\w$]+|\s*\[[^\]]*\])+\s*(?:\*\*|[-+*/%])?=(?!=)"), "assignment into `$.Ta`",
     "`$.Ta` is read-only; create instances instead, e.g. `new $.Ta.RSI(14)`"),
    (re.compile(r"(?<![\w$.])RegExp\b"), "`RegExp` is not allowed", "use a regular expression literal such as `/btc/i`"),
    (re.compile(r"\.\s*prototype\b|__proto__"), "prototype access is not allowed",
     "use `Object.hasOwn(obj, key)` and plain objects"),
    (re.compile(r"(?<![\w$.])arguments\b"), "`arguments` is not allowed", "use rest parameters: `(...args) => args.length`"),
    (re.compile(r"(?<![\w$.])with\s*\("), "`with` statements are not allowed", "reference the object explicitly"),
    (re.compile(r"(?<![\w$.])debugger\b"), "`debugger` is not allowed", "remove it; store debug values in $.Storage"),
]

SIZE_PATTERNS = [
    re.compile(rf"(?<![\w$.])Array\s*\(\s*{NUMBER_EXPR}\s*\)"),
    re.compile(rf"(?<![\w$.]){TYPED_ARRAYS}\s*\(\s*{NUMBER_EXPR}"),
    re.compile(rf"\.\s*(?:repeat|padStart|padEnd)\s*\(\s*{NUMBER_EXPR}"),
    re.compile(rf"\bArray\s*\.\s*from\s*\(\s*\{{\s*length\s*:\s*{NUMBER_EXPR}"),
    re.compile(rf"\.\s*length\s*=(?!=)\s*{NUMBER_EXPR}"),
]

# regular expression literal: after an operator, an opening bracket or `return`
REGEX_LITERAL = re.compile(r"(?:^|[(,=:\[!&|?{};]|\breturn)\s*(/(?![/*])((?:\\.|\[(?:\\.|[^\]\\\n])*\]|[^/\\\n\[])+)/[dgimsuyv]*)",
                           re.MULTILINE)


def strip_comments_and_strings(text):
    """Blank out comments and the contents of string/template literals, keeping line numbers and columns."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        char, nxt = text[i], text[i + 1] if i + 1 < n else ""
        if char == "/" and nxt == "/":
            while i < n and text[i] != "\n":
                out[i] = " "
                i += 1
        elif char == "/" and nxt == "*":
            end = text.find("*/", i + 2)
            end = n if end == -1 else end + 2
            for j in range(i, end):
                if text[j] != "\n":
                    out[j] = " "
            i = end
        elif char in "'\"`":
            quote, i = char, i + 1
            while i < n and text[i] != quote:
                if text[i] == "\\":
                    out[i] = " "
                    i += 1
                if i < n and text[i] != "\n":
                    out[i] = " "
                i += 1
            i += 1
        else:
            i += 1
    return "".join(out)


def number_value(match):
    """Value of a NUMBER_EXPR match (groups: first number, operator, second number)."""
    def parse(raw):
        raw = raw.replace("_", "")
        return int(raw, 16) if raw[:2].lower() == "0x" else float(raw)

    try:
        value = parse(match[0])
        if match[1] and match[2]:
            other = parse(match[2])
            value = value ** min(other, 400) if match[1] == "**" else value * other if match[1] == "*" else value * 2 ** min(other, 400)
        return value
    except (ValueError, OverflowError):
        return float("inf")


def has_nested_quantifier(pattern):
    """A quantified group that contains a quantifier, e.g. (a+)+ or (x*)*."""
    groups, in_class, i = [], False, 0

    def variable_quantifier_at(index):
        return index < len(pattern) and (pattern[index] in "*+" or re.match(r"\{\d+,\d*\}", pattern[index:]) is not None)

    while i < len(pattern):
        char = pattern[i]
        if char == "\\":
            i += 2
            continue
        if in_class:
            in_class = char != "]"
        elif char == "[":
            in_class = True
        elif char == "(":
            groups.append(False)
        elif char == ")":
            contains = groups.pop() if groups else False
            if contains and variable_quantifier_at(i + 1):
                return True
            if contains and groups:
                groups[-1] = True
        elif groups and variable_quantifier_at(i):
            groups[-1] = True
        i += 1
    return False


def balanced(code, start):
    """Text between the parenthesis at `start` and its matching closing one."""
    depth = 0
    for index in range(start, len(code)):
        if code[index] == "(":
            depth += 1
        elif code[index] == ")":
            depth -= 1
            if depth == 0:
                return code[start + 1:index]
    return code[start + 1:]


def loop_conditions(code):
    """(position, condition) of every `while (...)` and `for (...; condition; ...)`; None = no condition."""
    for match in re.finditer(r"(?<![\w$.])(while|for)\s*(?:await\s*)?\(", code):
        inside = balanced(code, match.end() - 1)
        if match.group(1) == "while":
            yield match.start(), inside
            continue
        parts = inside.split(";")
        if len(parts) >= 3:  # not for...of / for...in
            yield match.start(), parts[1].strip() or None


def position(text, index):
    line = text.count("\n", 0, index) + 1
    return line, index - (text.rfind("\n", 0, index) + 1) + 1


def check_rules(text):
    errors, warnings = [], []

    def error(index, message, hint):
        line, column = position(text, index)
        errors.append({"line": line, "column": column, "rule": message, "hint": hint})

    if len(text) > MAX_CODE_LENGTH:
        errors.append({"line": None, "column": None, "rule": f"code is longer than {MAX_CODE_LENGTH:,} characters",
                       "hint": "remove unused code and long comments"})

    code = strip_comments_and_strings(text)

    for pattern, message, hint in RULES:
        for match in pattern.finditer(code):
            # `const Map = ...` declares a local, it doesn't change the built-in
            if not re.search(r"(?<![\w$.])(?:let|const|var)\s+$", code[max(0, match.start() - 12):match.start()]):
                error(match.start(), message, hint)

    for pattern in SIZE_PATTERNS:
        for match in pattern.finditer(code):
            if number_value(match.groups()[-3:]) > MAX_SIZE:
                error(match.start(), f"size over {MAX_SIZE:,}", "keep arrays and strings small, e.g. `.slice(-500)`")

    for index, condition in loop_conditions(code):
        if condition is None or re.fullmatch(r"\s*(?:true|1|!0|!false|!!1)\s*", condition):
            error(index, "loop condition is always true or missing",
                  "give the loop a condition that becomes false, e.g. `for (let i = 0; i < xs.length; i++)`")
            continue
        for match in re.finditer(rf"{COMPARISON}\s*-?\s*{NUMBER_EXPR}|{NUMBER_EXPR}\s*{COMPARISON}", condition):
            value = number_value(match.groups()[:3]) if match.group(1) else number_value(match.groups()[3:])
            if abs(value) > MAX_LOOP_BOUND:
                error(index, f"loop bound over {MAX_LOOP_BOUND:,}", "loop over your data, e.g. `i < prices.length`")
                break

    for match in REGEX_LITERAL.finditer(code):
        literal_start = match.start(1)
        body = text[literal_start + 1:literal_start + 1 + len(match.group(2))]
        if has_nested_quantifier(body):
            error(literal_start, "regular expression with nested quantifiers",
                  "rewrite without a quantified group that contains a quantifier, e.g. `/a+$/` instead of `/(a+)+$/`")

    if re.search(r"(?<![\w$.])this\b", code) and not re.search(r"(?<![\w$.])class\b", code):
        line, column = position(text, re.search(r"(?<![\w$.])this\b", code).start())
        warnings.append({"line": line, "column": column, "message":
                         "`this` is only allowed inside class methods; use plain objects and functions"})

    declared = {"$"}
    for match in re.finditer(r"(?<![\w$.])(?:let|const|var)\s+([^;\n]+)", code):
        declared.update(re.findall(r"([A-Za-z_$][\w$]*)\s*(?==|,|;|\}|\]|:|$)", match.group(1)))
        declared.update(re.findall(r"^([A-Za-z_$][\w$]*)", match.group(1)))
    for match in re.finditer(r"(?<![\w$.])(?:let|const|var)\s*[\[{]([^=;]*)", code):
        declared.update(IDENT.findall(match.group(1)))
    for match in re.finditer(r"(?<![\w$.])(?:function\s*\*?|class)\s*([\w$]*)\s*(?:\(([^)]*)\))?", code):
        declared.add(match.group(1))
        declared.update(IDENT.findall(match.group(2) or ""))
    for match in re.finditer(r"\(([^()]*)\)\s*(?:=>|\{)|([A-Za-z_$][\w$]*)\s*=>|catch\s*\(([^)]*)\)", code):
        declared.update(IDENT.findall(" ".join(group or "" for group in match.groups())))
    for match in re.finditer(r"(?:^|[;{}(,\n])\s*([A-Za-z_$][\w$]*)\s*=(?![=>])", code, re.MULTILINE):
        name = match.group(1)
        if name not in declared and name not in WORD_TO_GROUP:
            line, column = position(text, match.start(1))
            warnings.append({"line": line, "column": column, "message":
                             f"`{name}` is assigned but never declared; the API rejects that, "
                             f"declare it with `let {name}` or `const {name}`"})
            declared.add(name)

    return errors, warnings


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

    rule_errors, rule_warnings = check_rules(text)
    errors.extend(rule_errors)
    warnings.extend(rule_warnings)

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
            where = f"{name}:{err['line']}:{err['column']}" if err["line"] else name
            if "rule" in err:
                print(f"{where}: ERROR {err['rule']}; {err['hint']}")
            else:
                print(f"{where}: ERROR `{err['identifier']}` is forbidden ({err['category']}); {err['hint']}")
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
