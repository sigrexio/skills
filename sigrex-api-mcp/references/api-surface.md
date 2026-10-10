# Sigrex REST API Surface

Complete endpoint and request-body map for the Sigrex REST API, generated
from the OpenAPI blocks in the live API reference
(https://docs.sigrex.io/api-reference) and cross-checked against the official
TypeScript client (https://github.com/sigrexio/sigrex-client-ts). If a field
here conflicts with the live page, trust the live page and mention the
difference.

## Conventions

- **Host:** `https://api.sigrex.io`. Every path starts with `/api/v2`; the
  tables below omit that prefix for readability, but the prefix **is part of
  the signed path**.
- **Auth headers on every request:** `api-key`, `timestamp` (Unix seconds),
  `signature`. See `SKILL.md` for the exact signing algorithm.
- **Bodies:** JSON with `Content-Type: application/json`. Field names are
  `snake_case` for bots, webhooks and strategies, and `camelCase` for API-key
  connections, sharing (`userId`), reset (`resetTriggers`), and visibility
  (`isPublic`). Copy them exactly.
- **IDs:** path `{id}` values are the numeric IDs returned by list/get calls.
  Bodies take numbers for `*_id` fields (`webhook_id: 12`, not `"12"`).
  `duplicate` bodies take `{"id": "<id>"}` as a string.
- **Status bodies:** `{"status": "ACTIVE"}` or `{"status": "INACTIVE"}`.
  Setting the status a resource already has returns `400`.
- **Errors:** route errors are JSON `{"error": "<message>"}`. Authentication
  failures return `401` with `{"message": "..."}`, for example
  `Missing api-key header` or `Invalid API key` (observed live). `400`
  validation, missing field, or (on some routes) a plan limit; `402`
  plan/package limit reached; `404` referenced resource not found; `409`
  resource still in use; `500` server.
- **Pagination:** routes that list bots/reactions attached to another resource
  require both `page` and `limit` query parameters (they return `400`
  without them). The response envelope is not published.
- **Response bodies:** the published spec references response schemas
  (`BotWebhook`, `CexSignalBot`, `CodeStrategy`, ...) without defining them.
  Read the actual response; do not assume field names. The official plugin
  documents that strategy objects expose `status`, `sendSignal`,
  `lastTrigger` and `lastRunAt`.

## Exchange catalog

| Method | Path (after `/api/v2`) | Purpose | Notable errors |
| --- | --- | --- | --- |
| GET | `/exchange?enabled=&chainId=` | Get all exchanges with optional filtering | - |
| GET | `/exchange/cex` | Get all CEX exchanges | - |
| GET | `/exchange/dex/{chain}` | Get all DEX exchanges by chain ID | `400` Missing chain ID |
| GET | `/exchange/prediction` | Get all Prediction exchanges | - |
| GET | `/exchange/with-exchange-rate` | Get all exchanges with exchange rates | - |

## Exchange (CEX) API keys

| Method | Path (after `/api/v2`) | Purpose | Notable errors |
| --- | --- | --- | --- |
| GET | `/api/exchange` | Get all exchange API keys for user | - |
| POST | `/api/exchange` | Create a new exchange API key | `400` Missing required fields or invalid credentials; `404` Exchange not found |
| GET | `/api/exchange/bot/signal/{id}?page=&limit=` | Get signal bots that use an API key | `400` Missing id, page, or limit |
| POST | `/api/exchange/test` | Test exchange API key credentials | `400` Missing required fields or invalid credentials; `404` Exchange not found |
| DELETE | `/api/exchange/{id}` | Delete an exchange API key | `400` Missing api id; `404` API key not found; `409` API key is in use by signal bots |
| PUT | `/api/exchange/{id}/status` | Update API key status | `400` Missing id or invalid status; `404` API key not found |

Body for `POST /api/exchange`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `exchangeId` | number | yes | The id of a CEX exchange |
| `name` | string | no | The name of the API key max 255 characters |
| `publicKey` | string | yes |  |
| `privateKey` | string | yes |  |
| `extra` | string | no | Some extra value if required, depends on the exchange |

Body for `POST /api/exchange/test`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `exchangeId` | number | yes | The id of a CEX exchange |
| `publicKey` | string | yes |  |
| `privateKey` | string | yes |  |
| `extra` | string | no | Some extra value if required, depends on the exchange |

Body for `PUT /api/exchange/{id}/status`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `status` | string | yes | Values: `ACTIVE`, `INACTIVE`. |

## LLM API keys

| Method | Path (after `/api/v2`) | Purpose | Notable errors |
| --- | --- | --- | --- |
| GET | `/api/llm` | Get all LLM API keys for user | - |
| POST | `/api/llm` | Create a new LLM API key | `400` Missing required fields or invalid API key; `404` Service or model not found |
| GET | `/api/llm/models/{serviceId}` | Get models for a specific service | `400` Missing serviceId |
| GET | `/api/llm/services` | Get all enabled LLM services | - |
| DELETE | `/api/llm/{id}` | Delete an LLM API key | `400` Missing id or API key is in use |
| PUT | `/api/llm/{id}/model` | Update model for an API key | `400` Missing id or modelId; `404` API key or model not found |

Body for `POST /api/llm`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | The name of the API key max 255 characters |
| `serviceId` | number | yes | The id of a LLM service |
| `modelId` | number | yes | The id of a LLM model |
| `apiKey` | string | yes |  |

Body for `PUT /api/llm/{id}/model`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `modelId` | number | yes | The id of a LLM model |

## Prediction API keys

| Method | Path (after `/api/v2`) | Purpose | Notable errors |
| --- | --- | --- | --- |
| GET | `/api/prediction` | Get all prediction API keys | - |
| POST | `/api/prediction` | Create a new prediction API key | `400` Missing required fields, invalid name, or invalid credentials; `404` Exchange not found |
| GET | `/api/prediction/bot/signal/{id}?page=&limit=` | Get prediction signal bots by API ID | `400` Missing required parameters |
| POST | `/api/prediction/test` | Test prediction API credentials | `400` Missing required fields, invalid credentials, or exchange not found |
| DELETE | `/api/prediction/{id}` | Delete prediction API key | `400` Missing API ID; `404` API key not found; `409` API key is in use by signal bots |
| PUT | `/api/prediction/{id}/status` | Update prediction API key status | `400` Missing id, invalid status, or status already set; `404` API key not found |

Body for `POST /api/prediction`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | The name of the API key max 255 characters |
| `exchangeId` | number | yes | The id of an exchange |
| `funderAddress` | string | yes | PolyMarket platform funder address |
| `walletPrivateKey` | string | yes | Signer wallet private key |

Body for `POST /api/prediction/test`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `exchangeId` | number | yes | The id of an exchange |
| `funderAddress` | string | yes | PolyMarket platform funder address (the published test schema says `number`; send the `0x...` address as a string) |
| `walletPrivateKey` | string | yes | Signer wallet private key |

Body for `PUT /api/prediction/{id}/status`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `status` | string | yes | Values: `ACTIVE`, `INACTIVE`. |

## Bot webhooks

| Method | Path (after `/api/v2`) | Purpose | Notable errors |
| --- | --- | --- | --- |
| GET | `/webhook/bot` | Get all bot webhooks | - |
| POST | `/webhook/bot` | Create a new bot webhook | `400` Missing required fields, invalid password, or webhook limit reached; `402` Webhook limit reached; `404` Package not found |
| GET | `/webhook/bot/bot/signal/{id}/cex?page=&limit=` | Get CEX signal bots for webhook | `400` Missing webhook id, page, or limit |
| GET | `/webhook/bot/bot/signal/{id}/dex?page=&limit=` | Get DEX signal bots for webhook | `400` Missing webhook id, page, or limit |
| POST | `/webhook/bot/share/{id}` | Share webhook with user | `400` Missing webhook/user id, invalid permission, or not friends; `404` Webhook not found |
| DELETE | `/webhook/bot/share/{id}` | Remove webhook share | `400` Missing webhook/user id or not friends; `404` Webhook not found |
| GET | `/webhook/bot/shared` | Get all shared webhooks for user | - |
| GET | `/webhook/bot/shared/by/{id}` | Get webhooks shared by specific user | `400` Missing user id; `404` Friendship not found |
| GET | `/webhook/bot/shared/with/{id}` | Get webhooks shared with specific user | `400` Missing user id; `404` Friendship not found |
| GET | `/webhook/bot/{id}` | Get bot webhook by ID | `400` Missing webhook id; `404` Bot webhook not found |
| PUT | `/webhook/bot/{id}` | Update bot webhook | `400` Missing webhook id or invalid password; `404` Webhook not found |
| DELETE | `/webhook/bot/{id}` | Delete bot webhook | `400` Missing webhook id; `404` Webhook not found; `409` Webhook is in use by bots or strategies |
| GET | `/webhook/bot/{id}/shares` | Get webhook shares | `400` Missing webhook id |
| PUT | `/webhook/bot/{id}/status` | Update webhook status | `400` Missing webhook id, invalid status, or status already set; `402` Webhook limit reached; `404` Webhook or package not found |

Body for `POST /webhook/bot`, `PUT /webhook/bot/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | The name of the bot hook max 255 characters |
| `description` | string | no | The description of the bot hook max 255 characters |
| `is_safe` | boolean | no | Set it true if want to set hash key |
| `hash_key` | string | no | The key of the bot hook |

Body for `POST /webhook/bot/share/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `userId` | string | yes | The user id of the user to share the webhook with |

Body for `DELETE /webhook/bot/share/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `userId` | string | yes | User ID to unshare with |

Body for `PUT /webhook/bot/{id}/status`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `status` | string | yes | Values: `ACTIVE`, `INACTIVE`. |

## Data webhooks

| Method | Path (after `/api/v2`) | Purpose | Notable errors |
| --- | --- | --- | --- |
| GET | `/webhook/data` | Get all data webhooks | - |
| POST | `/webhook/data` | Create a new data webhook | `400` Missing required fields or invalid password; `402` Webhook limit reached; `404` Package not found |
| POST | `/webhook/data/share/{id}` | Share webhook with user | `400` Missing webhook/user id, invalid permission, or not friends; `404` Webhook not found |
| DELETE | `/webhook/data/share/{id}` | Remove webhook share | `400` Missing webhook/user id or not friends; `404` Webhook not found |
| GET | `/webhook/data/shared` | Get all shared data webhooks for user | - |
| GET | `/webhook/data/shared/by/{id}` | Get data webhooks shared by specific user | `400` Missing user id; `404` Friendship not found |
| GET | `/webhook/data/shared/with/{id}` | Get data webhooks shared with specific user | `400` Missing user id; `404` Friendship not found |
| GET | `/webhook/data/{id}` | Get data webhook by ID | `400` Missing webhook id; `404` Webhook not found |
| PUT | `/webhook/data/{id}` | Update data webhook | `400` Missing webhook id or invalid password; `404` Webhook not found |
| DELETE | `/webhook/data/{id}` | Delete data webhook | `400` Missing webhook id; `404` Webhook not found; `409` Webhook is in use by reactions |
| GET | `/webhook/data/{id}/code-reactions?page=&limit=` | Get code reactions for webhook | `400` Missing webhook id, page, or limit |
| GET | `/webhook/data/{id}/llm-reactions?page=&limit=` | Get LLM reactions for webhook | `400` Missing webhook id, page, or limit |
| GET | `/webhook/data/{id}/shares` | Get webhook shares | `400` Missing webhook id |
| PUT | `/webhook/data/{id}/status` | Update webhook status | `400` Missing webhook id or invalid status; `402` Webhook limit reached; `404` Webhook not found |

Body for `POST /webhook/data`, `PUT /webhook/data/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | The name of the data hook max 255 characters |
| `description` | string | no | The description of the data hook max 255 characters |
| `is_safe` | boolean | no | Set it true if want to set hash key |
| `hash_key` | string | no | The key of the data hook |

Body for `POST /webhook/data/share/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `userId` | string | yes | The user id of the user to share the webhook with |

Body for `DELETE /webhook/data/share/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `userId` | string | yes | User ID to unshare with |

Body for `PUT /webhook/data/{id}/status`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `status` | string | yes | Values: `ACTIVE`, `INACTIVE`. |

## CEX signal bots

| Method | Path (after `/api/v2`) | Purpose | Notable errors |
| --- | --- | --- | --- |
| GET | `/bot/signal/cex` | Get all CEX signal bots | - |
| POST | `/bot/signal/cex` | Create a new CEX signal bot | `400` Missing required fields or invalid data; `404` API or webhook not found |
| POST | `/bot/signal/cex/duplicate` | Duplicate a CEX signal bot | `400` Missing bot id or bot limit reached; `404` Bot or webhook not found |
| GET | `/bot/signal/cex/total` | Get the total number of CEX signal bots | - |
| GET | `/bot/signal/cex/{id}` | Get CEX signal bot by ID | `400` Missing bot id; `404` Bot not found |
| PUT | `/bot/signal/cex/{id}` | Update CEX signal bot | `400` Missing bot id or invalid data; `404` Bot, API key, or webhook not found |
| DELETE | `/bot/signal/cex/{id}` | Delete CEX signal bot | `400` Missing bot id; `404` Bot not found |
| PUT | `/bot/signal/cex/{id}/status` | Update CEX signal bot status | `400` Missing bot id or invalid status; `402` Bot limit reached; `404` Bot or package not found |

Body for `POST /bot/signal/cex`, `PUT /bot/signal/cex/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | The name of the bot max 255 characters |
| `folder_id` | number | no | The folder id of the bot |
| `webhook_id` | number | yes | The id of a bot webhook |
| `api_id` | number | yes | The id of a bot CEX API key |
| `symbol` | string | yes | The symbol of the bot |
| `pair_base` | string | no | The base currency of the pair (On ALPACA not required) |
| `pair_quote` | string | no | The quote currency of the pair (On ALPACA not required) |
| `amount_from_signal` | boolean | yes | Set if amount is coming from signal |
| `amount` | number | no | The amount to trade (if amount_from_signal is false) |
| `is_quote` | boolean | no | Set if the amount is in quote currency |
| `delay` | number | no | Set how often the bot will check for new signals. eg. 10 means 10 in 1 second |

Body for `POST /bot/signal/cex/duplicate`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | yes | Bot ID to duplicate |

Body for `PUT /bot/signal/cex/{id}/status`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `status` | string | yes | Values: `ACTIVE`, `INACTIVE`. |

## DEX signal bots

| Method | Path (after `/api/v2`) | Purpose | Notable errors |
| --- | --- | --- | --- |
| GET | `/bot/signal/dex` | Get all DEX signal bots | - |
| POST | `/bot/signal/dex` | Create a new DEX signal bot | `400` Missing parameters, invalid data, or invalid contract address; `404` Factory or webhook not found |
| GET | `/bot/signal/dex/factory/{chainId}/{exchangeId}` | Get bot factory by chain and exchange | `400` Missing chain or exchange; `404` Factory not found |
| GET | `/bot/signal/dex/total` | Get the total number of DEX signal bots | - |
| GET | `/bot/signal/dex/{chainId}/{address}` | Get DEX signal bot by chain and address | `400` Missing chain id or address; `404` Bot not found |
| GET | `/bot/signal/dex/{id}` | Get DEX signal bot by ID | `400` Missing bot id; `404` Bot not found |
| PUT | `/bot/signal/dex/{id}` | Update DEX signal bot | `400` Missing bot id or invalid data; `404` Bot or webhook not found |
| DELETE | `/bot/signal/dex/{id}` | Delete DEX signal bot | `400` Missing bot id; `404` Bot not found |
| PUT | `/bot/signal/dex/{id}/status` | Update DEX signal bot status | `400` Missing bot id, invalid status, or status already set; `402` DEX bot limit reached; `404` Bot not found |

Body for `POST /bot/signal/dex`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | The name of the bot max 255 characters |
| `folder_id` | number | no | The folder id of the bot |
| `webhook_id` | number | yes | The id of a bot webhook |
| `factory_id` | number | yes | The id of a bot factory |
| `chain_id` | number | yes | The id of a chain |
| `address` | string | yes | The address of the bot |
| `symbol` | string | yes | The symbol of the bot |
| `delay` | number | no | Set how often the bot will check for new signals. eg. 10 means 10 in 1 second |

Body for `PUT /bot/signal/dex/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | The name of the bot max 255 characters |
| `folder_id` | number | no | The folder id of the bot |
| `webhook_id` | number | yes | The id of a bot webhook |
| `symbol` | string | yes | The symbol of the bot |
| `delay` | number | no | Set how often the bot will check for new signals. eg. 10 means 10 in 1 second |

Body for `PUT /bot/signal/dex/{id}/status`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `status` | string | yes | Values: `ACTIVE`, `INACTIVE`. |

## Prediction signal bots

| Method | Path (after `/api/v2`) | Purpose | Notable errors |
| --- | --- | --- | --- |
| GET | `/bot/signal/prediction` | Get all prediction signal bots | - |
| POST | `/bot/signal/prediction` | Create a new prediction signal bot | `400` Missing required fields, invalid data, or limit exceeded; `404` API key or webhook not found |
| POST | `/bot/signal/prediction/duplicate` | Duplicate a prediction signal bot | `400` Missing bot ID, bot not found, or limit exceeded; `404` Bot or webhook not found |
| GET | `/bot/signal/prediction/market/{exchange}/{slug}` | Get prediction market by slug | `400` Missing slug or invalid slug |
| GET | `/bot/signal/prediction/total` | Get the total number of Prediction signal bots | - |
| GET | `/bot/signal/prediction/{id}` | Get prediction signal bot by ID | `400` Missing bot ID; `404` Bot not found |
| PUT | `/bot/signal/prediction/{id}` | Update prediction signal bot | `400` Missing required fields or invalid data; `404` Bot, API key, or webhook not found |
| DELETE | `/bot/signal/prediction/{id}` | Delete prediction signal bot | `400` Missing bot ID; `404` Bot not found |
| PUT | `/bot/signal/prediction/{id}/status` | Update prediction signal bot status | `400` Missing bot ID, invalid status, or limit exceeded; `402` Bot limit exceeded; `404` Bot not found |

Body for `POST /bot/signal/prediction`, `PUT /bot/signal/prediction/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | The name of the bot max 255 characters |
| `folder_id` | number | no | The folder id of the bot |
| `webhook_id` | number | yes | The id of a bot webhook |
| `api_id` | number | yes | The id of a bot Prediction API key |
| `slug_from_signal` | boolean | yes | Set to true to specify a market slug dynamically within the signal payload. |
| `url` | string | no | The market url (required if slug_from_signal is false) |
| `amount_from_signal` | boolean | yes | Set if amount is coming from signal |
| `amount` | number | no | The amount of the bot in USDC (if amount_from_signal is false) |
| `delay` | number | no | Set how often the bot will check for new signals. eg. 10 means 10 in 1 second |

Body for `POST /bot/signal/prediction/duplicate`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | yes | Bot ID to duplicate |

Body for `PUT /bot/signal/prediction/{id}/status`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `status` | string | yes | Values: `ACTIVE`, `INACTIVE`. |

## Code strategies

| Method | Path (after `/api/v2`) | Purpose | Notable errors |
| --- | --- | --- | --- |
| GET | `/strategy/code` | Get all code strategies | - |
| POST | `/strategy/code` | Create a new code strategy | `400` Missing required fields, invalid code, or strategy limit reached; `404` Exchange or webhook not found |
| POST | `/strategy/code/duplicate` | Duplicate a code strategy | `400` Missing id or strategy limit reached |
| GET | `/strategy/code/total` | Get the total number of Code Strategies | - |
| GET | `/strategy/code/{id}` | Get code strategy by ID | `400` Missing id; `404` Strategy not found |
| PUT | `/strategy/code/{id}` | Update code strategy | `400` Missing id, invalid code, or validation errors; `404` Strategy, exchange, or webhook not found |
| DELETE | `/strategy/code/{id}` | Delete code strategy | `400` Missing id; `404` Strategy not found |
| PUT | `/strategy/code/{id}/public` | Update code strategy public visibility | `400` Missing id or invalid public flag; `404` Strategy not found |
| PUT | `/strategy/code/{id}/reset` | Reset code strategy triggers and/or storage | `400` Missing id, invalid options, or nothing to reset; `404` Strategy not found |
| PUT | `/strategy/code/{id}/status` | Update code strategy status | `400` Missing id, invalid status, status already set, or strategy limit reached; `404` Strategy not found |
| DELETE | `/strategy/code/{id}/store` | Delete code strategy storage | `400` Missing id; `404` Strategy not found |

Body for `POST /strategy/code`, `PUT /strategy/code/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | The name of the strategy max 255 characters |
| `folder_id` | number | no | The folder id of the strategy |
| `send_signal` | boolean | no | Set true to enable signal generation |
| `webhook_id` | number | no | The id of the bot hook where signal will be sent (required if send_signal is true) |
| `symbol` | string | no | The signal symbol or symbols of the strategy separated by comma (required if send_signal is true) |
| `code` | string | yes | The JavaScript code of the strategy |
| `use_price` | boolean | no | Set true if you want to use price ($.Price) in code |
| `exchange_id` | number | no | The id of the exchange where the price is fetched (required exchange with hasExchangeRate set to true) |
| `price_symbol` | string | no | The symbol of the price (required if use_price is true) |

Body for `POST /strategy/code/duplicate`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | yes | Strategy ID to duplicate |

Body for `PUT /strategy/code/{id}/public`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `isPublic` | boolean | yes | Set true to make the strategy public |

Body for `PUT /strategy/code/{id}/reset`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `resetTriggers` | boolean | yes | Set true to reset triggers |
| `resetStore` | boolean | yes | Set true to reset store |

Body for `PUT /strategy/code/{id}/status`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `status` | string | yes | Values: `ACTIVE`, `INACTIVE`. |

## LLM sessions

| Method | Path (after `/api/v2`) | Purpose | Notable errors |
| --- | --- | --- | --- |
| GET | `/strategy/llm-session` | Get all LLM sessions | - |
| POST | `/strategy/llm-session` | Create a new LLM session | `400` Missing required fields, invalid configuration, or session limit reached; `402` Session limit reached; `404` Package or LLM API not found |
| POST | `/strategy/llm-session/duplicate` | Duplicate an LLM session | `400` Missing id or session limit reached |
| GET | `/strategy/llm-session/folder` | Get all LLM session folders | - |
| POST | `/strategy/llm-session/folder` | Create a new LLM session folder | `400` Invalid name or max folder limit reached |
| GET | `/strategy/llm-session/folder/root` | Get LLM Sessions from root folder | - |
| GET | `/strategy/llm-session/folder/{id}` | Get LLM session folder by ID | `400` Missing id; `404` Folder not found |
| PUT | `/strategy/llm-session/folder/{id}` | Update LLM session folder | `400` Missing id, invalid name, or folder not found; `404` Folder not found |
| DELETE | `/strategy/llm-session/folder/{id}` | Delete LLM session folder | `400` Missing id, folder not found, or folder is not empty; `404` Folder not found |
| GET | `/strategy/llm-session/total` | Get the total number of LLM sessions | - |
| GET | `/strategy/llm-session/{id}` | Get LLM session by ID | `400` Missing id; `404` Session not found |
| PUT | `/strategy/llm-session/{id}` | Update LLM session | `400` Missing id, invalid configuration, or validation errors; `404` Session, webhook, or LLM API not found |
| DELETE | `/strategy/llm-session/{id}` | Delete LLM session | `400` Missing id; `404` Session not found |
| PUT | `/strategy/llm-session/{id}/public` | Update LLM session public visibility | `400` Missing id or invalid public flag; `404` Session not found |
| PUT | `/strategy/llm-session/{id}/reset` | Reset LLM session triggers, history or responses | `400` Missing id, invalid options, or nothing to reset; `404` Session not found |
| PUT | `/strategy/llm-session/{id}/status` | Update LLM session status | `400` Missing id, invalid status, or session limit reached; `402` Active session limit reached; `404` Session not found |

Body for `POST /strategy/llm-session`, `PUT /strategy/llm-session/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | The name of the strategy max 255 characters |
| `folder_id` | number | no | The folder id of the strategy |
| `llm_api_id` | number | yes | The main LLM Api key id used for the strategy |
| `fallback_api_id` | number | no | The fallback LLM Api key id used for the strategy if main is not available |
| `cron_interval` | string | yes | The schedule interval of the strategy Values: `3M`, `5M`, `15M`, `30M`, `1H`, `2H`, `4H`, `8H`, `12H`, `1D`. |
| `use_chart` | boolean | no | Set true if you want to send chart image with the strategy prompt |
| `chart_symbol` | string | no | The Tradingview symbol of the chart (required if use_chart is true) |
| `chart_interval` | string | no | The interval of the chart (required if use_chart is true) Values: `1`, `3`, `5`, `15`, `30`, `60`, `120`, `240`, `D`. |
| `chart_studies` | array<string> | no | The studies of the chart (optional if use_chart is true) 61 allowed values (see the LLM skill reference). Max 2 items. |
| `chart_data_range` | string | no | The data range of the chart (optional if use_chart is true) Values: `1D`, `5D`, `1M`, `3M`, `6M`, `YTD`, `12M`, `60M`, `ALL`. |
| `prompt` | string | yes | The strategy prompt minimum length is 20 characters maximum length is 1000000000 characters |
| `send_signal` | boolean | no | Set true to send signal to bot hook |
| `webhook_id` | number | no | The id of the bot hook where signal will be sent (required if send_signal is true) |
| `signal_symbol` | string | no | The signal symbol or symbols of the strategy separated by comma |
| `send_email` | boolean | no | Set true to send the LLM response to the user email |

Body for `POST /strategy/llm-session/duplicate`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | yes | Session ID to duplicate |

Body for `POST /strategy/llm-session/folder`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | Folder name (optional, auto-generated if not provided) |

Body for `PUT /strategy/llm-session/folder/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | New folder name (optional, auto-generated if not provided) |

Body for `PUT /strategy/llm-session/{id}/public`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `isPublic` | boolean | yes | Set true to make the strategy public |

Body for `PUT /strategy/llm-session/{id}/reset`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `resetTriggers` | boolean | yes | Set true to reset triggers |
| `resetStorage` | boolean | yes | Set true to reset storage |
| `resetResponse` | boolean | yes | Set true to reset response history |

Body for `PUT /strategy/llm-session/{id}/status`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `status` | string | yes | Values: `ACTIVE`, `INACTIVE`. |

## Code reactions

| Method | Path (after `/api/v2`) | Purpose | Notable errors |
| --- | --- | --- | --- |
| GET | `/strategy/reaction/code` | Get all code reactions | - |
| POST | `/strategy/reaction/code` | Create a new code reaction | `400` Missing required fields, invalid code, or reaction limit reached; `404` Exchange, webhook, or data hook not found |
| POST | `/strategy/reaction/code/duplicate` | Duplicate a code reaction | `400` Missing id or reaction limit reached |
| GET | `/strategy/reaction/code/folder` | Get all code reaction folders | - |
| POST | `/strategy/reaction/code/folder` | Create a new code reaction folder | `400` Invalid name or max folder limit reached |
| GET | `/strategy/reaction/code/folder/root` | Get code reactions from root folder | - |
| GET | `/strategy/reaction/code/folder/{id}` | Get code reaction folder by ID | `400` Missing id; `404` Folder not found |
| PUT | `/strategy/reaction/code/folder/{id}` | Update code reaction folder | `400` Missing id, invalid name, or folder not found; `404` Folder not found |
| DELETE | `/strategy/reaction/code/folder/{id}` | Delete code reaction folder | `400` Missing id, folder not found, or folder is not empty; `404` Folder not found |
| GET | `/strategy/reaction/code/total` | Get the total number of Code Reactions | - |
| GET | `/strategy/reaction/code/{id}` | Get code reaction by ID | `400` Missing id; `404` Strategy not found |
| PUT | `/strategy/reaction/code/{id}` | Update code reaction | `400` Missing id, invalid code, or validation errors; `404` Reaction, exchange, webhook, or data hook not found |
| DELETE | `/strategy/reaction/code/{id}` | Delete code reaction | `400` Missing id; `404` Strategy not found |
| PUT | `/strategy/reaction/code/{id}/public` | Update code reaction public visibility | `400` Missing id or invalid public flag; `404` Strategy not found |
| PUT | `/strategy/reaction/code/{id}/reset` | Reset code reaction triggers and/or storage | `400` Missing id, invalid options, or nothing to reset; `404` Strategy not found |
| PUT | `/strategy/reaction/code/{id}/status` | Update code reaction status | `400` Missing id, invalid status, or reaction limit reached; `404` Strategy not found |
| DELETE | `/strategy/reaction/code/{id}/store` | Delete code reaction storage | `400` Missing id; `404` Strategy not found |

Body for `POST /strategy/reaction/code`, `PUT /strategy/reaction/code/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | The name of the strategy max 255 characters |
| `folder_id` | number | no | The folder id of the reaction |
| `data_webhook_id` | number | yes | The id of the data hook which will be used to get data |
| `send_signal` | boolean | no | Set true to enable signal generation |
| `webhook_id` | number | no | The id of the bot hook where signal will be sent (required if send_signal is true) |
| `symbol` | string | no | The signal symbol or symbols of the strategy separated by comma (required if send_signal is true) |
| `delay` | number | no | Set how often the reaction will check for new signals. eg. 10 means 10 in 1 second |
| `code` | string | yes | The JavaScript code of the strategy |
| `use_price` | boolean | no | Set true if you want to use price ($.Price) in code |
| `exchange_id` | number | no | The id of the exchange where the price is fetched (required exchange with hasExchangeRate set to true) |
| `price_symbol` | string | no | The symbol of the price (required if use_price is true) |

Body for `POST /strategy/reaction/code/duplicate`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | yes | Reaction ID to duplicate |

Body for `POST /strategy/reaction/code/folder`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | Folder name (optional, auto-generated if not provided) |

Body for `PUT /strategy/reaction/code/folder/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | New folder name (optional, auto-generated if not provided) |

Body for `PUT /strategy/reaction/code/{id}/public`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `isPublic` | boolean | yes | Set true to make the strategy public |

Body for `PUT /strategy/reaction/code/{id}/reset`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `resetTriggers` | boolean | yes | Set true to reset triggers |
| `resetStore` | boolean | yes | Set true to reset store |

Body for `PUT /strategy/reaction/code/{id}/status`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `status` | string | yes | Values: `ACTIVE`, `INACTIVE`. |

## LLM reactions

| Method | Path (after `/api/v2`) | Purpose | Notable errors |
| --- | --- | --- | --- |
| GET | `/strategy/reaction/llm` | Get all LLM reactions | - |
| POST | `/strategy/reaction/llm` | Create a new LLM reaction | `400` Missing required fields, invalid prompt, or reaction limit reached; `402` Reaction limit reached; `404` Data webhook, bot webhook, or LLM API not found |
| POST | `/strategy/reaction/llm/duplicate` | Duplicate an LLM reaction | `400` Missing id or reaction limit reached |
| GET | `/strategy/reaction/llm/folder` | Get all LLM reaction folders | - |
| POST | `/strategy/reaction/llm/folder` | Create a new LLM reaction folder | `400` Invalid name or max folder limit reached |
| GET | `/strategy/reaction/llm/folder/root` | Get LLM reactions from root folder | - |
| GET | `/strategy/reaction/llm/folder/{id}` | Get LLM reaction folder by ID | `400` Missing id; `404` Folder not found |
| PUT | `/strategy/reaction/llm/folder/{id}` | Update LLM reaction folder | `400` Missing id, invalid name, or folder not found; `404` Folder not found |
| DELETE | `/strategy/reaction/llm/folder/{id}` | Delete LLM reaction folder | `400` Missing id, folder not found, or folder is not empty; `404` Folder not found |
| GET | `/strategy/reaction/llm/total` | Get the total number of LLM Reaction | - |
| GET | `/strategy/reaction/llm/{id}` | Get LLM reaction by ID | `400` Missing id; `404` Reaction not found |
| PUT | `/strategy/reaction/llm/{id}` | Update LLM reaction | `400` Missing id, invalid prompt, or validation errors; `404` Reaction, webhook, or LLM API not found |
| DELETE | `/strategy/reaction/llm/{id}` | Delete LLM reaction | `400` Missing id; `404` Reaction not found |
| PUT | `/strategy/reaction/llm/{id}/public` | Update LLM reaction public visibility | `400` Missing id or invalid public flag; `404` Strategy not found |
| PUT | `/strategy/reaction/llm/{id}/reset` | Reset LLM reaction triggers, history or responses | `400` Missing id, invalid options, or nothing to reset; `404` Reaction not found |
| PUT | `/strategy/reaction/llm/{id}/status` | Update LLM reaction status | `400` Missing id, invalid status, or reaction limit reached; `402` Active reaction limit reached; `404` Reaction not found |

Body for `POST /strategy/reaction/llm`, `PUT /strategy/reaction/llm/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | The name of the strategy max 255 characters |
| `folder_id` | number | no | The folder id of the reaction |
| `webhook_id` | number | no | The id of the bot hook where signal will be sent (required if send_signal is true) |
| `data_webhook_id` | number | yes | The id of the data hook which will be used to get data |
| `llm_api_id` | number | yes | The main LLM Api key id used for the strategy |
| `fallback_api_id` | number | no | The fallback LLM Api key id used for the strategy if main is not available |
| `delay` | number | no | Set how often the reaction will check for new signals. eg. 10 means 10 in 1 second |
| `use_chart` | boolean | no | Set true if you want to send chart image with the strategy prompt |
| `chart_symbol` | string | no | The Tradingview symbol of the chart (required if use_chart is true) |
| `chart_interval` | string | no | The interval of the chart (required if use_chart is true) Values: `1`, `3`, `5`, `15`, `30`, `60`, `120`, `240`, `D`. |
| `chart_studies` | array<string> | no | The studies of the chart (optional if use_chart is true) 61 allowed values (see the LLM skill reference). Max 2 items. |
| `chart_data_range` | string | no | The data range of the chart (optional if use_chart is true) Values: `1D`, `5D`, `1M`, `3M`, `6M`, `YTD`, `12M`, `60M`, `ALL`. |
| `prompt` | string | yes | The prompt used for the strategy |
| `send_signal` | boolean | no | Set true if you want to send a signal to the bot hook |
| `signal_symbol` | string | no | The signal symbol or symbols of the strategy separated by comma |
| `send_email` | boolean | no | Set true if you want to send the LLM response to the user email |

Body for `POST /strategy/reaction/llm/duplicate`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | yes | Reaction ID to duplicate |

Body for `POST /strategy/reaction/llm/folder`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | Folder name (optional, auto-generated if not provided) |

Body for `PUT /strategy/reaction/llm/folder/{id}`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | no | New folder name (optional, auto-generated if not provided) |

Body for `PUT /strategy/reaction/llm/{id}/public`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `isPublic` | boolean | yes | Set true to make the strategy public |

Body for `PUT /strategy/reaction/llm/{id}/reset`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `resetTriggers` | boolean | yes | Set true to reset triggers |
| `resetStorage` | boolean | yes | Set true to reset storage |
| `resetResponse` | boolean | yes | Set true to reset response history |

Body for `PUT /strategy/reaction/llm/{id}/status`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `status` | string | yes | Values: `ACTIVE`, `INACTIVE`. |

## Folder routes (present in the official client, not yet on the docs pages)

The rendered API reference documents folders only for LLM sessions and both
reaction types. The official TypeScript client (generated from the current
OpenAPI spec) also exposes the same folder route set for these resources:

```text
/strategy/code/folder
/bot/signal/cex/folder
/bot/signal/dex/folder
/bot/signal/prediction/folder
```

Each supports:

| Method | Path suffix | Purpose |
| --- | --- | --- |
| GET | `/folder` | List folders |
| POST | `/folder` | Create a folder, body `{"name": "..."}` (optional; auto-named) |
| GET | `/folder/root` | List items that are not in a folder |
| GET | `/folder/{id}` | Get a folder with its items |
| PUT | `/folder/{id}` | Rename, body `{"name": "..."}` |
| DELETE | `/folder/{id}` | Delete; fails with `400` while the folder is not empty |

Move an item into a folder by sending `folder_id` in its create/update body.
Folder-scoped environment variables (`$.Env`) are configured in the dashboard;
no API route for environment variables is published.

The client also exposes `GET /webhook/bot/bot/signal/{id}/prediction?page=&limit=`
(prediction bots attached to a bot webhook), mirroring the documented `cex`
and `dex` variants.

## Things that are not REST endpoints

- **Sending a trading signal** is not a REST call. POST the signal JSON to the
  Bot Webhook URL (`https://hook.sigrex.io/bot/<hash>`), email it to
  `<hash>@sigrex.io`, use the browser extension, or use the MCP tool
  `send_bot_hook_order_message`.
- **Sending data to a Data Webhook** is a POST to
  `https://hook.sigrex.io/data/<hash>` with the `X-Key` header when protected.
- **Friends** (requests, accept, remove) have no published REST routes.
- **Environment variables**, the **GasTank**, **DEX contract deployment**,
  and the **Polymarket/Outcome wallet connection** flow are dashboard or
  on-chain operations.

## SDK method map

`@sigrex/client` (and `$.Http.createApiClient()` inside Code Strategies and
Code Reactions) groups the routes as:

```text
client.exchanges.{list(query?), listCex(), getDex(chain), listPrediction(), listWithExchangeRate()}
client.apiKeys.exchange.{list, create, postTest, status, delete, getSignalBot(id, {page, limit})}
client.apiKeys.llm.{listServices, getModels(serviceId), list, create, model(id, body), delete}
client.apiKeys.prediction.{list, create, postTest, status, delete, getSignalBot(id, {page, limit})}
client.webhooks.bot.{list, create, get, update, delete, status, shares, deleteShare,
                     listShared, getWithShared, getByShared,
                     listBotSignalCex, listBotSignalDex, listBotSignalPrediction}
client.webhooks.data.{list, create, get, update, delete, status, shares, deleteShare,
                      listShared, getWithShared, getByShared, llmReactions, codeReactions}
client.bots.{cex,dex,prediction}.{list, create, get, update, delete, status, getTotal, listFolder, postFolder, listFolderRoot, getFolder, updateFolder, deleteFolder}
client.bots.cex.duplicate(body) / client.bots.prediction.duplicate(body)
client.bots.prediction.getMarket(exchange, slug)
client.bots.dex.{getByChainAndAddress(chainId, address), getFactory(chainId, exchangeId)}
client.strategies.code.{list, create, get, update, delete, status, duplicate, reset, public, store, getTotal, listFolder, postFolder, listFolderRoot, getFolder, updateFolder, deleteFolder}
client.strategies.llmSessions.{list, create, get, update, delete, status, duplicate, reset, public, listFolder, postFolder, listFolderRoot, getFolder, updateFolder, deleteFolder}
client.strategies.reactions.code.{...same as code strategies}
client.strategies.reactions.llm.{...same as llm sessions}
```

Known client quirk: the "share webhook" method (`POST /webhook/bot/share/{id}`
and `/webhook/data/share/{id}`) was generated without a name. Call it through
the generic request method instead:

```ts
await client.request({
  method: "POST",
  path: `/api/v2/webhook/bot/share/${webhookId}`,
  body: { userId: "<friend-user-id>" },
});
```
