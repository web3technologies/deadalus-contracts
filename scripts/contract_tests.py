import asyncio
import argparse
from deploy_modules import DeployerConfig, InitializeContractData, DeclareContract, DeployContract


async def test():

    deployer_config = DeployerConfig.get_config('dev', "GOERLI").init_account()


    ### NFT Declare
    print("Delcaring NFT Contract")
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

    flats = []
    ## Flat Declare
    print("Delcaring Flat Contract")
    initialized_flat_contract = InitializeContractData(contract_name="Flat")
    casm_class_hash_flat, compiled_contract_flat, sierra_class_hash_flat = initialized_flat_contract.read_contract_file_data()
    declared_flat_contract = DeclareContract(
        deployer_config,
        casm_class_hash_flat,
        compiled_contract_flat,
        sierra_class_hash_flat
    )
    declared_flat_contract = await declared_flat_contract.get_contract()
    print("Declared Flat Contract")
    for _ in range(1):
        deployer = DeployContract(
            declared_flat_contract,
            deployer_config,
            sierra_class_hash_flat,
            constructor_args={
                "image": "test",
                "initial_owner": int(deployer_config.account_address,16)
            }
        )
        deployed_flat_contract = await deployer.deploy()
        print('deployed')
        flats.append(deployed_flat_contract.address)


    ### vault 
    print("Declaring FractionVault Contract")
    initialized_faction_vault_contract = InitializeContractData(contract_name="FractionVault")
    casm_class_hash_faction_vault, compiled_contract_faction_vault, sierra_class_hash_faction_vault = initialized_faction_vault_contract.read_contract_file_data()
    declared_vault_contract = DeclareContract(
        deployer_config,
        casm_class_hash_faction_vault,
        compiled_contract_faction_vault,
        sierra_class_hash_faction_vault
    )
    declared_vault_contract = await declared_vault_contract.get_contract()
    print("Declared FractionVault Contract")
    deployer = DeployContract(
        declared_vault_contract,
        deployer_config,
        sierra_class_hash_faction_vault,
        constructor_args={
            "time_oracle_address": '',
            "nft_contract_class_hash": sierra_class_hash_nft
        }
    )
    deployed_vault_contract = await deployer.deploy()
    for flat_contract_address in flats:
        invocation = await deployed_vault_contract.functions["deposit_contract"].invoke_v3(
            **{"deposit_contract_address": int(hex(flat_contract_address),16)},
            auto_estimate=True
        )
        print()
    print()

if __name__ == "__main__":

    asyncio.run(test())