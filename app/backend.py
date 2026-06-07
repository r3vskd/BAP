import struct
from dataclasses import dataclass
from typing import Optional
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.system_program import create_account, CreateAccountParams
from solders.transaction import Transaction
from spl.token.constants import MINT_LEN, TOKEN_PROGRAM_ID
from spl.token.instructions import (
    burn,
    BurnParams,
    create_associated_token_account,
    get_associated_token_address,
    initialize_mint,
    InitializeMintParams,
    mint_to,
    MintToParams,
    set_authority,
    SetAuthorityParams,
    transfer,
    TransferParams,
)

from app.config import (
    METAPLEX_PROGRAM_ID,
    RPC_URLS,
    TOKEN_DECIMALS,
    TOKEN_NAME,
    TOKEN_SYMBOL,
    get_mint_address,
    save_mint_address,
)

@dataclass
class MintInfo:
    address: str
    decimals: int
    supply: float
    mint_authority: Optional[str]
    freeze_authority: Optional[str]

async def connect(cluster: str = "devnet") -> AsyncClient: # Conecta a la red de Solana.
    urls = RPC_URLS if cluster == "devnet" else [
        "https://api.mainnet-beta.solana.com",
    ]
    for url in urls:
        try:
            client = AsyncClient(url)
            if await client.is_connected():
                return client
            await client.close()
        except Exception:
            continue
    raise ConnectionError(f"Could not connect to any {cluster} RPC endpoint")

async def create_mint( # Crea la mint de BAP.
    client: AsyncClient,
    wallet,
    decimals: int = TOKEN_DECIMALS,
) -> Pubkey:
    mint_kp = Keypair()
    mint_pubkey = mint_kp.pubkey()

    lamports = (await client.get_minimum_balance_for_rent_exemption(MINT_LEN)).value

    create_ix = create_account(
        CreateAccountParams(
            from_pubkey=wallet.pubkey(),
            to_pubkey=mint_pubkey,
            lamports=lamports,
            space=MINT_LEN,
            owner=TOKEN_PROGRAM_ID,
        )
    )

    init_ix = initialize_mint(
        InitializeMintParams(
            mint=mint_pubkey,
            decimals=decimals,
            mint_authority=wallet.pubkey(),
            freeze_authority=wallet.pubkey(),
            program_id=TOKEN_PROGRAM_ID,
        )
    )

    blockhash = (await client.get_latest_blockhash()).value.blockhash
    msg = Message([create_ix, init_ix], wallet.pubkey())
    tx = Transaction([wallet, mint_kp], msg, blockhash)

    result = await client.send_transaction(
        tx, opts=TxOpts(skip_confirmation=False, preflight_commitment=Confirmed)
    )
    await client.confirm_transaction(result.value, commitment=Confirmed)

    save_mint_address(str(mint_pubkey))
    return mint_pubkey

async def create_token_account( # Crea la cuenta de token de BAP.
    client: AsyncClient,
    wallet,
    mint: Pubkey,
    owner: Optional[Pubkey] = None,
) -> Pubkey:
    owner = owner or wallet.pubkey()
    ata = get_associated_token_address(owner, mint)

    ix = create_associated_token_account(
        payer=wallet.pubkey(),
        owner=owner,
        mint=mint,
    )

    blockhash = (await client.get_latest_blockhash()).value.blockhash
    msg = Message([ix], wallet.pubkey())
    tx = Transaction([wallet], msg, blockhash)

    await client.send_transaction(
        tx, opts=TxOpts(skip_confirmation=False, preflight_commitment=Confirmed)
    )

    return ata

async def mint_tokens( # Muestra tokens de BAP.
    client: AsyncClient,
    wallet,
    mint: Pubkey,
    amount: float,
    dest: Optional[Pubkey] = None,
) -> Pubkey:
    if dest is None:
        dest = get_associated_token_address(wallet.pubkey(), mint)

    raw_amount = int(amount * (10 ** TOKEN_DECIMALS))

    ix = mint_to(
        MintToParams(
            mint=mint,
            dest=dest,
            mint_authority=wallet.pubkey(),
            amount=raw_amount,
            signers=[wallet.pubkey()],
            program_id=TOKEN_PROGRAM_ID,
        )
    )

    blockhash = (await client.get_latest_blockhash()).value.blockhash
    msg = Message([ix], wallet.pubkey())
    tx = Transaction([wallet], msg, blockhash)

    result = await client.send_transaction(
        tx, opts=TxOpts(skip_confirmation=False, preflight_commitment=Confirmed)
    )
    await client.confirm_transaction(result.value, commitment=Confirmed)

    return dest

async def transfer_tokens( # Transfiere tokens de BAP.
    client: AsyncClient,
    wallet,
    mint: Pubkey,
    amount: float,
    dest_owner: Pubkey,
) -> Pubkey:
    source = get_associated_token_address(wallet.pubkey(), mint)
    dest = get_associated_token_address(dest_owner, mint)

    raw_amount = int(amount * (10 ** TOKEN_DECIMALS))

    instructions = []

    dest_info = await client.get_account_info(dest)
    if dest_info.value is None:
        instructions.append(
            create_associated_token_account(
                payer=wallet.pubkey(),
                owner=dest_owner,
                mint=mint,
            )
        )

    instructions.append(
        transfer(
            TransferParams(
                source=source,
                dest=dest,
                owner=wallet.pubkey(),
                amount=raw_amount,
                signers=[wallet.pubkey()],
                program_id=TOKEN_PROGRAM_ID,
            )
        )
    )

    blockhash = (await client.get_latest_blockhash()).value.blockhash
    msg = Message(instructions, wallet.pubkey())
    tx = Transaction([wallet], msg, blockhash)

    result = await client.send_transaction(
        tx, opts=TxOpts(skip_confirmation=False, preflight_commitment=Confirmed)
    )
    await client.confirm_transaction(result.value, commitment=Confirmed)

    return dest

async def burn_tokens( # Destruye tokens de BAP.
    client: AsyncClient,
    wallet,
    mint: Pubkey,
    amount: float,
) -> None:
    source = get_associated_token_address(wallet.pubkey(), mint)
    raw_amount = int(amount * (10 ** TOKEN_DECIMALS))

    ix = burn(
        BurnParams(
            account=source,
            mint=mint,
            owner=wallet.pubkey(),
            amount=raw_amount,
            signers=[wallet.pubkey()],
            program_id=TOKEN_PROGRAM_ID,
        )
    )

    blockhash = (await client.get_latest_blockhash()).value.blockhash
    msg = Message([ix], wallet.pubkey())
    tx = Transaction([wallet], msg, blockhash)

    result = await client.send_transaction(
        tx, opts=TxOpts(skip_confirmation=False, preflight_commitment=Confirmed)
    )
    await client.confirm_transaction(result.value, commitment=Confirmed)

async def get_balance( # Obtiene el saldo de tokens de BAP.
    client: AsyncClient,
    mint: Pubkey,
    address: Optional[Pubkey] = None,
) -> float:
    if address is None:
        return 0.0

    ata = get_associated_token_address(address, mint)
    try:
        resp = await client.get_token_account_balance(ata, commitment=Confirmed)
        return float(resp.value.ui_amount or 0)
    except Exception:
        return 0.0

async def get_supply(client: AsyncClient, mint: Pubkey) -> float: # Obtiene la cantidad total de tokens de BAP.
    info = await get_mint_info(client, mint)
    return info.supply

async def get_mint_info(client: AsyncClient, mint: Pubkey) -> MintInfo: # Obtiene la informacion de la mint de BAP.
    resp = await client.get_account_info(mint, commitment=Confirmed)
    data = resp.value.data

    mint_authority_option = data[0]
    mint_authority = None
    if mint_authority_option == 1:
        mint_authority = str(Pubkey.from_bytes(data[1:33]))

    supply_raw = struct.unpack_from("<Q", data, 36)[0]
    decimals = data[44]

    freeze_authority_option = data[45]
    freeze_authority = None
    if freeze_authority_option == 1:
        freeze_authority = str(Pubkey.from_bytes(data[46:78]))

    supply = supply_raw / (10 ** decimals)

    return MintInfo(
        address=str(mint),
        decimals=decimals,
        supply=supply,
        mint_authority=mint_authority,
        freeze_authority=freeze_authority,
    )

def _encode_string(s: str) -> bytes:
    encoded = s.encode("utf-8")
    return struct.pack("<I", len(encoded)) + encoded

def _build_create_metadata_ix( # Construye la instruccion para crear la metadata de la mint de BAP.
    mint: Pubkey,
    authority: Pubkey,
    payer: Pubkey,
    name: str,
    symbol: str,
    uri: str,
    is_mutable: bool = True,
) -> Instruction:
    metaplex = Pubkey.from_string(METAPLEX_PROGRAM_ID)

    metadata_pda, _ = Pubkey.find_program_address(
        [b"metadata", bytes(metaplex), bytes(mint)],
        metaplex,
    )

    data = bytearray()
    data.append(33)

    data += _encode_string(name)
    data += _encode_string(symbol)
    data += _encode_string(uri)
    data += struct.pack("<H", 0)

    data.append(0)
    data.append(0)
    data.append(0)

    data.append(1 if is_mutable else 0)

    data.append(0)

    accounts = [
        AccountMeta(metadata_pda, is_signer=False, is_writable=True),
        AccountMeta(mint, is_signer=False, is_writable=False),
        AccountMeta(authority, is_signer=True, is_writable=False),
        AccountMeta(payer, is_signer=True, is_writable=True),
        AccountMeta(authority, is_signer=False, is_writable=False),
        AccountMeta(
            Pubkey.from_string("11111111111111111111111111111111"),
            is_signer=False,
            is_writable=False,
        ),
        AccountMeta(
            Pubkey.from_string("Sysvar1nstructions1111111111111111111111111"),
            is_signer=False,
            is_writable=False,
        ),
    ]

    return Instruction(metaplex, bytes(data), accounts)

async def set_metadata( # Establece la metadata de la mint de BAP.
    client: AsyncClient,
    wallet,
    mint: Pubkey,
    name: str = TOKEN_NAME,
    symbol: str = TOKEN_SYMBOL,
    uri: str = "",
) -> None:
    ix = _build_create_metadata_ix(
        mint=mint,
        authority=wallet.pubkey(),
        payer=wallet.pubkey(),
        name=name,
        symbol=symbol,
        uri=uri,
        is_mutable=True,
    )

    blockhash = (await client.get_latest_blockhash()).value.blockhash
    msg = Message([ix], wallet.pubkey())
    tx = Transaction([wallet], msg, blockhash)

    result = await client.send_transaction(
        tx, opts=TxOpts(skip_confirmation=False, preflight_commitment=Confirmed)
    )
    await client.confirm_transaction(result.value, commitment=Confirmed)

async def revoke_freeze_authority(client: AsyncClient, wallet, mint: Pubkey) -> None: # Revoca la autoridad de congelamiento de la mint de BAP.
    ix = set_authority(
        SetAuthorityParams(
            account_or_mint=mint,
            current_authority=wallet.pubkey(),
            authority_type=1,
            new_authority=None,
            signers=[wallet.pubkey()],
            program_id=TOKEN_PROGRAM_ID,
        )
    )

    blockhash = (await client.get_latest_blockhash()).value.blockhash
    msg = Message([ix], wallet.pubkey())
    tx = Transaction([wallet], msg, blockhash)

    result = await client.send_transaction(
        tx, opts=TxOpts(skip_confirmation=False, preflight_commitment=Confirmed)
    )
    await client.confirm_transaction(result.value, commitment=Confirmed)

async def revoke_mint_authority(client: AsyncClient, wallet, mint: Pubkey) -> None: # Revoca la autoridad de la mint de BAP.
    ix = set_authority(
        SetAuthorityParams(
            account_or_mint=mint,
            current_authority=wallet.pubkey(),
            authority_type=0,
            new_authority=None,
            signers=[wallet.pubkey()],
            program_id=TOKEN_PROGRAM_ID,
        )
    )

    blockhash = (await client.get_latest_blockhash()).value.blockhash
    msg = Message([ix], wallet.pubkey())
    tx = Transaction([wallet], msg, blockhash)

    result = await client.send_transaction(
        tx, opts=TxOpts(skip_confirmation=False, preflight_commitment=Confirmed)
    )
    await client.confirm_transaction(result.value, commitment=Confirmed)

async def make_metadata_immutable( # Hace la metadata de la mint de BAP inmutable.
    client: AsyncClient,
    wallet,
    mint: Pubkey,
) -> None:
    metaplex = Pubkey.from_string(METAPLEX_PROGRAM_ID)

    metadata_pda, _ = Pubkey.find_program_address(
        [b"metadata", bytes(metaplex), bytes(mint)],
        metaplex,
    )

    data = bytearray()
    data.append(15)
    data.append(2)
    data.append(0)
    data.append(0)

    accounts = [
        AccountMeta(metadata_pda, is_signer=False, is_writable=True),
        AccountMeta(wallet.pubkey(), is_signer=True, is_writable=False),
    ]

    ix = Instruction(metaplex, bytes(data), accounts)

    blockhash = (await client.get_latest_blockhash()).value.blockhash
    msg = Message([ix], wallet.pubkey())
    tx = Transaction([wallet], msg, blockhash)

    result = await client.send_transaction(
        tx, opts=TxOpts(skip_confirmation=False, preflight_commitment=Confirmed)
    )
    await client.confirm_transaction(result.value, commitment=Confirmed)