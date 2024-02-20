

#[starknet::contract]
mod Counter {

    use starknet::get_caller_address;
    use starknet::ContractAddress;

    #[storage]
    struct Storage{
        owner: ContractAddress,
    }

}