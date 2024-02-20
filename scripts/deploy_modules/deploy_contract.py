from pathlib import Path
import toml
import json

from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.client_models import SierraContractClass
from starknet_py.hash.casm_class_hash import compute_casm_class_hash
from starknet_py.hash.sierra_class_hash import compute_sierra_class_hash
from starknet_py.common import create_casm_class, create_sierra_compiled_contract
from starknet_py.net.client_errors import ClientError

from .deployer_config import DeployerConfig


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
        is_previously_declared = False
        try:
            declared_contract = await self.client.get_class_by_hash(class_hash=sierra_class_hash)
            print("contract previously declared")
            is_previously_declared = True
        except ClientError as e:
            if e.code == 28 and e.message == 'Client failed with code 28. Message: Class hash not found.':
                declared_contract = await self.declare(casm_class_hash, compiled_contract)
            else:
                raise e
        return declared_contract, is_previously_declared
        

    async def deploy(self, declared_contract, is_previously_declared, sierra_class_hash):
        print("deploying")
        if is_previously_declared:
            deploy_result = await Contract.deploy_contract_v3(
                account=self.account,
                class_hash=sierra_class_hash,
                deployer_address=self.deployer_config.udc_address,
                abi=json.loads(declared_contract.abi),
                constructor_args=self.constructor_args,
                auto_estimate=True,
            )
        else:
            deploy_result = await declared_contract.deploy_v3(
                deployer_address=self.deployer_config.udc_address,
                auto_estimate=True,
                constructor_args=self.constructor_args
            )
        await deploy_result.wait_for_acceptance()
        contract = deploy_result.deployed_contract
        return contract
        
    async def run(self):
        casm_class_hash, compiled_contract, sierra_class_hash = self.read_contract_file_data()
        declared_contract, is_previously_declared = await self.get_contract(casm_class_hash, compiled_contract, sierra_class_hash)
        deployed_contract = await self.deploy(declared_contract, is_previously_declared, sierra_class_hash)
        return deployed_contract