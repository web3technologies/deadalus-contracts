from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.signer.stark_curve_signer import KeyPair


class ContractInteration:
    
    def __init__(self, deployer_config) -> None:
        self.deployer_config = deployer_config
        self.key_pair = KeyPair.from_private_key(self.deployer_config.private_key)
        self.client = FullNodeClient(node_url=self.deployer_config.node_url)
        self.account = Account(
            address=self.deployer_config.account_address,
            client=self.client,
            key_pair=self.key_pair,
            chain=self.deployer_config.chain_id
        )
        self.contract = None
    
    async def get_contract(self, address):
        self.contract = await Contract.from_address(address=address, provider=self.account)
        return self.contract
    
    async def call_contract(self, function_name, contract_args):
        if self.contract is None:
            raise ValueError("Contract must not be none before calling")
        invocation = await self.contract.functions[function_name].invoke_v1(**contract_args)
        return invocation