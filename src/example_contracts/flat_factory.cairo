pub use starknet::{ContractAddress, ClassHash};

#[starknet::interface]
pub trait IFlatFactory<TContractState> {
    fn create_flat(ref self: TContractState) -> ContractAddress;
    fn update_counter_class_hash(ref self: TContractState, counter_class_hash: ClassHash);
}


#[starknet::contract]
pub mod FlatFactory {
    use core::poseidon::poseidon_hash_span;
    use starknet::{
        ContractAddress, 
        ClassHash, 
        SyscallResultTrait, 
        get_caller_address,
        get_tx_info
    };
    use starknet::syscalls::deploy_syscall;
    use deadalus::utils::storage::StoreSpanFelt252;

    #[storage]
    struct Storage {
        init_argument: Span<felt252>,
        class_hash: ClassHash,
        contract_id: u128,
    }

    #[constructor]
    fn constructor(
        ref self: ContractState, 
        class_hash: ClassHash
    ) {
        self.class_hash.write(class_hash);
        self.contract_id.write(1);
    }

    #[event]
    #[derive(Drop, starknet::Event)]
    enum Event {
        ContractDeployed: ContractDeployed,
    }
    #[derive(Drop, starknet::Event)]
    struct ContractDeployed {
        deployed_address: ContractAddress
    }

    #[abi(embed_v0)]
    impl FlatFactory of super::IFlatFactory<ContractState> {

        fn create_flat(ref self: ContractState) -> ContractAddress {
            let caller_address = get_caller_address();
            let felt_caller: felt252 = caller_address.into();
            let constructor_calldata = array!['test', felt_caller];
            // // Contract deployment
            let class_hash = self.class_hash.read();
            let transaction_nonce: felt252 = get_tx_info().unbox().nonce;
            let deploy_result = deploy_syscall(
                class_hash, 
                generate_salt(caller_address, transaction_nonce), 
                constructor_calldata.span(), 
                true
            );
            let deployed_address:ContractAddress = match deploy_result {
                Result::Ok((_contract_address, _return_data)) =>{
                    self.contract_id.write(self.contract_id.read() + 1);
                    self.emit(ContractDeployed { deployed_address: _contract_address});
                    _contract_address
                },
                Result::Err(_) => {
                    panic!("error in contract call")
                }
            };
            deployed_address
        }

        fn update_counter_class_hash(ref self: ContractState, counter_class_hash: ClassHash) {
            self.class_hash.write(counter_class_hash);
        }

    }

    // needed to provide randomness to the contract address
    fn generate_salt(address: ContractAddress, nonce: felt252) -> felt252{
        let values = array![address.into(), nonce];
        let salt = poseidon_hash_span(values.span());
        salt
    }
}

