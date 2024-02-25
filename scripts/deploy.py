import asyncio
import argparse
import json

from starknet_py.contract import DeclareResult

from deploy_modules import (
    DeclareContract,
    DeployContract, 
    DeployerConfig, 
    ContractDataWriter, 
    InitializeContractData,
    Erc20Contract
)


get_abi = lambda contract: contract._get_abi() if isinstance(contract, DeclareResult) else json.loads(contract.abi)


async def main(deploy_env):
    """
        main deployment script that will declare, deploy and write the contract data
    """
    deployer_config = DeployerConfig.get_config(deploy_env).init_account()
    
    ### Counter
    print("Delcaring Counter")
    initialized_counter_contract = InitializeContractData(contract_name="Counter")
    casm_class_hash_counter, compiled_contract_counter, sierra_class_hash_counter = initialized_counter_contract.read_contract_file_data()
    declared_counter_contract = DeclareContract(
        deployer_config,
        casm_class_hash_counter,
        compiled_contract_counter,
        sierra_class_hash_counter
    )
    declared_counter_contract = await declared_counter_contract.get_contract()
    print("Declared Counter Contract")
    ContractDataWriter.write_data(
        deploy_env=args.deploy_env, 
        abi=get_abi(declared_counter_contract),
        chain_id=deployer_config.chain_id,
        contract_name="Counter", 
    )
    print("Wrote Counter Contract Data")
    print()

    ### NFT Declare
    print("Delcaring NFT")
    initialized_nft_contract = InitializeContractData(contract_name="FractionNFT")
    casm_class_hash_nft, compiled_contract_nft, sierra_class_hash_nft = initialized_nft_contract.read_contract_file_data()
    declared_nft_contract = DeclareContract(
        deployer_config,
        casm_class_hash_nft,
        compiled_contract_nft,
        sierra_class_hash_nft
    )
    declared_nft_contract = await declared_nft_contract.get_contract()
    print("Declared NFT Contract")
    ContractDataWriter.write_data(
        deploy_env=args.deploy_env, 
        abi=get_abi(declared_nft_contract),
        chain_id=deployer_config.chain_id,
        contract_name="NFT", 
    )
    print("Wrote NFT Contract Data")
    print()

    ### Counter Factory
    print("Declaring CounterFactory")
    initialized_counter_factory_contract = InitializeContractData(contract_name="CounterFactory")
    casm_class_hash_counter_factory, compiled_contract_counter_factory, sierra_class_hash_counter_factory = initialized_counter_factory_contract.read_contract_file_data()
    declared_counter_factory_contract = DeclareContract(
        deployer_config,
        casm_class_hash_counter_factory,
        compiled_contract_counter_factory,
        sierra_class_hash_counter_factory
    )
    declared_counter_factory_contract = await declared_counter_factory_contract.get_contract()
    print("Declared CounterFactory Contract")
    deployer = DeployContract(
        declared_counter_factory_contract,
        deployer_config,
        sierra_class_hash_counter_factory,
        constructor_args={"class_hash": sierra_class_hash_counter}
    )
    deployed_counter_factory_contract = await deployer.deploy()
    print(f"Deployed CounterFactory Contract to address {hex(deployed_counter_factory_contract.address)}")
    ContractDataWriter.write_data(
        deploy_env=args.deploy_env, 
        abi=get_abi(declared_counter_factory_contract),
        chain_id=deployer_config.chain_id,
        contract_name="CounterFactory", 
        address = deployed_counter_factory_contract.address
    )
    print("Wrote CounterFactory Contract Data")
    print()

    ### TimeOracle
    print("Declaring TimeOracle Contract")
    initialized_time_oracle_contract = InitializeContractData(contract_name="TimeOracle")
    casm_class_hash_time_oracle, compiled_contract_time_oracle, sierra_class_hash_time_oracle = initialized_time_oracle_contract.read_contract_file_data()
    declared_time_oracle_contract = DeclareContract(
        deployer_config,
        casm_class_hash_time_oracle,
        compiled_contract_time_oracle,
        sierra_class_hash_time_oracle
    )
    declared_time_oracle_contract = await declared_time_oracle_contract.get_contract()
    print("Declared TimeOracle Contract")
    deployer = DeployContract(
        declared_time_oracle_contract,
        deployer_config,
        sierra_class_hash_time_oracle,
        constructor_args={}
    )
    deployed_time_oracle_contract = await deployer.deploy()
    print(f"Deployed TimeOracle Contract to address: {hex(deployed_time_oracle_contract.address)}")
    ContractDataWriter.write_data(
        deploy_env=args.deploy_env, 
        abi=get_abi(declared_time_oracle_contract),
        chain_id=deployer_config.chain_id,
        contract_name="TimeOracle", 
        address = deployed_time_oracle_contract.address
    )
    print()

    ### FractionVault
    print("Declaring FractionVaultFactory Contract")
    initialized_faction_vault_factory_contract = InitializeContractData(contract_name="FractionVault")
    casm_class_hash_faction_vault_factory, compiled_contract_faction_vault_factory, sierra_class_hash_faction_vault_factory = initialized_faction_vault_factory_contract.read_contract_file_data()
    declared_vault_factory_contract = DeclareContract(
        deployer_config,
        casm_class_hash_faction_vault_factory,
        compiled_contract_faction_vault_factory,
        sierra_class_hash_faction_vault_factory
    )
    declared_vault_factory_contract = await declared_vault_factory_contract.get_contract()
    print("Declared FractionVaultFactory Contract")
    deployer = DeployContract(
        declared_vault_factory_contract,
        deployer_config,
        sierra_class_hash_faction_vault_factory,
        constructor_args={
            "time_oracle_address": deployed_time_oracle_contract.address,
            "nft_contract_class_hash": sierra_class_hash_faction_vault_factory
        }
    )
    deployed_vault_factory_contract = await deployer.deploy()
    print(f"Deployed FractionVaultFactory Contract to address: {hex(deployed_vault_factory_contract.address)}")
    ContractDataWriter.write_data(
        deploy_env=args.deploy_env, 
        abi=get_abi(declared_vault_factory_contract),
        chain_id=deployer_config.chain_id,
        contract_name="FractionVaultFactory", 
        address = deployed_vault_factory_contract.address
    )
    print()

    return deployed_time_oracle_contract.address


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
        print(f"Current balance: {current_account_balance} funding account to {current_account_balance + int(1e18)}")
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
    oracle_address = asyncio.run(main(args.deploy_env))
    if args.deploy_env == "dev":
        asyncio.run(fund_account(args.deploy_env))
    print(f"Time oracle address: {oracle_address}")
        