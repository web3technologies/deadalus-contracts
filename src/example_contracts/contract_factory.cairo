use starknet::ClassHash;


#[starknet::interface]
trait IContractFactory<TContractState>{
    fn deploy_contract(ref self: TContractState, initial_owner: felt252);
    fn set_contract_classhash(ref self: TContractState, class_hash: ClassHash);
}


#[starknet::contract]
mod ContractFactory{

    use core::poseidon::poseidon_hash_span;
    use super::IContractFactory;
    use starknet::syscalls::deploy_syscall;
    use starknet::{
        ClassHash,
        ContractAddress,
        SyscallResult,
        get_caller_address,
        get_contract_address,
        get_tx_info
    };

    #[event]
    #[derive(Drop, starknet::Event)]
    enum Event {
        CounterDeploy: CounterDeploy,
    }

    #[derive(Drop, starknet::Event)]
    struct CounterDeploy {
        #[key]
        contract: ContractAddress,
        counter_id: u256
    }


    #[storage]
    struct Storage{
        owner: ContractAddress,
        contracts: LegacyMap::<ContractAddress, u256>,
        contract_class_hash: ClassHash, // need this in order to deploy,
        counter_id: u256
    }

    #[constructor]
    fn constructor(ref self: ContractState, class_hash: ClassHash){
        self.owner.write(get_caller_address());
        self.contract_class_hash.write(class_hash);
    }

    #[abi(embed_v0)]
    impl ContractFactory of IContractFactory<ContractState>{

        fn deploy_contract(ref self: ContractState, initial_owner: felt252){
            let caller_address = get_caller_address();
            let call_data = array!['test', initial_owner].span(); // empty call data
            let transaction_nonce: felt252 = get_tx_info().unbox().nonce;
            let deploy_result: SyscallResult = deploy_syscall(
                self.contract_class_hash.read(),
                generate_salt(caller_address, transaction_nonce), // important for preventing address collision
                call_data,
                deploy_from_zero: false
            );
            match deploy_result {
                Result::Ok((_contract_address, _return_data)) =>{
                    let counter_id = self.counter_id.read();
                    self.contracts.write(_contract_address, counter_id);
                    self.counter_id.write(counter_id + 1);
                    self.emit(CounterDeploy{contract: _contract_address, counter_id: counter_id})
                },
                Result::Err(_) => {
                    panic!("error in contract call");
                }
            }
        }
        fn set_contract_classhash(ref self: ContractState, class_hash: ClassHash){
            let caller: ContractAddress = get_caller_address();
            assert(caller == self.owner.read(), 'caller is not owner');
            self.contract_class_hash.write(class_hash);
        }
    }

    // needed to provide randomness to the contract address
    fn generate_salt(address: ContractAddress, nonce: felt252) -> felt252{
        let values = array![address.into(), nonce];
        let salt = poseidon_hash_span(values.span());
        salt
    }

}