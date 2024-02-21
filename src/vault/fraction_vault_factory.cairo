use starknet::ContractAddress;
use starknet::ClassHash;

#[starknet::contract]
mod FractionVaultFactory {
    use starknet::ClassHash;
    use starknet::ContractAddress;
    
    #[storage]
    struct Storage{
        owner: ContractAddress,
        erc20_token_class_hash: ClassHash,
    }
}