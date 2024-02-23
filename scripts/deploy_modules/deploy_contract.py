from pathlib import Path
import json

from starknet_py.contract import Contract, DeclareResult
from .deployer_config import DeployerConfig


class DeployContract:
    
    def __init__(self, declared_contract, deployer_config: DeployerConfig, sierra_class_hash, constructor_args:dict = {}):
        self.deployer_config = deployer_config
        self.declared_contract = declared_contract
        self.sierra_class_hash = sierra_class_hash
        self.constructor_args = constructor_args
        
    async def deploy(self):
        deploy_result = await Contract.deploy_contract_v3(
            account=self.deployer_config.account,
            class_hash=self.sierra_class_hash,
            deployer_address=self.deployer_config.udc_address,
            abi=self.declared_contract._get_abi() if isinstance(self.declared_contract, DeclareResult) else json.loads(self.declared_contract.abi),
            constructor_args=self.constructor_args,
            auto_estimate=True,
        )
        await deploy_result.wait_for_acceptance()
        contract = deploy_result.deployed_contract
        return contract