import asyncio
import argparse
from datetime import datetime

from deploy_modules import (
    DeclareContract,
    DeployContract, 
    DeployerConfig, 
    ContractDataWriter, 
    InitializeContractData,
    Erc20Contract,
)

CONTRACTS = [
    {
        "contract_name": "Counter",
        "constructor_args": {},
        "should_deploy": False
    }
]

async def main(deploy_env):
    """
        main deployment script that will declare, deploy and write the contract data
    """
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d:%H:%M:%S")
    deployer_config = DeployerConfig.get_config(deploy_env).init_account()
    
    for contract in CONTRACTS:
        initialized_contract = InitializeContractData(contract_name=contract["contract_name"])
        casm_class_hash, compiled_contract, sierra_class_hash = initialized_contract.read_contract_file_data()
        declared_contract = DeclareContract(
            deployer_config,
            casm_class_hash,
            compiled_contract,
            sierra_class_hash
        )
        declared_contract = await declared_contract.get_contract()
        if contract["should_deploy"]:
            deployer = DeployContract(
                declared_contract,
                deployer_config,
                sierra_class_hash,
                constructor_args=contract["constructor_args"]
            )
            deployed_contract = await deployer.deploy()
            ContractDataWriter.write_data(
                deploy_env=args.deploy_env, 
                contract=deployed_contract, 
                contract_name=contract["contract_name"], 
                formatted_time=formatted_time
            )


async def fund_account(deploy_env):
    """
        If using a dev network on local host we need to fund an argent or braavos account in order to interact with the smart contracts
    """
    deployer_config = DeployerConfig.get_config(deploy_env)
    eth_address = int("0x49D36570D4E46F48E99674BD3FCC84644DDD6B96F7C741B1562B82F9E004DC7", 16)
    contract_interaction = Erc20Contract(deployer_config, contract_address=eth_address)
    await contract_interaction.get_contract()
    current_account_balance = await contract_interaction.get_account_balance()
    if current_account_balance < int(1e18):
        print(f"current balance funding account to {current_account_balance + int(1e18)}")
        contract_kwargs = {
            "recipient":int(deployer_config.developer_account, 16), 
            "amount": int(1e18)     # send 1 ether
        }
        await contract_interaction.call_contract("transfer", contract_kwargs)
    else:
        print(f"Not funding account balance is {current_account_balance}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to deploy smart contracts.')
    parser.add_argument('--deploy-env', dest='deploy_env', type=str, help='Deployment environment (e.g., dev, int, prod)')
    args = parser.parse_args()
    asyncio.run(main(args.deploy_env))
    if args.deploy_env == "dev":
        asyncio.run(fund_account(args.deploy_env))