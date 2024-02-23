from pathlib import Path
import toml


from starknet_py.hash.casm_class_hash import compute_casm_class_hash
from starknet_py.hash.sierra_class_hash import compute_sierra_class_hash
from starknet_py.common import create_casm_class, create_sierra_compiled_contract


class InitializeContractData:
    
    def __init__(self, contract_name):
        self.contract_name = contract_name
        self.cwd = Path.cwd() / "deadalus-contracts"
        self.__get_package_name()
        
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