---
name: sigrex-dex-bots
description: Configure Sigrex Uniswap DEX Signal Bots, GasTank funding, EVM deployment addresses, and contract ABI interactions on Polygon or Arbitrum. Use when deploying, funding, registering, or troubleshooting Sigrex DEX bots and smart contracts.
metadata:
  author: sigrex
  version: "1.0"
---

# Sigrex DEX Signal Bots

DEX bots execute on-chain and can move funds. Never guess an address, chain,
token decimal, enum value, or privileged role. Verify every deployment against
the live docs and block explorer before signing a transaction.

## Supported Networks

The documented DEX integration is Uniswap spot on Polygon and Arbitrum. Key
the deployment by `(chainId, address)` because the same address may appear on
different chains.

| Network | Chain ID | GasTank | BotFactory |
| --- | ---: | --- | --- |
| Arbitrum One | `42161` | `0x3d152e7B21b91295a136CEB42bA5A0cB0d4d6c74` | `0xc44771aEedE1F80756874201C58b47e7ea49E174` |
| Polygon | `137` | `0x4B3632c58cAC8481a241b703c8784C836E023A7D` | `0x3d152e7B21b91295a136CEB42bA5A0cB0d4d6c74` |

These values are documentation snapshots. Re-check:
https://docs.sigrex.io/dex-signal-bot/deployment-addresses.md and the linked
explorer before transacting.

## Deployment Workflow

1. Select the chain and token pair; verify token addresses and decimals.
2. Use the chain's BotFactory to create the bot with token addresses, starting
   amount, `useAll`, and starting side.
3. Record the resulting bot contract address and transaction.
4. Fund the bot with the correct starting token: quote token for `BUY`, base
   token for `SELL`.
5. Deposit native gas into the chain's GasTank for automated execution.
6. Register the contract with the DEX Signal Bot API.
7. Attach a Bot Webhook, keep the bot inactive, and test before activation.

## DEX API Configuration

Create under `/api/v2/bot/signal/dex`:

```json
{
  "name": "WETH-USDC bot",
  "webhook_id": 123,
  "factory_id": 10,
  "chain_id": 42161,
  "address": "0xDeployedBotContract",
  "symbol": "WETHUSDC",
  "delay": 10
}
```

Required fields are `webhook_id`, `factory_id`, `chain_id`, `symbol`, and
`address`. Optional fields include `name`, `folder_id`, and `delay`.

```text
GET/POST /bot/signal/dex
GET/PUT/DELETE /bot/signal/dex/{id}
GET /bot/signal/dex/total
GET /bot/signal/dex/{chainId}/{address}
GET /bot/signal/dex/factory/{chainId}/{exchangeId}
PUT /bot/signal/dex/{id}/status
```

The REST schema does not configure token addresses, amount, `useAll`, or
`startWith`; those belong to the on-chain strategy.

## GasTank

GasTank is chain-specific and non-custodial. Unused deposits can be withdrawn.
Automated execution charges measured gas plus a documented 15% buffer. If the
balance is insufficient, the transaction reverts and the DEX bot is suspended.
Manual wallet execution pays gas directly and bypasses GasTank.

The documented ABI includes:

```solidity
deposit() payable
withdraw(uint256 amount)
getGas() view returns (uint256)
getAddressGas(address account) view returns (uint256)
getFee() view returns (uint256)
burn(address from, uint256 amount, bytes uid)
```

The current ABI requires all three `burn` arguments; do not use simplified
two-argument examples without checking the ABI version.

## Contract ABI Safety

BotFactory exposes `createBot(bytes uid,address token0,address token1,uint256
amount,bool useAll,uint8 startWith)` and bot enumeration/deletion methods.
SignalBot exposes `executeSwap(uint8 side)`, `setStrategy(...)`,
`getStrategy()`, and token `withdraw(...)`. `startWith` and `side` encode an
enum, but the docs do not publish the numeric BUY/SELL mapping or UID
convention. Never guess them or call privileged methods from an untrusted
client.

The docs do not specify slippage, approvals, MEV protection, price limits,
token decimals, or retry behavior. Treat those as unresolved risks.

## Canonical Docs

- https://docs.sigrex.io/dex-signal-bot/creating-a-dex-signal-bot.md
- https://docs.sigrex.io/dex-signal-bot/gas-tank.md
- https://docs.sigrex.io/dex-signal-bot/deployment-addresses.md
- https://docs.sigrex.io/dex-signal-bot/contract-abi.md
- https://docs.sigrex.io/dex-signal-bot/contract-abi/gastank-abi.md
- https://docs.sigrex.io/dex-signal-bot/contract-abi/botfactory-abi.md
- https://docs.sigrex.io/dex-signal-bot/contract-abi/signalbot-abi.md
- https://github.com/sigrexio/ABI
