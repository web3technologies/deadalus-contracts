from pathlib import Path
import json
import re


class ContractDataWriter:

    @staticmethod
    def write_data(deploy_env, abi, chain_id, contract_name, address=""):
        match = re.search(r'\.(.*)', str(chain_id))
        base_data_path = Path.cwd() / f"deadalus-interface/src/contracts/{deploy_env}/{match.group(1)}"
        base_data_path.mkdir(parents=True, exist_ok=True)
        file_data = {
            "address": hex(address) if address else "null",
            "chain_id": repr(chain_id),
            "abi": abi
        }
        with open(base_data_path / f"{contract_name}_output.json", "w") as file:
            json.dump(file_data, file, indent=4)