use starknet::ContractAddress;

#[starknet::interface]
trait ICounter<TContractState> {
    fn increment(ref self: TContractState);
    fn decrement(ref self: TContractState);
    fn set_owner(ref self: TContractState, new_owner: ContractAddress);
    fn get_count(self: @TContractState);
}


#[starknet::contract]
mod Counter {

    use super::ICounter;

    use starknet::get_caller_address;
    use starknet::ContractAddress;

    #[storage]
    struct Storage{
        owner: ContractAddress,
        count: u256
    }

    #[constructor]
    fn constructor(ref self: ContractState, _owner: ContractAddress){
        self.owner.write(_owner);
    }


    #[abi(embed_v0)]
    impl Counter of ICounter<ContractState>{
        fn increment(ref self: ContractState){
            self.count.write(self.count.read() + 1);
        }
        fn decrement(ref self: ContractState){
            self.count.write(self.count.read() -1);
        }
        fn set_owner(ref self: ContractState, new_owner: ContractAddress){
            self.owner.write(new_owner)
        }
        fn get_count(self: @ContractState){
            self.count;
        }
    }

}