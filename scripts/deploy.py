import asyncio
import argparse
from datetime import datetime

from deploy_modules import (
    DeployContract, 
    DeployerConfig, 
    ContractDataWriter, 
    ContractInteration
)


async def main(deploy_env):
    
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d:%H:%M:%S")
    deployer_config = DeployerConfig.get_config(deploy_env)
    contract_name = "ExoToken"
    deployer = DeployContract(
        contract_name=contract_name, 
        deployer_config=deployer_config,
        constructor_args={
            "initial_supply": 10000, 
            "recipient": int(deployer_config.account_address, 16)       # must cast address string to int16
        }
    )
    deployed_contract = await deployer.run()
    ContractDataWriter.write_data(
        deploy_env=args.deploy_env, 
        contract=deployed_contract, 
        contract_name=contract_name, 
        formatted_time=formatted_time
    )


async def fund_account(deploy_env):
    deployer_config = DeployerConfig.get_config(deploy_env)
    eth_address = int("0x49D36570D4E46F48E99674BD3FCC84644DDD6B96F7C741B1562B82F9E004DC7", 16)
    contract_interaction = ContractInteration(deployer_config)
    await contract_interaction.get_contract(eth_address)
    contract_kwargs = {
        "sender":int(deployer_config.account_address,16), 
        "recipient":int("0x0578cc46220bb2822ed5070ab5cc98687395135780ae709b8356bd11a1c5f3e5", 16), 
        "amount": 10000, 
        "max_fee": int(1e16)
    }
    transaction = await contract_interaction.call_contract("transferFrom", contract_kwargs)
    print(transaction)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to deploy smart contracts.')
    parser.add_argument('--deploy-env', dest='deploy_env', type=str, help='Deployment environment (e.g., dev, int, prod)')
    args = parser.parse_args()

    asyncio.run(main(args.deploy_env))
    # asyncio.run(fund_account(args.deploy_env))