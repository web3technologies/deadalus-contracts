use starknet::ContractAddress;

#[starknet::interface]
trait ICounter<TContractState> {
    fn increment(ref self: TContractState);
    fn decrement(ref self: TContractState);
    fn set_owner(ref self: TContractState, new_owner: ContractAddress);
    fn get_count(self: @TContractState) -> u256;
}


#[starknet::contract]
mod Counter {
    use super::ICounter;

    use starknet::get_caller_address;
    use starknet::ContractAddress;

    #[storage]
    struct Storage {
        owner: ContractAddress,
        count: u256
    }

    #[constructor]
    fn constructor(ref self: ContractState) {
        self.owner.write(get_caller_address());
    }

    #[abi(embed_v0)]
    impl Counter of ICounter<ContractState> {
        fn increment(ref self: ContractState) {
            assert(get_caller_address() == self.owner.read(), 'caller is not owner');
            self.count.write(self.count.read() + 1);
        }
        fn decrement(ref self: ContractState) {
            assert(get_caller_address() == self.owner.read(), 'caller is not owner');
            self.count.write(self.count.read() - 1);
        }
        fn set_owner(ref self: ContractState, new_owner: ContractAddress) {
            // need to refine this logic
            // should owner transfer ownership to factory or should factory be able to claim ownership in same function call
            assert(get_caller_address() == self.owner.read(), 'caller is not owner');
            self.owner.write(new_owner)
        }
        fn get_count(self: @ContractState) -> u256 {
            self.count.read()
        }
    }
}
