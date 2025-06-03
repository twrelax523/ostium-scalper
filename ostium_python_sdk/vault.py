from decimal import Decimal
from web3 import Web3
from .abi.vault_abi import vault_abi
from .abi.usdc_abi import usdc_abi
from .utils import convert_to_scaled_integer, to_base_units, approve_usdc, get_account
from eth_account.account import Account

# Minimum lock duration in seconds (1 week)
MIN_LOCK_DURATION = 7 * 24 * 60 * 60  # 7 days in seconds


class OstiumVault:
    """
    Client for interacting with the Ostium vault on the Arbitrum network.

    Supports vault operations like deposits, withdrawals, and managing locked positions.
    This class is designed for market makers and liquidity providers who want to
    interact with the vault directly.

    Args:
        w3: Web3 instance connected to the Arbitrum network
        vault_address: Contract address for the Ostium vault
        usdc_address: Contract address for USDC token
        private_key: Optional private key for transaction signing. If not provided,
                    only read-only operations will be available.
        verbose: Whether to log detailed information
    """

    def __init__(self, w3: Web3, vault_address: str, usdc_address: str, private_key: str = None, verbose=False) -> None:
        self.web3 = w3
        self.verbose = verbose
        self.private_key = private_key
        self.vault_address = vault_address
        self.usdc_address = usdc_address

        # Create contract instances
        self.vault_contract = self.web3.eth.contract(
            address=self.vault_address, abi=vault_abi)
        self.usdc_contract = self.web3.eth.contract(
            address=self.usdc_address, abi=usdc_abi)

        if (verbose):
            print(f"Vault contract: {self.vault_contract.address}")
            print(f"USDC contract: {self.usdc_contract.address}")

    def log(self, message):
        if self.verbose:
            print(message)

    def get_nonce(self, address):
        return self.web3.eth.get_transaction_count(address)

    def deposit(self, amount: float, receiver: str = None):
        """
        Deposit USDC into the vault.

        Args:
            amount: Amount of USDC to deposit
            receiver: Optional address to receive the vault shares (defaults to sender)

        Returns:
            Transaction receipt

        Raises:
            ValueError: If no private key is provided during initialization
        """
        account = get_account(self.web3, self.private_key)
        receiver = receiver or account.address

        # Convert amount to base units (6 decimals for USDC)
        amount_base = to_base_units(amount, decimals=6)

        # First approve the vault to spend USDC
        self.log("Approving USDC spend for vault...")
        approve_usdc(
            self.web3,
            self.usdc_contract,
            self.vault_address,
            amount_base,
            self.private_key,
            self.verbose
        )

        # Build and send deposit transaction
        self.log("Depositing USDC to vault...")
        tx = self.vault_contract.functions.deposit(
            amount_base,
            receiver
        ).build_transaction({
            'from': account.address,
            'nonce': self.get_nonce(account.address)
        })

        signed_tx = self.web3.eth.account.sign_transaction(
            tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return receipt

    def deposit_with_lock(self, amount: float, lock_period_seconds: int, receiver: str = None):
        """
        Deposit USDC into the vault with a lock period.

        Args:
            amount: Amount of USDC to deposit
            lock_period_seconds: Lock period in seconds (minimum 1 week)
            receiver: Optional address to receive the vault shares (defaults to sender)

        Returns:
            Transaction receipt

        Raises:
            ValueError: If no private key is provided during initialization or if lock period is less than 1 week
        """
        if lock_period_seconds < MIN_LOCK_DURATION:
            raise ValueError(
                f"Lock period must be at least {MIN_LOCK_DURATION} seconds (1 week)")

        account = get_account(self.web3, self.private_key)
        receiver = receiver or account.address

        # Convert amount to base units (6 decimals for USDC)
        amount_base = to_base_units(amount, decimals=6)

        # First approve the vault to spend USDC
        self.log("Approving USDC spend for vault...")
        approve_usdc(
            self.web3,
            self.usdc_contract,
            self.vault_address,
            amount_base,
            self.private_key,
            self.verbose
        )

        # Build and send transaction
        self.log("Depositing USDC to vault with lock...")
        tx = self.vault_contract.functions.depositWithDiscountAndLock(
            amount_base,
            lock_period_seconds,
            receiver
        ).build_transaction({
            'from': account.address,
            'nonce': self.get_nonce(account.address)
        })

        signed_tx = self.web3.eth.account.sign_transaction(
            tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return receipt

    def withdraw(self, shares: float, receiver: str = None):
        """
        Withdraw USDC from the vault by burning shares.

        Args:
            shares: Amount of vault shares to burn
            receiver: Optional address to receive the USDC (defaults to sender)

        Returns:
            Transaction receipt

        Raises:
            ValueError: If no private key is provided during initialization
        """
        account = get_account(self.web3, self.private_key)
        receiver = receiver or account.address

        # Convert shares to base units (18 decimals for vault shares)
        shares_base = to_base_units(shares, decimals=18)

        # Build and send transaction
        tx = self.vault_contract.functions.redeem(
            shares_base,
            receiver,
            account.address
        ).build_transaction({
            'from': account.address,
            'nonce': self.get_nonce(account.address)
        })

        signed_tx = self.web3.eth.account.sign_transaction(
            tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return receipt

    def get_balance(self, address: str = None):
        """
        Get the vault share (OLP) balance for an address.

        Args:
            address: Address to check balance for (defaults to sender if private key provided)

        Returns:
            Balance in vault shares
        """
        if address is None and self.private_key:
            account = get_account(self.web3, self.private_key)
            address = account.address
        elif address is None:
            raise ValueError(
                "Either address parameter or private_key must be provided")

        balance = self.vault_contract.functions.balanceOf(address).call()
        return Decimal(balance) / Decimal(10**6)

    def get_total_assets(self):
        """
        Get the total assets in the vault.

        Returns:
            Total assets in USDC
        """
        total_assets = self.vault_contract.functions.totalAssets().call()
        # Convert from base units
        return Decimal(total_assets) / Decimal(10**6)

    def get_asset_per_share(self):
        """
        Get the current asset per share ratio.

        Returns:
            Asset per share ratio
        """
        total_assets = self.vault_contract.functions.totalAssets().call()
        total_supply = self.vault_contract.functions.totalSupply().call()

        if total_supply == 0:
            return Decimal(1)

        return Decimal(total_assets) / Decimal(total_supply)
