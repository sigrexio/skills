# Sigrex API Surface

This is a compact operation map for the API documented at
https://docs.sigrex.io/api-reference. Prefix every route with
`https://api.sigrex.io/api/v2`, sign the exact method/path/body, and use the
live page when a schema detail is important.

## Exchange Catalog

```text
GET /exchange
GET /exchange/cex
GET /exchange/dex/{chain}
GET /exchange/prediction
GET /exchange/with-exchange-rate
```

`/exchange` supports documented `enabled` and `chainId` filters. Catalog
objects expose `id`, `type`, `name`, `service`, `enabled`, `hasExchangeRate`,
and `extra`.

## API Key Connections

### LLM

```text
GET /api/llm/services
GET /api/llm/models/{serviceId}
GET /api/llm
POST /api/llm
PUT /api/llm/{id}/model
DELETE /api/llm/{id}
```

Create fields: `serviceId`, `modelId`, `apiKey`, optional `name`. Discover
service and model IDs before creation. Model changes are supported; key
replacement requires delete and recreate.

### Exchange

```text
GET /api/exchange
POST /api/exchange
POST /api/exchange/test
PUT /api/exchange/{id}/status
GET /api/exchange/bot/signal/{id}?page=&limit=
DELETE /api/exchange/{id}
```

Create/test fields: `exchangeId`, `publicKey`, `privateKey`, optional `name`
and `extra`.

### Prediction

```text
GET /api/prediction
POST /api/prediction
POST /api/prediction/test
GET /api/prediction/bot/signal/{id}?page=&limit=
PUT /api/prediction/{id}/status
DELETE /api/prediction/{id}
```

Create/test fields include `exchangeId`, `funderAddress`,
`walletPrivateKey`, and optional `name`. Treat `funderAddress` as a string
address even where the test schema says number.

## Webhooks

```text
GET/POST /webhook/bot
GET/PUT/DELETE /webhook/bot/{id}
PUT /webhook/bot/{id}/status
GET /webhook/bot/{id}/shares
POST /webhook/bot/share/{id}
DELETE /webhook/bot/share/{id}
GET /webhook/bot/shared
GET /webhook/bot/shared/with/{id}
GET /webhook/bot/shared/by/{id}

GET/POST /webhook/data
GET/PUT/DELETE /webhook/data/{id}
PUT /webhook/data/{id}/status
GET /webhook/data/{id}/shares
GET /webhook/data/{id}/llm-reactions?page=&limit=
GET /webhook/data/{id}/code-reactions?page=&limit=
POST /webhook/data/share/{id}
DELETE /webhook/data/share/{id}
GET /webhook/data/shared
GET /webhook/data/shared/with/{id}
GET /webhook/data/shared/by/{id}
```

Hook management fields are `name`, `description`, `is_safe`, and `has_key`.
Status is `ACTIVE` or `INACTIVE`. Sharing request bodies use `userId`.

## Signal Bots

### CEX

```text
GET/POST /bot/signal/cex
GET/PUT/DELETE /bot/signal/cex/{id}
GET /bot/signal/cex/total
PUT /bot/signal/cex/{id}/status
POST /bot/signal/cex/duplicate       {"id":"..."}
```

Creation requires `webhook_id`, `api_id`, `symbol`, and
`amount_from_signal`. Optional fields include `name`, `folder_id`,
`pair_base`, `pair_quote`, `amount`, `is_quote`, and `delay`.

### DEX

```text
GET/POST /bot/signal/dex
GET/PUT/DELETE /bot/signal/dex/{id}
GET /bot/signal/dex/total
GET /bot/signal/dex/{chainId}/{address}
GET /bot/signal/dex/factory/{chainId}/{exchangeId}
PUT /bot/signal/dex/{id}/status
```

Creation requires `webhook_id`, `factory_id`, `chain_id`, `symbol`, and
`address`. Update requires `webhook_id` and `symbol`; factory, chain, and
address are not update fields in the documented schema.

### Prediction

```text
GET/POST /bot/signal/prediction
GET/PUT/DELETE /bot/signal/prediction/{id}
GET /bot/signal/prediction/market/{slug}
GET /bot/signal/prediction/total
PUT /bot/signal/prediction/{id}/status
POST /bot/signal/prediction/duplicate       {"id":"..."}
```

Creation requires `webhook_id`, `api_id`, `slug_from_signal`, and
`amount_from_signal`. Fixed mode uses `url`; fixed amount uses `amount` in
USDC. Signal mode uses `slug` and `size` in the incoming payload.

## Code Strategy

```text
GET/POST /strategy/code
GET/PUT/DELETE /strategy/code/{id}
GET /strategy/code/total
POST /strategy/code/duplicate              {"id":"..."}
PUT /strategy/code/{id}/reset              {"resetTriggers":true,"resetStore":true}
PUT /strategy/code/{id}/status             {"status":"ACTIVE|INACTIVE"}
PUT /strategy/code/{id}/public             {"isPublic":true}
DELETE /strategy/code/{id}/store
```

Creation requires `webhook_id`, `symbol`, and `code`. Price fields are
`use_price`, `exchange_id`, and `price_symbol`; the exchange must expose a
rate.

## LLM Session

```text
GET/POST /strategy/llm-session
GET/PUT/DELETE /strategy/llm-session/{id}
GET /strategy/llm-session/total
POST /strategy/llm-session/duplicate             {"id":"..."}
PUT /strategy/llm-session/{id}/reset
PUT /strategy/llm-session/{id}/status            {"status":"ACTIVE|INACTIVE"}
PUT /strategy/llm-session/{id}/public            {"isPublic":true}
GET/POST /strategy/llm-session/folder
GET /strategy/llm-session/folder/root
GET/PUT/DELETE /strategy/llm-session/folder/{id}
```

Creation requires `llm_api_id`, `cron_interval`, and `prompt`. Optional
settings include fallback API, chart fields, signal webhook/symbols, email,
and folder. Reset requires `resetTriggers`, `resetStorage`, and
`resetResponse`.

## LLM Reaction

```text
GET/POST /strategy/reaction/llm
GET/PUT/DELETE /strategy/reaction/llm/{id}
GET /strategy/reaction/llm/total
POST /strategy/reaction/llm/duplicate             {"id":"..."}
PUT /strategy/reaction/llm/{id}/reset
PUT /strategy/reaction/llm/{id}/status            {"status":"ACTIVE|INACTIVE"}
PUT /strategy/reaction/llm/{id}/public            {"isPublic":true}
GET/POST /strategy/reaction/llm/folder
GET /strategy/reaction/llm/folder/root
GET/PUT/DELETE /strategy/reaction/llm/folder/{id}
```

Creation requires `data_webhook_id`, `llm_api_id`, and `prompt`. Optional
fields include bot `webhook_id`, fallback key, `delay`, chart settings,
signal settings, email, and folder.

## Code Reaction

```text
GET/POST /strategy/reaction/code
GET/PUT/DELETE /strategy/reaction/code/{id}
GET /strategy/reaction/code/total
POST /strategy/reaction/code/duplicate            {"id":"..."}
PUT /strategy/reaction/code/{id}/reset
PUT /strategy/reaction/code/{id}/status            {"status":"ACTIVE|INACTIVE"}
PUT /strategy/reaction/code/{id}/public            {"isPublic":true}
DELETE /strategy/reaction/code/{id}/store
GET/POST /strategy/reaction/code/folder
GET /strategy/reaction/code/folder/root
GET/PUT/DELETE /strategy/reaction/code/folder/{id}
```

Creation requires `webhook_id`, `data_webhook_id`, `symbol`, and `code`.
Optional fields include `delay`, price settings, and folder.

## Common API Rules

- Use `api-key`, `timestamp`, and `signature` headers.
- Sign GET/DELETE as `METHOD + PATH + TIMESTAMP`.
- Sign POST/PUT as `METHOD + PATH + JSON.stringify(body) + TIMESTAMP`.
- HMAC-SHA256 is lowercase hex; ML-DSA44 is Base64.
- Exact query signing behavior is not specified; verify against the SDK for
  signed query requests.
- Do not expose secrets in frontend code.
- `402` commonly means a plan/resource limit; `409` commonly means a resource
  is still referenced.
- Pagination schemas are incomplete in the published docs; do not assume a
  response shape beyond the endpoint's documented description.
