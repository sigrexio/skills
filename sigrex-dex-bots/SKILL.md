---
name: sigrex-dex-bots
description: Set up and operate Sigrex DEX Signal Bots that swap on Uniswap (Polygon or Arbitrum) from a per-bot smart contract, including BotFactory deployment, Start With / Use All / amount semantics, funding the bot contract, GasTank deposits and the 15% gas buffer, registering the contract via the API, contract addresses, ABIs and troubleshooting suspended bots. Use for any Sigrex DEX bot, Uniswap automation, GasTank or Sigrex smart-contract question.
metadata:
  author: sigrex
  version: "2.0"
---

# Sigrex DEX Signal Bots

A DEX Signal Bot is a **smart contract owned by the user** that holds the
tokens it trades. When its Bot Webhook receives a matching signal, a Sigrex
executor calls the contract's `executeSwap(side)`, which swaps on Uniswap.
Gas for that call is paid from the user's **GasTank** balance. These are
on-chain actions with real funds: never guess an address, chain, decimals or
enum value, and verify everything on the block explorer before signing.

## Supported Networks And Addresses

DEX catalog entry: Uniswap, `exchangeId` `10`, spot only.

| Network | Chain ID | Native gas token | GasTank | BotFactory |
| --- | ---: | --- | --- | --- |
| Arbitrum One | `42161` | ETH | `0x3d152e7B21b91295a136CEB42bA5A0cB0d4d6c74` | `0xc44771aEedE1F80756874201C58b47e7ea49E174` |
| Polygon PoS | `137` | POL | `0x4B3632c58cAC8481a241b703c8784C836E023A7D` | `0x3d152e7B21b91295a136CEB42bA5A0cB0d4d6c74` |

The same address `0x3d15...6c74` is the GasTank on Arbitrum but the
BotFactory on Polygon: always key contracts by `(chainId, address)`.
Re-check https://docs.sigrex.io/dex-signal-bot/deployment-addresses.md and
the explorer (arbiscan.io / polygonscan.com) before any transaction.

## How It Works

1. **Deploy:** in the Sigrex dashboard the user picks chain + Uniswap, base
   and quote token addresses, Start With, amount / Use All. Their wallet
   signs `BotFactory.createBot(...)`, which deploys a SignalBot contract owned
   by them.
2. **Fund the bot:** send the starting token to the **bot contract address**
   right after creation.
3. **Fund gas:** deposit native token into the chain's **GasTank**.
4. **Register:** the bot is stored in Sigrex with its webhook and symbol
   (dashboard, or `POST /bot/signal/dex` with the contract address).
5. **Execute:** signals with the bot's `symbol` make the executor call
   `executeSwap`. Cost = measured gas x gas price x 1.15, burned from the
   owner's GasTank balance. If the balance is too low, the transaction
   reverts and the **bot is automatically suspended**.

Manual alternative: the user can trigger the swap from their own wallet
(e.g. MetaMask). Then the wallet pays gas directly, the GasTank is not used,
and no 15% buffer is burned.

## Bot Strategy Settings (on-chain)

| Setting | Meaning |
| --- | --- |
| Base token | ERC-20 being bought/sold (e.g. WETH) |
| Quote token | ERC-20 paid/received (e.g. USDC) |
| **Start With = BUY** | First trade buys base with quote. Fund the bot with the **quote** token; amount is in quote units |
| **Start With = SELL** | First trade sells base for quote. Fund the bot with the **base** token; amount is in base units |
| **Amount** | Fixed amount of the starting token per trade. If the balance falls below it (e.g. after a loss), the swap does not happen |
| **Use All** | Trade 100% of the available balance each time; trades shrink after losses, never stall |

These live in the contract (`setStrategy` / `getStrategy`, struct
`{useAll, amount, token0, token1, startWith}`), not in the REST bot. On-chain
amounts are integers in the token's smallest unit (USDC has 6 decimals, WETH
18); the dashboard converts for you. Deposits to and withdrawals from the
bot's token balance are possible at any time from the dashboard.

## Register Or Manage Via API (prefix `/api/v2`)

Find the factory record first, then register the deployed contract:

```text
GET /exchange/dex/{chainId}                          DEX exchanges on a chain
GET /bot/signal/dex/factory/{chainId}/{exchangeId}   e.g. /bot/signal/dex/factory/42161/10 -> factory_id
```

```json
POST /api/v2/bot/signal/dex
{
  "name": "WETH-USDC arb",
  "webhook_id": 101,
  "factory_id": 3,
  "chain_id": 42161,
  "address": "0xYourDeployedSignalBotContract",
  "symbol": "WETHUSDC",
  "delay": 10
}
```

| Field | Required | Notes |
| --- | --- | --- |
| `webhook_id` | yes | Bot Webhook to listen to |
| `factory_id` | yes | From the factory lookup above |
| `chain_id` | yes | `42161` or `137` |
| `address` | yes | Deployed SignalBot contract; invalid addresses return `400` |
| `symbol` | yes | Label used to match signals, e.g. `WETHUSDC`; signals must use the same string |
| `delay` | no | Frequency limit (same meaning as on CEX bots) |
| `name`, `folder_id` | no | |

Updates (`PUT /bot/signal/dex/{id}`) accept only `webhook_id` (required),
`symbol` (required), `name`, `folder_id`, `delay`. The chain, factory and
address are fixed. To change tokens, amount or Use All, change the contract
strategy from the dashboard.

```text
GET  /bot/signal/dex                 GET /bot/signal/dex/{id}          GET /bot/signal/dex/total
GET  /bot/signal/dex/{chainId}/{address}                             look up by contract
PUT  /bot/signal/dex/{id}/status     {"status":"ACTIVE"|"INACTIVE"}  (402 = DEX bot limit)
DELETE /bot/signal/dex/{id}
GET|POST /bot/signal/dex/folder, GET /bot/signal/dex/folder/root, GET|PUT|DELETE /bot/signal/dex/folder/{id}
```

There is no DEX duplicate endpoint, because each bot is its own contract.

## Signals

DEX bots use the standard bot payload: `{"symbol":"WETHUSDC","side":"BUY"}`.
The swap amount comes from the contract strategy (fixed or Use All). Spot
only: `BUY` swaps quote to base, `SELL` swaps base to quote. Test with
`flag: "TEST"` before live signals.

## GasTank (user operations)

| Function | Use |
| --- | --- |
| `deposit()` payable | Add native gas token to your balance |
| `withdraw(uint256 amount)` | Withdraw unused balance (wei); funds are never locked |
| `getGas() view` | Balance of `msg.sender` |
| `getAddressGas(address) view` | Balance of any owner address |
| `getFee() view` | Current fee parameter |

`burn`, `transfer`, `addFacility`, `addPipe`, `setFee`, `pause` and
ownership functions are privileged (owner/executor); users never call them.
Keep a healthy balance and watch it in the dashboard; a dry tank suspends
bots.

## Contract Safety Notes

- Full function tables: `references/contracts.md`. ABIs:
  https://github.com/sigrexio/ABI.
- `createBot(bytes uid, address token0, address token1, uint256 amount,
  bool useAll, uint8 startWith)`: the `uid` convention and the numeric
  values of the `OrderSide` enum (`startWith`, `executeSwap(side)`) are **not
  published**. Do not hand-craft these calls; use the dashboard.
- The bot contract uses role-based access control; only authorized accounts
  can call `executeSwap`, `setStrategy`, `withdraw`, `pause`.
- Not documented: slippage limits, MEV protection, price limits, pool fee
  tier selection, approval handling, retry behaviour. Treat them as open
  risks, prefer liquid pairs, and size small first.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Bot suspended | GasTank balance too low on that chain; top up, then reactivate |
| Signal logged, no swap | Symbol mismatch; bot inactive; balance below the fixed amount (Use All off); `TEST` flag |
| `SwapFailed` event on-chain | Read the reason string; often liquidity/route or balance |
| `400 invalid contract address` on register | Wrong chain ID for that address, or not a Sigrex SignalBot |
| Wrong token sold first | Start With and funding token do not match |

## Canonical Docs

- https://docs.sigrex.io/dex-signal-bot/creating-a-dex-signal-bot.md
- https://docs.sigrex.io/dex-signal-bot/gas-tank.md
- https://docs.sigrex.io/dex-signal-bot/deployment-addresses.md
- https://docs.sigrex.io/dex-signal-bot/contract-abi.md
- https://docs.sigrex.io/api-reference/reference/signal-bots/dex-bot.md
- https://github.com/sigrexio/ABI
