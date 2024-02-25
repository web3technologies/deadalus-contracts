from abc import ABC

from starknet_py.contract import Contract


class ContractInteration(ABC):
    
    def __init__(self, deployer_config, contract_address) -> None:
        self.deployer_config = deployer_config
        self.__contract_address = contract_address
        self.__contract = None

    @property
    def contract_address(self):
        return self.__contract_address

    @property
    def contract(self):
        return self.__contract

    async def get_contract(self):
        self.__contract = await Contract.from_address(address=self.__contract_address, provider=self.deployer_config.account)
        return self.contract

    
class Erc20Contract(ContractInteration):
    async def get_account_balance(self):
        (balance,) = await self.contract.functions["balanceOf"].call(int(self.deployer_config.developer_account,16))
        return balance
    
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


class CounterContract(ContractInteration):
    ...


class FractionContract(ContractInteration):
    ...