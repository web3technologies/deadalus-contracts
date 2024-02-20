from abc import ABC

from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.signer.stark_curve_signer import KeyPair


class ContractInteration(ABC):
    
    def __init__(self, deployer_config, contract_address) -> None:
        self.deployer_config = deployer_config
        self.key_pair = KeyPair.from_private_key(self.deployer_config.private_key)
        self.client = FullNodeClient(node_url=self.deployer_config.node_url)
        self.account = Account(
            address=self.deployer_config.account_address,
            client=self.client,
            key_pair=self.key_pair,
            chain=self.deployer_config.chain_id
        )
        self.__contract_address = contract_address
        self.__contract = None

    @property
    def contract_address(self):
        return self.__contract_address

    @property
    def contract(self):
        return self.__contract

    async def get_contract(self):
        self.__contract = await Contract.from_address(address=self.__contract_address, provider=self.account)
        return self.contract
    
    async def call_contract(self, function_name, contract_kwargs):
        if self.contract is None:
            raise ValueError("Contract must not be none before calling")
        invocation = await self.contract.functions[function_name].invoke_v3(
            **contract_kwargs,
            auto_estimate=True
        )
        (balance,) = await self.contract.functions["balanceOf"].call(contract_kwargs.get("recipient"))
        print(f"new balance {balance}")
        return invocation
    
class Erc20Contract(ContractInteration):
    async def get_account_balance(self):
        (balance,) = await self.contract.functions["balanceOf"].call(int(self.deployer_config.developer_account,16))
        return balance