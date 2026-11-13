"""Print copy-paste instructions for minting the accepted test USDC
for a TrapTest burner wallet.

Read-only: this script NEVER holds, reads, or prints a private key.
It takes only a burner ADDRESS (``--address``) and an amount, and
prints the exact mint call for that address. If no address is given
it prints the same instructions with a ``<BURNER_ADDRESS>``
placeholder — fill it in with your burner's address (never its key).

The accepted token is Telegraph's test USDC on Ethereum Sepolia,
``0xcc194e1a843B658526D0D5C431f670028582Ae17`` (6 decimals, open
``mint(address,uint256)`` — verified live 13 Nov 2026 by an
``eth_call`` simulation of ``mint(burner, 30_000_000)`` returning
``0x`` with no revert). This is NOT Circle faucet USDC
(``0x1c7d4b196cb0c7b01d743fbc6116a902379c7238``) — signing for that
token is rejected by the facilitator.

Usage:
    python3 scripts/fund_burner.py --address 0xYOUR_BURNER_ADDRESS
    python3 scripts/fund_burner.py --address 0x... --amount 30
"""
import argparse

TOKEN = "0xcc194e1a843B658526D0D5C431f670028582Ae17"
TOKEN_NAME = "USD Coin"
CHAIN = "Ethereum Sepolia (chain ID 11155111)"
DECIMALS = 6
DEFAULT_AMOUNT_USDC = 30
FAUCET_URL = "https://sepolia-faucet.pk910.de"

MINT_ABI_FRAGMENT = {
    "name": "mint",
    "type": "function",
    "inputs": [
        {"name": "to", "type": "address"},
        {"name": "amount", "type": "uint256"},
    ],
    "outputs": [],
    "stateMutability": "nonpayable",
}
MINT_SELECTOR = "0x40c10f19"  # mint(address,uint256)


def mint_instructions(address, amount_usdc):
    """Copy-paste mint instructions for ``address``. No keys involved."""
    amount_atomic = int(amount_usdc * 10 ** DECIMALS)
    addr = address or "<BURNER_ADDRESS>"
    return f"""\
Fund your TrapTest burner with accepted test USDC
================================================

Token: {TOKEN} ({TOKEN_NAME}, {DECIMALS} decimals)
Chain: {CHAIN}
Burner address: {addr}
Amount: {amount_usdc} USDC = {amount_atomic} atomic units (6 decimals)

There is NO Telegraph faucet: you mint the accepted test USDC
yourself — the token has an open mint function.

1. Sepolia ETH for gas (the mint tx needs a little): claim from the
   PoW faucet, {FAUCET_URL} (mine a small amount, no account).

2. Call mint() on the token contract, FROM your burner address, for
   your burner address:

   Contract: {TOKEN}
   Function: mint(address to, uint256 amount)
   Selector: {MINT_SELECTOR}
   to:       {addr}
   amount:   {amount_atomic}   ({amount_usdc} USDC)

   ABI fragment (for ethers / web3 / cast):
     {MINT_ABI_FRAGMENT}

   Easiest route: Etherscan Sepolia -> token contract -> "Write
   Contract" -> connect your burner wallet -> mint, with the to /
   amount above. Or with cast:
     cast send {TOKEN} "mint(address,uint256)" {addr} {amount_atomic} \\
       --rpc-url https://ethereum-sepolia-rpc.publicnode.com \\
       --private-key <YOUR_BURNER_KEY>   # never share this key

3. Verify the balance (no spend):
     python3 -m traptest.run --list-miners
     python3 -m traptest.run --traps traps-frozen-2026-11-09.json \\
       --providers 9002,8453 --key .burner3.key \\
       --out /tmp/traptest-dry-run.json --dry-run

   The dry-run prints the payer address and the max cost ($0 at
   dry-run — nothing is bought or written).

Do NOT use Circle faucet USDC (0x1c7d4b196cb0c7b01d743fbc6116a902379c7238):
signing for that token is rejected by the facilitator.
"""


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Print mint instructions for a TrapTest burner "
                    "(address only — never a private key).")
    parser.add_argument("--address", default=None,
                        help="burner wallet address to fund "
                             "(0x...; no key, ever)")
    parser.add_argument("--amount", type=float, default=DEFAULT_AMOUNT_USDC,
                        help=f"USDC to mint (default {DEFAULT_AMOUNT_USDC})")
    args = parser.parse_args(argv)
    print(mint_instructions(args.address, args.amount))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
