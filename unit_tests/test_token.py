import asyncio
import json
import sys
from pathlib import Path
from solders.keypair import Keypair
from solders.pubkey import Pubkey

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import backend
from app.config import TOKEN_DECIMALS

def load_test_wallet() -> Keypair:
    keypair_path = Path.home() / ".config" / "solana" / "id.json"
    if not keypair_path.exists():
        raise FileNotFoundError(
            f"Test wallet not found at {keypair_path}. "
            "Generate one with: solana-keygen new"
        )
    with open(keypair_path, "r") as f:
        data = json.load(f)
    return Keypair.from_bytes(bytes(data))

async def test_create_mint():
    print("Test: create_mint...")
    wallet = load_test_wallet()
    client = await backend.connect("devnet")
    try:
        mint = await backend.create_mint(client, wallet)
        assert mint is not None
        info = await backend.get_mint_info(client, mint)
        assert info.decimals == TOKEN_DECIMALS
        assert info.mint_authority == str(wallet.pubkey())
        assert info.freeze_authority == str(wallet.pubkey())
        assert info.supply == 0.0
        print(f"  PASS - Mint: {mint}")
        return mint
    finally:
        await client.close()

async def test_mint_tokens(mint: Pubkey):
    print("Test: mint_tokens...")
    wallet = load_test_wallet()
    client = await backend.connect("devnet")
    try:
        ata = await backend.create_token_account(client, wallet, mint)
        await backend.mint_tokens(client, wallet, mint, 1000.0)
        balance = await backend.get_balance(client, mint, wallet.pubkey())
        assert balance == 1000.0, f"Expected 1000.0, got {balance}"
        print(f"  PASS - Balance: {balance} BAP")
    finally:
        await client.close()

async def test_transfer_tokens(mint: Pubkey):
    print("Test: transfer_tokens...")
    wallet = load_test_wallet()
    dest_wallet = Keypair()
    client = await backend.connect("devnet")
    try:
        airdrop = await client.request_airdrop(dest_wallet.pubkey(), 1_000_000_000)
        await client.confirm_transaction(airdrop.value)
        await asyncio.sleep(2)

        await backend.transfer_tokens(client, wallet, mint, 100.0, dest_wallet.pubkey())

        dest_balance = await backend.get_balance(client, mint, dest_wallet.pubkey())
        assert dest_balance == 100.0, f"Expected 100.0, got {dest_balance}"

        sender_balance = await backend.get_balance(client, mint, wallet.pubkey())
        assert sender_balance == 900.0, f"Expected 900.0, got {sender_balance}"
        print(f"  PASS - Sender: {sender_balance}, Dest: {dest_balance}")
    finally:
        await client.close()

async def test_burn_tokens(mint: Pubkey):
    print("Test: burn_tokens...")
    wallet = load_test_wallet()
    client = await backend.connect("devnet")
    try:
        before = await backend.get_balance(client, mint, wallet.pubkey())
        await backend.burn_tokens(client, wallet, mint, 50.0)
        after = await backend.get_balance(client, mint, wallet.pubkey())
        assert after == before - 50.0, f"Expected {before - 50.0}, got {after}"
        print(f"  PASS - Before: {before}, After: {after}")
    finally:
        await client.close()

async def test_get_supply(mint: Pubkey):
    print("Test: get_supply...")
    client = await backend.connect("devnet")
    try:
        supply = await backend.get_supply(client, mint)
        assert supply == 950.0, f"Expected 950.0, got {supply}"
        print(f"  PASS - Supply: {supply} BAP")
    finally:
        await client.close()

async def test_set_metadata(mint: Pubkey):
    print("Test: set_metadata...")
    wallet = load_test_wallet()
    client = await backend.connect("devnet")
    try:
        await backend.set_metadata(client, wallet, mint, uri="https://example.com/bap.json")
        print("  PASS - Metadata set")
    finally:
        await client.close()

async def test_revoke_freeze(mint: Pubkey):
    print("Test: revoke_freeze_authority...")
    wallet = load_test_wallet()
    client = await backend.connect("devnet")
    try:
        await backend.revoke_freeze_authority(client, wallet, mint)
        info = await backend.get_mint_info(client, mint)
        assert info.freeze_authority is None, f"Expected None, got {info.freeze_authority}"
        print("  PASS - Freeze authority revoked")
    finally:
        await client.close()

async def test_get_mint_info(mint: Pubkey):
    print("Test: get_mint_info...")
    client = await backend.connect("devnet")
    try:
        info = await backend.get_mint_info(client, mint)
        assert info.address == str(mint)
        assert info.decimals == TOKEN_DECIMALS
        print(f"  PASS - {info}")
    finally:
        await client.close()

async def run_all_tests():
    print("=" * 50)
    print("BAP Token Integration Tests (devnet)")
    print("=" * 50)

    try:
        mint = await test_create_mint()
        await test_mint_tokens(mint)
        await test_transfer_tokens(mint)
        await test_burn_tokens(mint)
        await test_get_supply(mint)
        await test_set_metadata(mint)
        await test_revoke_freeze(mint)
        await test_get_mint_info(mint)

        print("=" * 50)
        print("ALL TESTS PASSED")
        print("=" * 50)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_all_tests())