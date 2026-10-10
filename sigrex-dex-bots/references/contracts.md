# Sigrex DEX Contract Reference

Generated from the ABI files in https://github.com/sigrexio/ABI (formerly
`Towerflow/ABI`, which now redirects there). Deployment addresses are in
`SKILL.md`. Verify the ABI version on the block explorer before you encode
any call.

## Who Calls What

| Contract | User (owner wallet) | Sigrex executor / admin only |
| --- | --- | --- |
| GasTank | `deposit`, `withdraw`, `getGas`, `getAddressGas`, `getFee`, `paused` | `burn`, `transfer`, `addFacility`, `removeFacility`, `addPipe`, `removePipe`, `setFee`, `pause`, `unpause`, ownership functions |
| BotFactory | `createBot` (via the dashboard), `deleteBot` (own bots), read functions | `pause`, `unpause`, ownership functions |
| SignalBot | `getStrategy`, `getUid`, `withdraw(token, amount)` and `setStrategy(...)` as owner, read functions | `executeSwap(side)` for automated execution (owner wallet can also run it manually), role management |

Notes:

- `startWith` (BotFactory/SignalBot) and `side` (`executeSwap`, events) are a
  Solidity `enum Util.OrderSide` encoded as `uint8`. The numeric BUY/SELL
  mapping is **not published**; read it from a known bot with `getStrategy()`
  if you must, but prefer the dashboard.
- `uid` (`bytes`) is an identifier passed to `createBot`, stored in the bot
  (`getUid()`) and emitted in GasTank `Burn` events. Its format is not
  published. Do not invent one.
- `amount` values are in the token's smallest unit (respect `decimals`).
- GasTank defines `ContractsNotAllowed`; deposits from smart-contract wallets
  may revert, so fund it from a regular wallet (EOA).
- SignalBot emits `SwapSuccess(side, amountIn, amountOut)` and
  `SwapFailed(side, amountIn, reason)`; use them to audit executions on the
  explorer. GasTank emits `Burn(from, amount, executor, fee, uid)` for each
  gas charge.
- The 15% buffer is applied by the executor:
  `totalCost = ((startGas - gasleft()) * tx.gasprice * 115) / 100; gasTank.burn(owner, totalCost, uid);`

## GasTank

Constructor: `constructor(address owner)`

| Function | Mutability | Returns |
| --- | --- | --- |
| `addFacility(address addr)` | nonpayable | - |
| `addPipe(address addr)` | nonpayable | - |
| `burn(address from, uint256 amount, bytes uid)` | nonpayable | - |
| `deposit()` | payable | - |
| `getAddressGas(address addr)` | view | `uint256` |
| `getFacility()` | view | `address[]` |
| `getFee()` | view | `uint256` |
| `getGas()` | view | `uint256` |
| `getPipes()` | view | `address[]` |
| `owner()` | view | `address` |
| `pause()` | nonpayable | - |
| `paused()` | view | `bool` |
| `removeFacility(address addr)` | nonpayable | - |
| `removePipe(address addr)` | nonpayable | - |
| `renounceOwnership()` | nonpayable | - |
| `setFee(uint256 newFee)` | nonpayable | - |
| `transfer(address from, address to, uint256 amount)` | nonpayable | - |
| `transferOwnership(address newOwner)` | nonpayable | - |
| `unpause()` | nonpayable | - |
| `withdraw(uint256 amount)` | nonpayable | - |

Events: `Burn(address from, uint256 amount, address executor, uint256 fee, bytes uid)`; `Deposit(address user, uint256 amount)`; `FacilityAdded(address addr)`; `FacilityRemoved(address addr)`; `OwnershipTransferred(address previousOwner, address newOwner)`; `Paused(address account)`; `PipedAdded(address addr)`; `PipedRemoved(address addr)`; `Transfer(address from, address to, uint256 amount)`; `Unpaused(address account)`; `Withdraw(address user, uint256 amount)`

Errors: `ContractsNotAllowed`, `EnforcedPause`, `ExpectedPause`, `InsufficientBalance`, `NotAuthorized`, `OwnableInvalidOwner(address owner)`, `OwnableUnauthorizedAccount(address account)`, `ReentrancyGuardReentrantCall`, `TransferFailed`, `TransferNotAllowed`, `ZeroAddressNotAllowed`, `ZeroAmount`

## BotFactory

Constructor: `constructor(address _gasTank, address _router, address _quoter)`

| Function | Mutability | Returns |
| --- | --- | --- |
| `createBot(bytes uid, address token0, address token1, uint256 amount, bool useAll, uint8 startWith)` | nonpayable | `address` |
| `deleteBot(address botAddress)` | nonpayable | - |
| `getBot(uint256 index)` | view | `address` |
| `getBotCount()` | view | `uint256` |
| `getBotIndex(address botAddress)` | view | `uint256` |
| `getBots()` | view | `address[]` |
| `getBotsPaginated(uint256 start, uint256 length)` | view | `address[]` |
| `getGasTank()` | view | `address` |
| `getLastBot()` | view | `address` |
| `owner()` | view | `address` |
| `pause()` | nonpayable | - |
| `paused()` | view | `bool` |
| `renounceOwnership()` | nonpayable | - |
| `transferOwnership(address newOwner)` | nonpayable | - |
| `unpause()` | nonpayable | - |

Events: `BotCreated(address user, address bot)`; `BotDeleted(address user, address bot)`; `OwnershipTransferred(address previousOwner, address newOwner)`; `Paused(address account)`; `Unpaused(address account)`

Errors: `BotNotFound(address bot)`, `EnforcedPause`, `ExpectedPause`, `IndexOutOfBounds(uint256 index)`, `InsufficientBalance(address sender, uint256 balance, uint256 needed)`, `OwnableInvalidOwner(address owner)`, `OwnableUnauthorizedAccount(address account)`, `ReentrancyGuardReentrantCall`, `SafeERC20FailedOperation(address token)`

## SignalBot

Constructor: `constructor(address _owner, bytes _uid, (bool useAll, uint256 amount, address token0, address token1, uint8 startWith) _strategy, address _router, address _quoter)`

| Function | Mutability | Returns |
| --- | --- | --- |
| `DEFAULT_ADMIN_ROLE()` | view | `bytes32` |
| `executeSwap(uint8 side)` | nonpayable | - |
| `getFactory()` | view | `address` |
| `getGasTank()` | view | `address` |
| `getRoleAdmin(bytes32 role)` | view | `bytes32` |
| `getStrategy()` | view | `(bool useAll, uint256 amount, address token0, address token1, uint8 startWith)` |
| `getUid()` | view | `bytes` |
| `grantRole(bytes32 role, address account)` | nonpayable | - |
| `hasRole(bytes32 role, address account)` | view | `bool` |
| `pause()` | nonpayable | - |
| `paused()` | view | `bool` |
| `renounceRole(bytes32 role, address callerConfirmation)` | nonpayable | - |
| `revokeRole(bytes32 role, address account)` | nonpayable | - |
| `setStrategy(uint8 _startWith, bool _useAll, uint256 _amount, address _token0, address _token1)` | nonpayable | - |
| `supportsInterface(bytes4 interfaceId)` | view | `bool` |
| `unpause()` | nonpayable | - |
| `withdraw(address _token, uint256 _amount)` | nonpayable | - |

Events: `Paused(address account)`; `RoleAdminChanged(bytes32 role, bytes32 previousAdminRole, bytes32 newAdminRole)`; `RoleGranted(bytes32 role, address account, address sender)`; `RoleRevoked(bytes32 role, address account, address sender)`; `StrategyChanged((bool useAll, uint256 amount, address token0, address token1, uint8 startWith) strategy)`; `SwapFailed(uint8 side, uint256 amountIn, string reason)`; `SwapSuccess(uint8 side, uint256 amountIn, uint256 amountOut)`; `Unpaused(address account)`

Errors: `AccessControlBadConfirmation`, `AccessControlUnauthorizedAccount(address account, bytes32 neededRole)`, `EnforcedPause`, `ExpectedPause`, `InsufficientFunds`, `ReentrancyGuardReentrantCall`, `SafeERC20FailedOperation(address token)`, `TokenNotIncluded(address token)`, `Unauthorized`, `ZeroAmount`

