# Sigrex Flow Troubleshooting

Work from the source toward the exchange and stop at the first broken link.
Read-only checks first; changes only with approval.

## 1. Did the signal reach the Bot Webhook?

| Symptom | Likely cause | Check / fix |
| --- | --- | --- |
| Nothing in the signal log | Wrong URL (data hook instead of bot hook, typo, old hash) | Compare with the hook in `GET /webhook/bot/{id}` / dashboard |
| | Hook `INACTIVE` | `PUT /webhook/bot/{id}/status {"status":"ACTIVE"}` |
| | Key missing or wrong | Bot hooks need `"key"` in the JSON body (not a header) |
| | Invalid JSON (trailing comma, smart quotes, unescaped TradingView text) | Run `python3 scripts/validate_signal.py '<json>'`; test with curl |
| | Email signal not recognised | Body must contain only a valid payload JSON; non-signal mails are forwarded to the owner |
| Data Webhook rejects POST | Missing `X-Key` header or non-JSON body | Send `Content-Type: application/json` and `X-Key` |

## 2. Did a strategy or reaction emit the action?

| Symptom | Likely cause | Check / fix |
| --- | --- | --- |
| Strategy never acts | Status `INACTIVE` or suspended | `GET /strategy/code/{id}`; check last run time |
| | `send_signal` false, or no `webhook_id`/`symbol` | Update with the full body |
| | Suspended for a forbidden identifier or limit breach | Lint the live code with `python3 scripts/check_sandbox.py <file>`; check runtime and HTTP usage |
| | Entry condition never true | Read storage debug fields; evaluate conditions against current data |
| | Thinks a position is open (`lastTrigger` = `LONG`/`SHORT`) after test runs or manual closes | Reset triggers when the exchange is flat |
| | Second `EXIT` rejected | Exit only when `lastTrigger` is `LONG`/`SHORT` |
| | Flip attempted in one run | `EXIT` this run, open the other side on a later run |
| | `$.Price` undefined | `use_price` off; use `$.getExchangeRate` |
| | HTTP data missing | 1750 ms timeout, non-200 status, 5 s cache returning stale data |
| LLM Session never trades | `send_signal` false, or prompt rules never satisfied | Read stored responses; preview with `resolve_llm_session_prompt_template` |
| | Chart enabled with a text-only model | Session will not run; switch to a vision model or disable the chart |
| | Timeout (long tool chains) | Lower work per run; see the interval/timeout table |
| | Symbol not in the prompt | `signal_symbol` is not injected; name it in the prompt |
| Reaction silent | Data Webhook inactive, wrong `data_webhook_id`, `delay` throttling, invalid JSON | `GET /webhook/data/{id}/code-reactions?page=1&limit=50`; POST a test event |

## 3. Did a bot pick it up?

| Symptom | Likely cause | Check / fix |
| --- | --- | --- |
| Signal logged, no bot reaction | Bot `INACTIVE` | `GET /webhook/bot/bot/signal/{hookId}/cex?page=1&limit=50` lists bots and status |
| | Symbol mismatch (case, separator, `.P` suffix, trailing space) | Signal `symbol` must equal bot `symbol` exactly |
| | `TEST` flag still present | Remove it (with approval) |
| | `delay` / Frequency window dropped a burst | Space signals or adjust `delay` |
| | Prediction: slug or outcome mismatch | Exact slug (last URL segment) and exact outcome label |
| Only some bots executed | Others inactive, different symbols, or their keys failed | Check each bot and key |

## 4. Did the venue accept the order?

| Symptom | Likely cause | Check / fix |
| --- | --- | --- |
| CEX rejected | Below minimum notional | Raise `amount`/`size` above the pair minimum |
| | Insufficient balance or wrong wallet (spot vs futures) | Fund the right account; key for the right product |
| | API key revoked/expired or lacking trade permission | `POST /api/exchange/test`; recreate the key |
| | Close size wrong | Close `size` is base currency |
| | Futures settings (leverage, margin or position mode) | Check on the exchange |
| DEX swap failed or bot suspended | GasTank empty on that chain | Top up, then reactivate |
| | Bot token balance below fixed amount (Use All off) | Fund the contract or enable Use All |
| | `SwapFailed` event | Read the reason on the explorer (liquidity, route) |
| Prediction order failed | Session key expired (180 days), account not a Deposit Wallet, no USDC | Reconnect; fund the profile address |

## 5. API errors while building

| Code | Meaning | Action |
| --- | --- | --- |
| `401` | Signature or key problem | Path must include `/api/v2` and the query string; sign the exact body; timestamp in seconds |
| `400` | Missing/invalid field, invalid code, status already set | Compare the body with the endpoint reference in the `sigrex-api-mcp` skill |
| `402` | Plan limit (webhooks, bots, sessions, active resources) | Deactivate/delete something or upgrade; tell the user |
| `404` | Referenced ID does not exist (webhook, key, data hook, factory) | Re-list and use real IDs |
| `409` | Resource still in use | List dependants (bots on key/hook, reactions on data hook), detach first |

## 6. State drift checklist

After any manual intervention, make these agree before reactivating:

1. The exchange position (open or flat, side, size).
2. The strategy's `lastTrigger.action`.
3. The strategy's storage (entry price, flags).
4. The bot's status.

Reset triggers or storage only with approval, and only to match reality.
