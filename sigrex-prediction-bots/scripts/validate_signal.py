#!/usr/bin/env python3
"""Validate a Sigrex Bot Webhook signal payload before sending it.

Checks a CEX/DEX signal (default) or a Prediction signal (--prediction)
against the published schemas. The `key` value is redacted in all output.

Sources:
  https://docs.sigrex.io/getting-started/signal-payload-format.md
  https://docs.sigrex.io/prediction-signal-bot-beta/payload-format.md
Requires Python 3.8+ (standard library only).
"""

import argparse
import json
import sys
from urllib.parse import urlparse

EPILOG = """examples:
  scripts/validate_signal.py '{"symbol":"BTCUSDT","side":"BUY","flag":"TEST"}'
  scripts/validate_signal.py --file payload.json --expect-key
  scripts/validate_signal.py --prediction '{"slug":"some-market","outcome":"Yes","side":"BUY"}'
  scripts/validate_signal.py --format text --file payload.json

output:
  json (default): {"valid": bool, "mode": "signal"|"prediction", "errors": [...],
                   "warnings": [...], "payload": {...key redacted...}}
  text: the redacted payload, then ERROR/WARN lines and RESULT VALID|INVALID

exit codes:
  0  payload is valid (warnings may exist)
  1  payload is invalid (including malformed JSON)
  2  usage error (missing payload, unreadable file)
"""

SIGNAL_FIELDS = {"id", "key", "symbol", "side", "size", "forceSize", "dilution", "flag", "debug", "callback"}
PREDICTION_FIELDS = {"id", "key", "slug", "outcome", "side", "size", "forceSize", "dilution", "debug", "callback"}
FLAGS = {"TEST", "DEBUG", "REVERSE"}


def check(payload, prediction, expect_key):
    errors, warnings = [], []
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"], []

    allowed = PREDICTION_FIELDS if prediction else SIGNAL_FIELDS
    for field in payload:
        if field not in allowed:
            if prediction and field in ("symbol", "flag"):
                errors.append(f"`{field}` is not part of the prediction payload; "
                              + ("use `slug` + `outcome`" if field == "symbol" else
                                 "prediction bots have no documented TEST flag, test with the smallest size"))
            elif not prediction and field in ("slug", "outcome"):
                errors.append(f"`{field}` belongs to prediction payloads; CEX/DEX bots need `symbol`")
            else:
                warnings.append(f"unknown field `{field}` will be ignored or rejected")

    side = payload.get("side")
    if side is None:
        errors.append("`side` is required")
    elif not isinstance(side, str) or side.upper() not in ("BUY", "SELL"):
        errors.append("`side` must be BUY or SELL")
    elif side != side.upper():
        warnings.append("`side` is accepted in lowercase, but uppercase BUY/SELL is clearer")

    if prediction:
        for field in ("slug", "outcome"):
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"`{field}` is required and must be a non-empty string")
        slug = payload.get("slug")
        if isinstance(slug, str) and ("/" in slug or slug.startswith("http")):
            errors.append("`slug` must be the bare market slug, not a URL or path")
        outcome = payload.get("outcome")
        if isinstance(outcome, str) and outcome != outcome.strip():
            errors.append("`outcome` has surrounding whitespace; it must match the market outcome exactly")
    else:
        symbol = payload.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip():
            errors.append("`symbol` is required and must be a non-empty string")
        elif symbol != symbol.strip():
            errors.append("`symbol` has surrounding whitespace; it must equal the bot's symbol exactly")

    if "size" in payload:
        size = payload["size"]
        if isinstance(size, bool) or not isinstance(size, (int, float)):
            errors.append("`size` must be a number (send 12.5, not \"12.5\")")
        elif size <= 0:
            errors.append("`size` must be greater than 0")
        elif not prediction:
            warnings.append("`size` units: quote currency when opening, base currency when closing")

    for field in ("dilution", "forceSize"):
        if field in payload and not isinstance(payload[field], bool):
            errors.append(f"`{field}` must be true or false (boolean, not a string)")

    if not prediction:
        flags = payload.get("flag", [])
        values = flags if isinstance(flags, list) else [flags]
        for value in values:
            if not isinstance(value, str) or value not in FLAGS:
                errors.append(f"`flag` values must be TEST, DEBUG or REVERSE (got {value!r})")
        if "TEST" not in values:
            warnings.append("no TEST flag: this signal can place a real order")

    if "id" in payload and not isinstance(payload["id"], str):
        errors.append("`id` must be a string")

    if "key" in payload:
        if not isinstance(payload["key"], str) or not payload["key"]:
            errors.append("`key` must be a non-empty string")
    elif expect_key:
        errors.append("webhook is key-protected but `key` is missing; the signal will be rejected")

    if "callback" in payload:
        url = payload["callback"]
        parsed = urlparse(url) if isinstance(url, str) else None
        if not parsed or parsed.scheme not in ("http", "https") or not parsed.netloc:
            errors.append("`callback` must be an absolute http(s) URL")
        else:
            if parsed.scheme != "https":
                warnings.append("`callback` is not HTTPS")
            if "key" in payload:
                warnings.append("the callback receives the original signal, including `key`; "
                                "only use a callback URL you control")
    return errors, warnings


def redacted(payload):
    if not isinstance(payload, dict):
        return payload
    shown = dict(payload)
    if isinstance(shown.get("key"), str):
        shown["key"] = shown["key"][:4] + "…"
    return shown


def main(argv):
    parser = argparse.ArgumentParser(
        prog="validate_signal.py", description=__doc__.split("\n\n")[0],
        epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("payload", nargs="?", help="payload JSON string")
    parser.add_argument("--file", help="read the payload JSON from FILE ('-' for stdin)")
    parser.add_argument("--prediction", action="store_true", help="validate a Prediction bot payload")
    parser.add_argument("--expect-key", action="store_true", help="the target webhook is key-protected")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                        help="output format (default: json)")
    args = parser.parse_args(argv)

    if args.payload is not None and args.file:
        parser.error("pass either a payload string or --file, not both")
    try:
        if args.file == "-":
            raw = sys.stdin.read()
        elif args.file:
            with open(args.file, encoding="utf-8") as handle:
                raw = handle.read()
        elif args.payload is not None:
            raw = args.payload
        else:
            parser.error("missing payload: pass a JSON string or --file FILE")
    except OSError as error:
        print(f"Error: cannot read {args.file}: {error.strerror}", file=sys.stderr)
        return 2

    mode = "prediction" if args.prediction else "signal"
    try:
        payload = json.loads(raw)
    except ValueError as error:
        payload, errors, warnings = None, [f"invalid JSON: {error}"], []
    else:
        errors, warnings = check(payload, args.prediction, args.expect_key)

    if args.format == "json":
        print(json.dumps({"valid": not errors, "mode": mode, "errors": errors,
                          "warnings": warnings, "payload": redacted(payload)}, indent=2, ensure_ascii=False))
    else:
        if payload is not None:
            print(json.dumps(redacted(payload), indent=2, ensure_ascii=False))
        for message in errors:
            print(f"ERROR {message}")
        for message in warnings:
            print(f"WARN  {message}")
        print("RESULT", "INVALID" if errors else "VALID")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
