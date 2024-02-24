import time

from starknet_py.contract import Contract
from .deployer_config import DeployerConfig


async def update_oracle(deploy_env, contract_address):
    deployer_config = DeployerConfig.get_config(deploy_env).init_account()
    oracle_contract = await Contract.from_address(provider=deployer_config.account, address=contract_address)
    while True:
        curr_time = int(time.time())
        await oracle_contract.functions["set_time"].invoke_v3(
            unix_timestamp=curr_time,
            auto_estimate=True
        )
        contract_time = await oracle_contract.functions["get_time"].call()
        print(f"Current contract time is: {contract_time[0]}")