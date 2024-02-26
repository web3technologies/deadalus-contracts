import asyncio
from decouple import config

from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.models import StarknetChainId

from deploy_modules import DeployerConfig, InitializeContractData, DeclareContract, DeployContract

## address to send second nft and ensure caller works properly
ACCOUNT_ADDRESS_2 = "0x3805b27d17d628cc06463b7feb71a9373524d15b44117ce9e68208783bce30c"
FUNCTION_SELECTOR = "0x003ed4ef5a86416c4497bd25609bebf337f226baca0782fe076b9594a2ee7335"

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
    for _ in range(2):
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
            "time_oracle_address": deployed_time_oracle_contract.address,
            "nft_contract_class_hash": sierra_class_hash_nft
        }
    )
    deployed_vault_contract = await deployer.deploy()
    for idx, flat_contract_address in enumerate(flats):

        # set oracle time
        tx = await deployed_time_oracle_contract.functions["set_time"].invoke_v3(
            unix_timestamp=1708907167,
            auto_estimate=True
        )
        await deployer_config.account.client.wait_for_tx(tx.hash)
        print("oracle updated")
        
        curr_time = await deployed_time_oracle_contract.functions["get_time"].call()
        assert curr_time[0] == 1708907167

        flat_contract = await Contract.from_address(address=flat_contract_address, provider=deployer_config.account)

        get_contract_id = await deployed_vault_contract.functions["get_contract_id"].call()
        assert get_contract_id[0] == idx 
        
        transfer_flat = await flat_contract.functions["transfer_ownership"].invoke_v3(
            new_owner=deployed_vault_contract.address,
            auto_estimate=True
        )
        invocation = await deployed_vault_contract.functions["deposit_contract"].invoke_v3(
            **{"deposit_contract_address": flat_contract_address},
            auto_estimate=True
        )
        add_function_invocation = await deployed_vault_contract.functions["add_function"].invoke_v3(
            function_selector=int(FUNCTION_SELECTOR, 16),
            require_owner=True,
            auto_estimate=True
        )

        get_contract_id = await deployed_vault_contract.functions["get_contract_id"].call()
        assert get_contract_id[0] == idx + 1

        get_flat_door_state = await flat_contract.functions["get_door_state"].call()
        assert get_flat_door_state[0] == False
        ## then need to transfer nft to address 2
        ## then check caller is id 1
        ## then update time > 45 and assert controller is address 2
        controller_call = await deployed_vault_contract.functions["get_controller"].call(
            deposited_contract_address=flat_contract_address
        )
        current_controller = hex(controller_call[0])
        assert current_controller == deployer_config.account_address

        # call the toogle door
        call_toogle_door = await deployed_vault_contract.functions["call_function"].invoke_v3(
            contract_address=flat_contract_address,
            function_selector=int(FUNCTION_SELECTOR, 16),
            call_data=[],
            auto_estimate=True
        )
        get_flat_door_state = await flat_contract.functions["get_door_state"].call()
        assert get_flat_door_state[0] == True
        
        # transfer nft 2 to a new user
        # then call the oracle to update time
        # then owner of nft2 should be the current controller
        get_nft_address_call = await deployed_vault_contract.functions["get_nft_address"].call(deposited_contract_address=flat_contract_address)
        nft_contract = await Contract.from_address(address=get_nft_address_call[0], provider=deployer_config.account)
        transfer_nft = await nft_contract.functions["transfer_from"].invoke_v3(
            **{
                "from":int(deployer_config.account_address,16), 
                "to": int(ACCOUNT_ADDRESS_2,16), 
                "token_id": 2
            },
            auto_estimate=True
        )
        nft_id_2_owner = await nft_contract.functions["owner_of"].call(2)
        nft_id_2_owner = nft_id_2_owner[0]
        assert hex(nft_id_2_owner) == ACCOUNT_ADDRESS_2

        tx = await deployed_time_oracle_contract.functions["set_time"].invoke_v3(
            unix_timestamp=1708907270,
            auto_estimate=True
        )
        await deployer_config.account.client.wait_for_tx(tx.hash)
        curr_time = await deployed_time_oracle_contract.functions["get_time"].call()
        assert curr_time[0] == 1708907270

        ## check nft id 2 is owned by account address 2
        controller_call_2 = await deployed_vault_contract.functions["get_controller"].call(deposited_contract_address=flat_contract_address)
        current_controller_2 = hex(controller_call_2[0])
        assert current_controller_2 == ACCOUNT_ADDRESS_2

        key_pair_account_2 = KeyPair.from_private_key(config("UT_PRIVATE_KEY"))
        client_account_2 = FullNodeClient(node_url=config("DEV_NODE_URL"))
        account_account_2 = Account(
            address=ACCOUNT_ADDRESS_2,
            client=client_account_2,
            key_pair=key_pair_account_2,
            chain=StarknetChainId.GOERLI
        )
        deployed_vault_contract_for_account_2 = await Contract.from_address(deployed_vault_contract.address, provider=account_account_2)
        call_function_invocation = await deployed_vault_contract_for_account_2.functions["call_function"].invoke_v3(
            contract_address=flat_contract_address,
            function_selector=int(FUNCTION_SELECTOR, 16),
            call_data=[],
            auto_estimate=True
        )
        get_flat_door_state = await flat_contract.functions["get_door_state"].call()
        assert get_flat_door_state[0] == False

    deposited_contracts = await deployed_vault_contract.functions["get_deposited_contracts"].call()
    assert deposited_contracts[0] == flats

if __name__ == "__main__":

    asyncio.run(test())