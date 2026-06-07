import json
import os
from pathlib import Path
from typing import Optional
from solders.keypair import Keypair

TOKEN_NAME = "BAP"
TOKEN_SYMBOL = "BAP"
TOKEN_DECIMALS = 9

RPC_URLS = [ # Lista de URLs de Solana devnet para intentar. Si uno falla, se usa el siguiente.
    "https://api.devnet.solana.com",
    "https://devnet.helius-rpc.com/?api-key=test",
]

KEYPAIR_PATH = os.environ.get( # Ruta del archivo de la wallet de BAP. Si no se proporciona, se usa la ruta por defecto.
    "BAP_WALLET",
    str(Path.home() / ".config" / "solana" / "id.json"),
)

MINT_FILE = Path(__file__).resolve().parent.parent / ".bap.json" # Ruta del archivo de la mint de BAP.

METAPLEX_PROGRAM_ID = "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s" # ID del programa Metaplex.

def load_keypair(path: Optional[str] = None) -> Keypair: # Carga la wallet de BAP. Si no se proporciona, se usa la ruta por defecto.
    kp_path = path or KEYPAIR_PATH
    if not Path(kp_path).exists():
        raise FileNotFoundError(
            f"Keypair not found at {kp_path}. "
            "Generate one with: solana-keygen new"
        )
    with open(kp_path, "r") as f:
        data = json.load(f)
    return Keypair.from_bytes(bytes(data))

def save_mint_address(address: str) -> None: # Guarda la mint de BAP.
    with open(MINT_FILE, "w") as f:
        json.dump({"mint": address}, f, indent=2)

def get_mint_address() -> Optional[str]: # Obtiene la mint de BAP.
    if not MINT_FILE.exists():
        return None
    with open(MINT_FILE, "r") as f:
        data = json.load(f)
    return data.get("mint")