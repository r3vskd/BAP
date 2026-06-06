import asyncio
import json
from pathlib import Path
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair


async def main():
    client = AsyncClient("https://api.devnet.solana.com")

    keypair_path = Path.home() / ".config" / "solana" / "id.json"
    with open(keypair_path, "r") as f:
        keypair_data = json.load(f)
    keypair = Keypair.from_bytes(bytes(keypair_data))

    print(f"Connected to devnet: {await client.is_connected()}")
    print(f"Public key: {keypair.pubkey()}")

    balance = await client.get_balance(keypair.pubkey())
    print(f"Balance: {balance.value / 1e9} SOL")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
