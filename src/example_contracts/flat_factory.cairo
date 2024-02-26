pub use starknet::{ContractAddress, ClassHash};

#[starknet::interface]
pub trait ICounterFactory<TContractState> {
    fn get_init_argument(self: @TContractState) -> Span<felt252>;

    fn create_flat(ref self: TContractState) -> ContractAddress;

    fn create_flat_with(ref self: TContractState, init_argument: Span<felt252>) -> ContractAddress;

    fn update_init_argument(ref self: TContractState, init_argument: Span<felt252>);

    fn update_counter_class_hash(ref self: TContractState, counter_class_hash: ClassHash);
}


#[starknet::contract]
pub mod FlatFactory {
    use starknet::{ContractAddress, ClassHash, SyscallResultTrait};
    use starknet::syscalls::deploy_syscall;
    use deadalus::utils::storage::StoreSpanFelt252;

    #[storage]
    struct Storage {
        init_argument: Span<felt252>,
        counter_class_hash: ClassHash,
        contract_id: u128,
    }

    #[constructor]
    fn constructor(ref self: ContractState, init_argument: Span<felt252>, class_hash: ClassHash) {
        self.init_argument.write(init_argument);
        self.counter_class_hash.write(class_hash);
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
    impl Factory of super::ICounterFactory<ContractState> {
        fn create_flat_with(
            ref self: ContractState, init_argument: Span<felt252>
        ) -> ContractAddress {
            // Contructor arguments
            let mut constructor_calldata: Span<felt252> = init_argument;

            // Contract deployment
            let (deployed_address, _) = deploy_syscall(
                self.counter_class_hash.read(), 0, constructor_calldata, false
            )
                .unwrap_syscall();
            self.contract_id.write(self.contract_id.read() + 1);
            self.emit(ContractDeployed { deployed_address: deployed_address });
            deployed_address
        }

        fn create_flat(ref self: ContractState) -> ContractAddress {
            self.create_flat_with(self.init_argument.read())
        }

        fn update_init_argument(ref self: ContractState, init_argument: Span<felt252>) {
            self.init_argument.write(init_argument);
        }

        fn update_counter_class_hash(ref self: ContractState, counter_class_hash: ClassHash) {
            self.counter_class_hash.write(counter_class_hash);
        }

        fn get_init_argument(self: @ContractState) -> Span<felt252> {
            self.init_argument.read()
        }
    }
}

