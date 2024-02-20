import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from decouple import config
import toml
import json

from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.models import StarknetChainId
from starknet_py.net.client_models import SierraContractClass
from starknet_py.hash.casm_class_hash import compute_casm_class_hash
from starknet_py.hash.sierra_class_hash import compute_sierra_class_hash
from starknet_py.common import create_casm_class, create_sierra_compiled_contract
from starknet_py.net.client_errors import ClientError
from starknet_py.contract import DeclareResult
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
    
    def __init__(self, contract_name, deployer_config: DeployerConfig, constructor_args:dict = {}):
        self.contract_name = contract_name
        self.deployer_config = deployer_config
        self.constructor_args = constructor_args
        self.cwd = Path.cwd() / "deadalus-contracts"
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
            compiled_contract_class = file.read()
        casm_class_hash = compute_casm_class_hash(create_casm_class(compiled_contract_class))
        
        with open(self.cwd / f"target/dev/{self.module_name}_{self.contract_name}.contract_class.json", "r") as file:
            compiled_contract = file.read()
        sierra_class_hash = compute_sierra_class_hash(create_sierra_compiled_contract(compiled_contract=compiled_contract))
            
        return casm_class_hash, compiled_contract, sierra_class_hash
    
    async def declare(self, casm_class_hash, compiled_contract):
        print("declaring") 
        declare_result = await Contract.declare_v3(
            account=self.account, 
            compiled_contract=compiled_contract,
            compiled_class_hash=casm_class_hash,
            auto_estimate=True
        )
        await declare_result.wait_for_acceptance()
        return declare_result
    
    async def get_contract(self, casm_class_hash, compiled_contract, sierra_class_hash) -> tuple[Contract | SierraContractClass, bool]:
        try:
            declared_contract = await self.client.get_class_by_hash(class_hash=sierra_class_hash)
            print("contract previously declared")
        except ClientError as e:
            if e.code == 28 and e.message == 'Client failed with code 28. Message: Class hash not found.':
                declared_contract = await self.declare(casm_class_hash, compiled_contract)
            else:
                raise e
        return declared_contract
        

    async def deploy(self, declared_contract, sierra_class_hash):
        print("deploying")
        deploy_result = await Contract.deploy_contract_v3(
            account=self.account,
            class_hash=sierra_class_hash,
            deployer_address=self.deployer_config.udc_address,
            abi=declared_contract._get_abi() if isinstance(declared_contract, DeclareResult) else json.loads(declared_contract.abi),
            constructor_args=self.constructor_args,
            auto_estimate=True,
        )
        await deploy_result.wait_for_acceptance()
        contract = deploy_result.deployed_contract
        return contract
        
    async def run(self):
        casm_class_hash, compiled_contract, sierra_class_hash = self.read_contract_file_data()
        declared_contract = await self.get_contract(casm_class_hash, compiled_contract, sierra_class_hash)
        deployed_contract = await self.deploy(declared_contract, sierra_class_hash)
        return deployed_contract


class ContractInterations:
    
    def __init__(self, deployer_config: DeployerConfig) -> None:
        self.deployer_config = deployer_config
        self.key_pair = KeyPair.from_private_key(self.deployer_config.private_key)
        self.client = FullNodeClient(node_url=self.deployer_config.node_url)
        self.account = Account(
            address=self.deployer_config.account_address,
            client=self.client,
            key_pair=self.key_pair,
            chain=self.deployer_config.chain_id
        )
    
    async def get_contract(self, address):
        c = await Contract.from_address(address=address, provider=self.client)
        print(c)
        
class ContractDataWriter:
    
    @staticmethod
    def write_data(deploy_env, contract, contract_name, formatted_time):
        print("writing file")
        base_data_path = Path.cwd() / f"deadalus-contracts/deploy_output/{deploy_env}"
        base_data_path.mkdir(parents=True, exist_ok=True)
        file_data = {
            "address": hex(contract.address),
            "chain_id": repr(contract.account.signer.chain_id),
            "abi": contract.data.abi
        }
        with open(base_data_path / f"{contract_name}_output_{formatted_time}.json", "w") as file:
            json.dump(file_data, file, indent=4)
        
    
def main():
    parser = argparse.ArgumentParser(description='Script to deploy smart contracts.')
    parser.add_argument('--deploy-env', dest='deploy_env', type=str, help='Deployment environment (e.g., dev, int, prod)')
    args = parser.parse_args()
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d:%H:%M:%S")
    deployer_config = DeployerConfig.get_config(args.deploy_env)
    contract_name = "ExoToken"
    deployer = DeployContract(
        contract_name=contract_name, 
        deployer_config=deployer_config,
        constructor_args={
            "initial_supply": 10000, 
            "recipient": int(deployer_config.account_address, 16)       # must cast address string to int16
        }
    )
    deployed_contract = asyncio.run(deployer.run())
    ContractDataWriter.write_data(
        deploy_env=args.deploy_env, 
        contract=deployed_contract, 
        contract_name=contract_name, 
        formatted_time=formatted_time
    )

if __name__ == "__main__":
    main()