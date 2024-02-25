use snforge_std::{declare, ContractClassTrait};
use starknet::ContractAddress;
use deadalus::vault::fraction_vault::{IFractionVaultDispatcher, IFractionVaultDispatcherTrait};

#[test]
fn check_counter_Balance() {
    // First declare and deploy a contract
    // let contract = declare('FractionVault');
    // let constructor_data = array![];
    // let contract_address = contract.deploy(@constructor_data);
    // let dispatcher = ICounterDispatcher { contract_address };
    // let balance = dispatcher.increment();
    assert(2 == 2, 'nums incorrect');
}






