use starknet::ContractAddress;
use starknet::ClassHash;


enum FractionPeriod {
   DAILY,
   MONTHLY,
   YEARLY 
}


#[starknet::interface]
trait IFractionVaultFactory<TContractState>{
    fn deposit_contract(
        ref self: TContractState, 
            name: felt252, 
            contract_address: ContractAddress,
            // fraction_period: FractionPeriod
        );
}


#[starknet::contract]
mod FractionVaultFactory {

    use super::IFractionVaultFactory;
    use super::FractionPeriod;
    use starknet::ClassHash;
    use starknet::ContractAddress;
    
    use starknet::get_caller_address;

    #[storage]
    struct Storage{
        owner: ContractAddress,
        erc20_token_class_hash: ClassHash,
    }

    #[constructor]
    fn constructor(ref self: ContractState, erc20_class_hash: ClassHash){
        self.owner.write(get_caller_address());
        self.erc20_token_class_hash.write(erc20_class_hash);
    }

    #[abi(embed_v0)]
    impl FracationVaultFactory of IFractionVaultFactory<ContractState>{
        fn deposit_contract(
            ref self: ContractState, 
                name: felt252, 
                contract_address: ContractAddress,
                // fraction_period: FractionPeriod
            ){

        }
    }

}