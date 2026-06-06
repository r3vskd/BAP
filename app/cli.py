import argparse
import asyncio
import sys
from typing import Optional
from solders.pubkey import Pubkey
from app import backend
from app.config import get_mint_address, load_keypair

def get_mint(mint_override: Optional[str]) -> Pubkey:
    addr = mint_override or get_mint_address()
    if addr is None:
        print("Error: No mint address found. Run 'init' first or pass --mint <address>")
        sys.exit(1)
    return Pubkey.from_string(addr)

async def cmd_init(args):
    wallet = load_keypair(args.wallet)
    client = await backend.connect(args.cluster)
    try:
        print(f"Creating BAP mint on {args.cluster}...")
        mint = await backend.create_mint(client, wallet)
        print(f"Mint created: {mint}")
        print(f"Saved to .bap.json")
    finally:
        await client.close()

async def cmd_metadata(args):
    wallet = load_keypair(args.wallet)
    client = await backend.connect(args.cluster)
    mint = get_mint(args.mint)
    try:
        print(f"Setting metadata for {mint}...")
        await backend.set_metadata(client, wallet, mint, uri=args.uri)
        print("Metadata set successfully")
    finally:
        await client.close()

async def cmd_mint(args):
    wallet = load_keypair(args.wallet)
    client = await backend.connect(args.cluster)
    mint = get_mint(args.mint)
    dest = Pubkey.from_string(args.to) if args.to else None
    try:
        print(f"Minting {args.amount} BAP...")
        ata = await backend.mint_tokens(client, wallet, mint, args.amount, dest)
        print(f"Minted {args.amount} BAP to {ata}")
    finally:
        await client.close()

async def cmd_transfer(args):
    wallet = load_keypair(args.wallet)
    client = await backend.connect(args.cluster)
    mint = get_mint(args.mint)
    dest_owner = Pubkey.from_string(args.to)
    try:
        print(f"Transferring {args.amount} BAP to {dest_owner}...")
        ata = await backend.transfer_tokens(client, wallet, mint, args.amount, dest_owner)
        print(f"Transferred {args.amount} BAP to {ata}")
    finally:
        await client.close()

async def cmd_burn(args):
    wallet = load_keypair(args.wallet)
    client = await backend.connect(args.cluster)
    mint = get_mint(args.mint)
    try:
        print(f"Burning {args.amount} BAP...")
        await backend.burn_tokens(client, wallet, mint, args.amount)
        print(f"Burned {args.amount} BAP")
    finally:
        await client.close()

async def cmd_balance(args):
    client = await backend.connect(args.cluster)
    mint = get_mint(args.mint)
    address = Pubkey.from_string(args.address) if args.address else None
    try:
        if address is None:
            wallet = load_keypair(args.wallet)
            address = wallet.pubkey()
        balance = await backend.get_balance(client, mint, address)
        print(f"Balance: {balance} BAP")
    finally:
        await client.close()

async def cmd_supply(args):
    client = await backend.connect(args.cluster)
    mint = get_mint(args.mint)
    try:
        supply = await backend.get_supply(client, mint)
        print(f"Total supply: {supply} BAP")
    finally:
        await client.close()

async def cmd_info(args):
    client = await backend.connect(args.cluster)
    mint = get_mint(args.mint)
    try:
        info = await backend.get_mint_info(client, mint)
        print(f"Mint address: {info.address}")
        print(f"Decimals: {info.decimals}")
        print(f"Supply: {info.supply} BAP")
        print(f"Mint authority: {info.mint_authority or 'Revoked'}")
        print(f"Freeze authority: {info.freeze_authority or 'Revoked'}")
    finally:
        await client.close()

async def cmd_revoke_freeze(args):
    if not args.yes:
        print("WARNING: This action is PERMANENT and IRREVERSIBLE.")
        print("After revoking freeze authority, no one can freeze BAP token accounts.")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Cancelled.")
            return

    wallet = load_keypair(args.wallet)
    client = await backend.connect(args.cluster)
    mint = get_mint(args.mint)
    try:
        print("Revoking freeze authority...")
        await backend.revoke_freeze_authority(client, wallet, mint)
        print("Freeze authority revoked permanently")
    finally:
        await client.close()

async def cmd_revoke_mint(args):
    if not args.yes:
        print("WARNING: This action is PERMANENT and IRREVERSIBLE.")
        print("After revoking mint authority, no more BAP tokens can ever be created.")
        print("The total supply will be permanently fixed.")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Cancelled.")
            return

    wallet = load_keypair(args.wallet)
    client = await backend.connect(args.cluster)
    mint = get_mint(args.mint)
    try:
        print("Revoking mint authority...")
        await backend.revoke_mint_authority(client, wallet, mint)
        print("Mint authority revoked permanently. Supply is now fixed.")
    finally:
        await client.close()

async def cmd_make_immutable(args):
    if not args.yes:
        print("WARNING: This action is PERMANENT and IRREVERSIBLE.")
        print("After making metadata immutable, the token name, symbol, and logo can never be changed.")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Cancelled.")
            return

    wallet = load_keypair(args.wallet)
    client = await backend.connect(args.cluster)
    mint = get_mint(args.mint)
    try:
        print("Making metadata immutable...")
        await backend.make_metadata_immutable(client, wallet, mint)
        print("Metadata is now permanently immutable")
    finally:
        await client.close()

def main():
    parser = argparse.ArgumentParser(
        prog="bap",
        description="BAP Token Management CLI",
    )
    parser.add_argument(
        "--cluster",
        choices=["devnet", "mainnet"],
        default="devnet",
        help="Solana cluster (default: devnet)",
    )
    parser.add_argument(
        "--wallet",
        default=None,
        help="Path to wallet keypair JSON (default: ~/.config/solana/id.json or BAP_WALLET env)",
    )
    parser.add_argument(
        "--mint",
        default=None,
        help="Override mint address (default: read from .bap.json)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("init", help="Create BAP token mint")

    metadata_parser = subparsers.add_parser("metadata", help="Set token metadata")
    metadata_parser.add_argument("--uri", default="", help="Metadata JSON URI (e.g., Arweave/IPFS link)")

    mint_parser = subparsers.add_parser("mint", help="Mint BAP tokens")
    mint_parser.add_argument("amount", type=float, help="Amount of BAP to mint")
    mint_parser.add_argument("--to", default=None, help="Destination wallet (default: your wallet)")

    transfer_parser = subparsers.add_parser("transfer", help="Transfer BAP tokens")
    transfer_parser.add_argument("amount", type=float, help="Amount of BAP to transfer")
    transfer_parser.add_argument("to", help="Destination wallet address")

    burn_parser = subparsers.add_parser("burn", help="Burn BAP tokens")
    burn_parser.add_argument("amount", type=float, help="Amount of BAP to burn")

    balance_parser = subparsers.add_parser("balance", help="Check BAP balance")
    balance_parser.add_argument("--address", default=None, help="Wallet address (default: your wallet)")

    subparsers.add_parser("supply", help="Check total BAP supply")
    subparsers.add_parser("info", help="Show BAP mint info")

    revoke_freeze_parser = subparsers.add_parser("revoke-freeze", help="Revoke freeze authority (permanent)")
    revoke_freeze_parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    revoke_mint_parser = subparsers.add_parser("revoke-mint", help="Revoke mint authority (permanent)")
    revoke_mint_parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    immutable_parser = subparsers.add_parser("make-immutable", help="Make metadata immutable (permanent)")
    immutable_parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    commands = {
        "init": cmd_init,
        "metadata": cmd_metadata,
        "mint": cmd_mint,
        "transfer": cmd_transfer,
        "burn": cmd_burn,
        "balance": cmd_balance,
        "supply": cmd_supply,
        "info": cmd_info,
        "revoke-freeze": cmd_revoke_freeze,
        "revoke-mint": cmd_revoke_mint,
        "make-immutable": cmd_make_immutable,
    }

    try:
        asyncio.run(commands[args.command](args))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()