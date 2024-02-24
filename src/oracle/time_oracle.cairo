#[starknet::interface]
trait ITimeOracle<TContractState>{
    fn set_time(ref self: TContractState, unix_timestamp: u256);
    fn get_time(ref self: TContractState) -> u256;
}

#[starknet::contract]
mod TimeOracle{

    use super::{ITimeOracle};
    use starknet::ContractAddress;

    #[storage]
    struct Storage{
        unix_time: u256,
        owner: ContractAddress 
    }

    #[abi(embed_v0)]
    impl TimeOracle of ITimeOracle<ContractState>{
        
        fn set_time(ref self: ContractState, unix_timestamp: u256){
            self.unix_time.write(unix_timestamp);
        }

        fn get_time(ref self: ContractState) -> u256{
            self.unix_time.read()
        }
    }
}

