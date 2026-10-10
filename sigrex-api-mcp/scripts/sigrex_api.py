#!/usr/bin/env python3
"""Sign and (optionally) send one Sigrex REST API request.

Dry run by default: prints the request with the API key and signature
redacted and sends nothing. Add --send to perform the request.

Credentials come from the environment, never from arguments:
  SIGREX_API_KEY     public API key   (header `api-key`)
  SIGREX_API_SECRET  private secret   (HMAC-SHA256 signing)
  SIGREX_API_BASE    optional base URL (default https://api.sigrex.io)

Signing contract (https://docs.sigrex.io/api-reference/reference/sigrex-api):
  GET / DELETE : METHOD + PATH + TIMESTAMP
  POST / PUT   : METHOD + PATH + BODY + TIMESTAMP
PATH is the full path including `/api/v2` and the query string (as the
official TypeScript client signs it). BODY is the exact JSON sent, serialised
like JavaScript's JSON.stringify (no spaces). A DELETE body is sent but not
signed. TIMESTAMP is Unix seconds. HMAC output is lowercase hex.

Requires Python 3.8+ (standard library only).
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = "https://api.sigrex.io"
# The API's edge blocks Python's default "Python-urllib/x.y" agent (HTTP 403, "error code: 1010").
USER_AGENT = "sigrex-skills/2.0 (+https://github.com/sigrexio/skills)"

EPILOG = """examples:
  scripts/sigrex_api.py GET /strategy/code
  scripts/sigrex_api.py GET /webhook/data/12/code-reactions --query page=1 --query limit=50
  scripts/sigrex_api.py PUT /bot/signal/cex/34/status --body '{"status":"INACTIVE"}'
  scripts/sigrex_api.py POST /webhook/bot --body-file hook.json --send
  scripts/sigrex_api.py GET /strategy/code --send --output codes.json

output (stdout, json by default):
  dry run: {"dry_run": true, "method", "url", "headers" (redacted), "body", "body_signed", "next"}
  sent:    {"dry_run": false, "method", "url", "status", "ok", "body"}
           large bodies: "truncated": true with "body_preview"; use --output FILE for the full body
  diagnostics go to stderr

exit codes:
  0  dry run printed, or the API answered 2xx
  1  the API answered with a non-2xx status (see "status" and "body")
  2  usage error (bad arguments, invalid JSON body, unreadable file)
  3  --send without SIGREX_API_KEY / SIGREX_API_SECRET in the environment
  4  network error (no response from the API)
"""


def js_normalize(value):
    """Make Python's JSON output match JSON.stringify for typical bodies."""
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("NaN/Infinity cannot be sent as JSON")
        return int(value) if value.is_integer() else value
    if isinstance(value, dict):
        return {k: js_normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [js_normalize(v) for v in value]
    return value


def build_request(method, path, query, body, timestamp, secret):
    """Return (signed_path, body_text, message, signature)."""
    method = method.upper()
    if not path.startswith("/"):
        path = "/" + path
    if not path.startswith("/api/v2/"):
        path = "/api/v2" + path
    query_string = urllib.parse.urlencode(query) if query else ""
    signed_path = path + ("?" + query_string if query_string else "")

    body_text = ""
    if body is not None:
        body_text = json.dumps(js_normalize(body), separators=(",", ":"), ensure_ascii=False)
    signed_body = body_text if method in ("POST", "PUT") else ""

    message = method + signed_path + signed_body + timestamp
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return signed_path, body_text, message, signature


def redact(value, keep=4):
    if not value:
        return "<unset>"
    return value[:keep] + "…" if len(value) > keep else "…"


def emit(data, fmt):
    if fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return
    print(f"{data['method']} {data['url']}")
    if data["dry_run"]:
        for name, value in data["headers"].items():
            print(f"  {name}: {value}")
        if data.get("body"):
            print(f"  body: {data['body']}" + ("" if data["body_signed"] else "  (not signed)"))
        print(f"\n{data['next']}")
        return
    print(f"HTTP {data['status']}")
    if data.get("saved_to"):
        print(f"Full body ({data['body_chars']} chars) saved to {data['saved_to']}")
    elif data.get("truncated"):
        print(data["body_preview"])
        print(f"... truncated at {len(data['body_preview'])} of {data['body_chars']} chars; use --output FILE")
    else:
        body = data["body"]
        print(json.dumps(body, indent=2, ensure_ascii=False) if not isinstance(body, str) else body)


def main(argv):
    parser = argparse.ArgumentParser(
        prog="sigrex_api.py", description="Sign and (optionally) send one Sigrex REST API request. "
        "Dry run unless --send.", epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("method", type=str.upper, choices=["GET", "POST", "PUT", "DELETE"])
    parser.add_argument("path", help="API path, with or without the /api/v2 prefix, e.g. /strategy/code")
    parser.add_argument("--query", action="append", default=[], metavar="KEY=VALUE",
                        help="query parameter (repeatable, order is preserved)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--body", metavar="JSON", help="JSON request body")
    group.add_argument("--body-file", metavar="FILE", help="read the JSON request body from FILE")
    parser.add_argument("--send", action="store_true", help="actually send the request (default: dry run)")
    parser.add_argument("--output", metavar="FILE", help="write the full response body to FILE")
    parser.add_argument("--max-chars", type=int, default=20000,
                        help="truncate the printed response body beyond this many chars (default: 20000)")
    parser.add_argument("--timeout", type=float, default=30.0, help="request timeout in seconds (default: 30)")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="output format (default: json)")
    args = parser.parse_args(argv)

    query = []
    for item in args.query:
        if "=" not in item:
            parser.error(f"--query expects KEY=VALUE, got {item!r}")
        query.append(tuple(item.split("=", 1)))

    try:
        if args.body is not None:
            body = json.loads(args.body)
        elif args.body_file:
            with open(args.body_file, encoding="utf-8") as handle:
                body = json.load(handle)
        else:
            body = {} if args.method in ("POST", "PUT") else None
    except OSError as error:
        print(f"Error: cannot read {args.body_file}: {error.strerror}", file=sys.stderr)
        return 2
    except ValueError as error:
        print(f"Error: request body is not valid JSON: {error}. Example: --body '{{\"status\":\"INACTIVE\"}}'",
              file=sys.stderr)
        return 2

    api_key = os.environ.get("SIGREX_API_KEY", "")
    secret = os.environ.get("SIGREX_API_SECRET", "")
    if args.send and (not api_key or not secret):
        print("Error: --send needs SIGREX_API_KEY and SIGREX_API_SECRET in the environment. "
              "Create a key under API Management in the Sigrex dashboard.", file=sys.stderr)
        return 3

    timestamp = str(int(time.time()))
    try:
        signed_path, body_text, message, signature = build_request(
            args.method, args.path, query, body, timestamp, secret or "dry-run-secret")
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    base = os.environ.get("SIGREX_API_BASE", DEFAULT_BASE).rstrip("/")
    url = base + signed_path
    body_signed = bool(body_text) and args.method in ("POST", "PUT")

    if not args.send:
        emit({
            "dry_run": True, "method": args.method, "url": url,
            "headers": {"api-key": redact(api_key), "timestamp": timestamp, "signature": redact(signature, 8)},
            "body": body_text or None, "body_signed": body_signed,
            "next": "Dry run only. Re-run with --send after the user approves this request.",
        }, args.format)
        return 0

    if args.method != "GET":
        print(f"Sending a mutating {args.method} request to {url}", file=sys.stderr)
    headers = {"api-key": api_key, "timestamp": timestamp, "signature": signature, "User-Agent": USER_AGENT}
    data = None
    if body_text:
        headers["Content-Type"] = "application/json"
        data = body_text.encode("utf-8")
    request = urllib.request.Request(url, data=data, method=args.method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read()
    except (urllib.error.URLError, TimeoutError) as error:
        reason = getattr(error, "reason", error)
        print(f"Error: no response from {base}: {reason}. Check network access and SIGREX_API_BASE.",
              file=sys.stderr)
        return 4

    text = raw.decode("utf-8", errors="replace")
    result = {"dry_run": False, "method": args.method, "url": url, "status": status,
              "ok": 200 <= status < 300, "body_chars": len(text)}
    if status == 403 and "1010" in text:
        print("Hint: 403 'error code: 1010' is the API edge rejecting the client's User-Agent, "
              "not a Sigrex auth error.", file=sys.stderr)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(text)
        except OSError as error:
            print(f"Error: cannot write {args.output}: {error.strerror}", file=sys.stderr)
            return 2
        result["saved_to"] = args.output
    elif len(text) > args.max_chars:
        result["truncated"] = True
        result["body_preview"] = text[:args.max_chars]
        print(f"Response body is {len(text)} chars; printed the first {args.max_chars}. "
              "Use --output FILE for the full body.", file=sys.stderr)
    else:
        try:
            result["body"] = json.loads(text) if text else None
        except ValueError:
            result["body"] = text
    emit(result, args.format)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
