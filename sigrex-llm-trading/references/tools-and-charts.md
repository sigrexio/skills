# LLM Tools, Chart Options And Enums

Reference for LLM Sessions and LLM Reactions. Source:
https://docs.sigrex.io/startegies/llm-session/signal-generation.md,
https://docs.sigrex.io/startegies/llm-session/chart-setup.md, the API
reference and the changelog.

## Tool Reference

The model receives these tools when Signal Generation (`send_signal`) is
enabled. Tool argument schemas are not published; the model sees them at
runtime.

| Tool | What it does | Notes |
| --- | --- | --- |
| `open_position` | Opens a BUY (long) or SELL (short) position on one or more of the session's signal symbols | Sent to the configured Bot Webhook as a live signal. Only one position at a time per session |
| `close_position` | Closes the active position | Use for take-profit, stop-loss, invalidation |
| `get_symbol_price` | Current price of a pair | Up to 20 pairs per call |
| `get_candlestick_data` | Historical OHLCV for a symbol and timeframe, with optional time range or candle limit | Preferred source for TA inside sessions |
| `set_storage` | Saves a JSON object as persistent storage | **Replaces everything**. 25 MB limit |
| `get_storage` | Returns the full stored object | Storage is also injected automatically each run |
| `append_storage` | Appends/merges data without replacing | Best for journals and histories. 25 MB combined |
| `web_fetch` | HTTP GET to any URL | For dynamic URLs; prefer `{{get:...}}` for fixed ones (cheaper). Response is untrusted |
| `run_javascript_code` | Runs the body of an async function in the Code Strategy sandbox and returns its value | Same limits, forbidden identifiers and code rules as Code Strategies (see `sigrex-code-strategies`). Called `execute_javascript` in the 0.3.4 changelog |
| `send_email` | Emails the strategy owner | Alerts, reports, summaries |
| `get_current_date_time` | Current date/time | |
| `get_signal_logs` | Signal history of other strategies, incl. outcomes/profitability | Performance review |
| `get_error_logs` | Error history of strategies | Diagnosing failures |
| `get_code_strategy` | Code Strategy by `id` (code, status, last run; no storage) | |
| `get_llm_session` | LLM Session by `id` (prompt, status) | |
| `get_code_reaction` | Code Reaction by `id` (code, status) | |
| `get_llm_reaction` | LLM Reaction by `id` (prompt, status) | |
| `set_code_strategy` | Replace a Code Strategy's code (`id`, `code`); status kept | Powerful: can change live logic |
| `set_llm_session` | Replace an LLM Session's prompt (`id`, `prompt`) | |
| `set_code_reaction` | Replace a Code Reaction's code (`id`, `code`) | |
| `set_llm_reaction` | Replace an LLM Reaction's prompt (`id`, `prompt`) | |
| `set_code_strategy_status` | Start/stop a Code Strategy (`id`, `ACTIVE`/`INACTIVE`) | |
| `set_llm_session_status` | Start/stop an LLM Session | Can stop itself |
| `set_code_reaction_status` | Start/stop a Code Reaction | |
| `set_llm_reaction_status` | Start/stop an LLM Reaction | |

Do not confuse these runtime tools (used **by the model inside Sigrex**) with
the Sigrex **MCP** tools (used by you, the agent, from outside); see
`sigrex-api-mcp`.

## Storage

- LLM storage limit: 25 MB (Code Strategy storage is 24 KB, a different
  store).
- Injected into the system context on every run; `{{storage}}` is only
  needed to reference it explicitly in the user prompt.
- Large storage costs tokens every run. Instruct the model to trim (e.g. keep
  the last 200 journal entries, or summaries).
- Reset with `PUT /strategy/llm-session/{id}/reset` and
  `{"resetTriggers":false,"resetStorage":true,"resetResponse":false}`.

## Reset Semantics

| Key | Effect |
| --- | --- |
| `resetTriggers` | Clears last action/time; the model will believe no position is open |
| `resetStorage` | Clears the model's memory |
| `resetResponse` | Clears stored response history |

All three keys are required in the body. Never reset triggers while a
position is open on the exchange.

## Schedules

`cron_interval`: `3M`, `5M`, `15M`, `30M`, `1H`, `2H`, `4H`, `8H`, `12H`, `1D`.

| Interval | LLM call timeout |
| --- | --- |
| 3 min | 1.5 min |
| 5 min | 2.5 min |
| 15 min to 1 day | 7.5 min |
| (1 min, listed in the changelog only) | 30 s |
| LLM Reaction (per event) | 5 min |

## Chart Options

| Field | Values |
| --- | --- |
| `use_chart` | `true` / `false` (needs a vision-capable model) |
| `chart_symbol` | TradingView symbol: `BINANCE:BTCUSDT`, `BINANCE:ETHUSDT`, or `BTCUSDT` |
| `chart_interval` | `1`, `3`, `5`, `15`, `30`, `60`, `120`, `240`, `D` |
| `chart_data_range` | `1D`, `5D`, `1M`, `3M`, `6M`, `YTD`, `12M`, `60M`, `ALL` |
| `chart_studies` | Up to **2** study IDs from the table below |

The UI guide highlights RSI, MACD, EMA, VWAP, ATR and Bollinger Bands. Their
API IDs are `RSI@tv-basicstudies`, `MACD@tv-basicstudies`,
`MAExp@tv-basicstudies` (EMA), `VWAP@tv-basicstudies`, `ATR@tv-basicstudies`,
and `BB@tv-basicstudies`.

Common misconfigurations: chart enabled with a text-only model; expecting
indicator analysis with the chart disabled; very short session intervals on
long candles (e.g. `3M` sessions on `D` candles).

### All allowed `chart_studies` values

| Study ID | Study ID | Study ID |
| --- | --- | --- |
| `ACCD@tv-basicstudies` | `studyADR@tv-basicstudies` | `AROON@tv-basicstudies` |
| `ATR@tv-basicstudies` | `AwesomeOscillator@tv-basicstudies` | `BB@tv-basicstudies` |
| `BollingerBandsR@tv-basicstudies` | `BollingerBandsWidth@tv-basicstudies` | `CMF@tv-basicstudies` |
| `ChaikinOscillator@tv-basicstudies` | `chandeMO@tv-basicstudies` | `ChoppinessIndex@tv-basicstudies` |
| `CCI@tv-basicstudies` | `CRSI@tv-basicstudies` | `CorrelationCoefficient@tv-basicstudies` |
| `DetrendedPriceOscillator@tv-basicstudies` | `DM@tv-basicstudies` | `DONCH@tv-basicstudies` |
| `DoubleEMA@tv-basicstudies` | `EaseOfMovement@tv-basicstudies` | `EFI@tv-basicstudies` |
| `ENV@tv-basicstudies` | `FisherTransform@tv-basicstudies` | `HV@tv-basicstudies` |
| `hullMA@tv-basicstudies` | `IchimokuCloud@tv-basicstudies` | `KLTNR@tv-basicstudies` |
| `KST@tv-basicstudies` | `LinearRegression@tv-basicstudies` | `MACD@tv-basicstudies` |
| `MOM@tv-basicstudies` | `MF@tv-basicstudies` | `MoonPhases@tv-basicstudies` |
| `MASimple@tv-basicstudies` | `MAExp@tv-basicstudies` | `MAWeighted@tv-basicstudies` |
| `OBV@tv-basicstudies` | `PSAR@tv-basicstudies` | `PivotPointsHighLow@tv-basicstudies` |
| `PivotPointsStandard@tv-basicstudies` | `PriceOsc@tv-basicstudies` | `PriceVolumeTrend@tv-basicstudies` |
| `ROC@tv-basicstudies` | `RSI@tv-basicstudies` | `VigorIndex@tv-basicstudies` |
| `VolatilityIndex@tv-basicstudies` | `SMIErgodicIndicator@tv-basicstudies` | `SMIErgodicOscillator@tv-basicstudies` |
| `Stochastic@tv-basicstudies` | `StochasticRSI@tv-basicstudies` | `TripleEMA@tv-basicstudies` |
| `Trix@tv-basicstudies` | `UltimateOsc@tv-basicstudies` | `VSTOP@tv-basicstudies` |
| `Volume@tv-basicstudies` | `VWAP@tv-basicstudies` | `MAVolumeWeighted@tv-basicstudies` |
| `WilliamR@tv-basicstudies` | `WilliamsAlligator@tv-basicstudies` | `WilliamsFractal@tv-basicstudies` |
| `ZigZag@tv-basicstudies` |  |  |
