import asyncio
from pathlib import Path
from decouple import config
import toml

from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.models import StarknetChainId
from starknet_py.hash.casm_class_hash import compute_casm_class_hash
from starknet_py.common import create_casm_class
from starknet_py.constants import DEFAULT_DEPLOYER_ADDRESS


class DeployerConfig:
    
    def __init__(self, account_address, private_key, node_url, udc_address=DEFAULT_DEPLOYER_ADDRESS, chain_id=StarknetChainId.GOERLI) -> None:
        self.account_address = account_address
        self.private_key = private_key
        self.node_url = node_url
        self.udc_address = udc_address
        self.chain_id=chain_id
        
    @classmethod
    def get_config(cls, deploy_env):
        if deploy_env == 'dev':
            dev_deployer_config = cls(
                account_address=config("DEV_ACCOUNT_ADDRESS"),
                private_key=config("DEV_PRIVATE_KEY"),
                node_url=config("DEV_NODE_URL"),
                udc_address="0x41A78E741E5AF2FEC34B695679BC6891742439F7AFB8484ECD7766661AD02BF"
            )
        elif deploy_env == 'int':
            dev_deployer_config = cls(
                account_address=config("INT_ACCOUNT_ADDRESS"),
                private_key=config("INT_PRIVATE_KEY"),
                node_url=config("INT_NODE_URL"),
            )
        else:
            raise ValueError(f"{deploy_env} is not available for deployment.")
        return dev_deployer_config
        
class DeployContract:
    
    def __init__(self, contract_name, deployer_config: DeployerConfig):
        self.contract_name = contract_name
        self.deployer_config = deployer_config
        self.cwd = Path.cwd()
        self.__get_package_name()
        self.__init__data()
        
    def __init__data(self):
        self.key_pair = KeyPair.from_private_key(self.deployer_config.private_key)
        self.client = FullNodeClient(node_url=self.deployer_config.node_url)
        self.account = Account(
            address=self.deployer_config.account_address,
            client=self.client,
            key_pair=self.key_pair,
            chain=self.deployer_config.chain_id
        )
    
    def __get_package_name(self):
        with open(self.cwd / "Scarb.toml", "r") as toml_file:
            parsed_toml=toml.loads(toml_file.read())
        self.module_name=parsed_toml["package"]["name"]
    
    def read_contract_file_data(self):
        
        with open(self.cwd / f"target/dev/{self.module_name}_{self.contract_name}.compiled_contract_class.json", "r") as file:
            casm_data = file.read()
        compiled_class_hash = compute_casm_class_hash(create_casm_class(casm_data))
        
        with open(self.cwd / f"target/dev/{self.module_name}_{self.contract_name}.contract_class.json", "r") as file:
            compiled_contract = file.read()
            
        with open(self.cwd / f"target/dev/{self.module_name}.casm", "r") as file:
            compiled_contract_casm = file.read()
            
        return compiled_class_hash, compiled_contract, compiled_contract_casm
    
    async def declare(self, compiled_class_hash, compiled_contract, compiled_contract_casm):
        print("declaring") 
        declare_result = await Contract.declare_v3(
            account=self.account, 
            compiled_contract=compiled_contract,
            compiled_contract_casm=compiled_contract_casm, 
            compiled_class_hash=compiled_class_hash,
            auto_estimate=True
        )
        await declare_result.wait_for_acceptance()
        return declare_result

    async def deploy(self, declared_contract):
        print("deploying")
        deploy_result = await declared_contract.deploy_v3(
            deployer_address=self.deployer_config.udc_address,
            auto_estimate=True
        )
        await deploy_result.wait_for_acceptance()
        contract = deploy_result.deployed_contract
        return contract
        
    async def run(self):
        compiled_class_hash, compiled_contract, compiled_contract_casm = self.read_contract_file_data()
        declared_contract = await self.declare(compiled_class_hash, compiled_contract, compiled_contract_casm)
        contract = await self.deploy(declared_contract)
        print(hex(contract.address))

def main():
    deploy_env = config("DEPLOY_ENV")
    deployer_config = DeployerConfig.get_config(deploy_env)
    deployer = DeployContract(
        contract_name="HelloStarknet", 
        deployer_config=deployer_config
    )
    asyncio.run(deployer.run())      


if __name__ == "__main__":
    main()