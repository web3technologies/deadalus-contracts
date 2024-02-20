from pathlib import Path
import json


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