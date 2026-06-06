from seahorse.prelude import *

declare_id('Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS')


class TokenData(Account):
    mint: TokenMint
    authority: Signer


@instruction
def init_token(owner: Signer, mint: Empty[TokenMint]):
    mint.init(
        payer=owner,
        seeds=['my_token', owner],
        decimals=9,
        authority=owner
    )
    print("Token initialized successfully")


@instruction
def mint_token(owner: Signer, mint: TokenMint, dest: TokenAccount):
    mint.mint(
        authority=owner,
        to=dest,
        amount=1000000000
    )
    print("Minted 1 token")
