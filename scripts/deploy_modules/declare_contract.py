from starknet_py.contract import Contract
from starknet_py.net.client_errors import ClientError


class DeclareContract:
    
    def __init__(self, deployer_config, casm_class_hash, compiled_contract, sierra_class_hash) -> None:
        self.deployer_config = deployer_config
        self.casm_class_hash = casm_class_hash
        self.compiled_contract = compiled_contract
        self.sierra_class_hash = sierra_class_hash
    
    async def __declare(self):
        declare_result = await Contract.declare_v3(
            account=self.deployer_config.account, 
            compiled_contract=self.compiled_contract,
            compiled_class_hash=self.casm_class_hash,
            auto_estimate=True
        )
        await declare_result.wait_for_acceptance()
        return declare_result
    
    async def get_contract(self):
        try:
            declared_contract = await self.deployer_config.client.get_class_by_hash(class_hash=self.sierra_class_hash)
            print("contract previously declared")
        except ClientError as e:
            if e.code == 28 and e.message == 'Client failed with code 28. Message: Class hash not found.':
                declared_contract = await self.__declare()
            else:
                raise e
        return declared_contract