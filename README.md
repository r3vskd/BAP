# BAP

BAP is a cryptocurrency token built on the Solana blockchain using the SPL Token standard.

## Prerequisites

- Python 3.10+
- [Solana CLI](https://docs.solanalabs.com/cli/install) installed
- A Solana wallet keypair (`solana-keygen new`)
- Devnet SOL for testing (`solana airdrop 2` after setting `solana config set --url devnet`)

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# 1. Create the BAP token mint
python -m app.cli init

# 2. Set token metadata (name, symbol, logo)
python -m app.cli metadata --uri "https://your-metadata-url.com/bap.json"

# 3. Mint tokens to your wallet
python -m app.cli mint 1000000

# 4. Check your balance
python -m app.cli balance

# 5. Transfer tokens
python -m app.cli transfer 100 <recipient-wallet-address>
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `init` | Create BAP token mint on Solana |
| `metadata --uri <url>` | Set token name, symbol, and logo URI |
| `mint <amount> [--to <addr>]` | Mint BAP tokens (default: your wallet) |
| `transfer <amount> <to>` | Transfer BAP to another wallet |
| `burn <amount>` | Burn (destroy) BAP tokens |
| `balance [--address <addr>]` | Check BAP balance |
| `supply` | Check total BAP supply |
| `info` | Show mint details (supply, authorities) |
| `revoke-freeze` | Permanently remove freeze authority |
| `revoke-mint` | Permanently remove mint authority (caps supply) |
| `make-immutable` | Permanently lock token metadata |

### Global Flags

```
--cluster devnet|mainnet   Solana cluster (default: devnet)
--wallet <path>            Override wallet keypair path
--mint <address>           Override mint address
```

## Publishing to Mainnet

Once you're satisfied on devnet, switch to mainnet:

```bash
# Set Solana CLI to mainnet
solana config set --url mainnet-beta

# Create mint on mainnet
python -m app.cli --cluster mainnet init

# Set metadata
python -m app.cli --cluster mainnet metadata --uri "https://your-metadata-url.com/bap.json"

# Mint initial supply
python -m app.cli --cluster mainnet mint 1000000

# Lock everything down (PERMANENT)
python -m app.cli --cluster mainnet revoke-freeze --yes
python -m app.cli --cluster mainnet make-immutable --yes
```

## Zero Maintenance

After running the setup commands, BAP lives on Solana permanently:

- **Token transfers** work in any Solana wallet (Phantom, Solflare, Backpack)
- **Trading** works on any Solana DEX (Jupiter, Raydium, Orca)
- **Balance queries** work on any Solana explorer (Solscan, SolanaFM)

This CLI is a convenience tool. If it ever stops working, you can manage BAP using:
- `solana` CLI (`spl-token` commands)
- Any Solana wallet
- Any DEX

## Token Details

| Property | Value |
|----------|-------|
| Standard | SPL Token |
| Decimals | 9 |
| Network | Solana |

## Architecture

```
Solana Blockchain
├── SPL Token Program (standard) ← handles mint/transfer/burn
├── BAP Mint Account ← your token's data
├── Token Accounts ← who holds how much BAP
└── Metaplex Metadata ← name, symbol, logo

Your Machine
├── app/backend.py ← core token operations
├── app/cli.py ← command-line interface
└── app/config.py ← configuration
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `BAP_WALLET` | Path to wallet keypair JSON (overrides default) |

## Running Tests

Tests run against devnet and require a funded wallet:

```bash
solana config set --url devnet
solana airdrop 2
python tests/test_token.py
```

## License

Apache 2.0
