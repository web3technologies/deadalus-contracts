use starknet::ContractAddress;
use starknet::ClassHash;


#[derive(Copy, Drop, starknet::Store)]
struct ContractFunction{
    name: felt252,
    selector: felt252,
    require_owner: bool
}


#[derive(Copy, Drop, Serde, starknet::Store)]
enum FractionPeriod {
    MINUTELY,
    HOURLY,
    DAILY,
    MONTHLY,
    YEARLY 
}

#[starknet::interface]
trait IFractionVault<TContractState>{
    fn deposit_contract(
        ref self: TContractState, 
            name: felt252, 
            contract_address: ContractAddress,
            fraction_period: FractionPeriod
        );
    fn call_function(ref self: TContractState, contract_address: ContractAddress, function_name: felt252, call_data: Array<felt252>);
    fn add_function(ref self: TContractState, function_name: felt252, function_selector: felt252, require_owner: bool);
    // fn get_controller(ref self: TContractState) -> ContractAddress;
}



#[starknet::contract]
mod FractionVault {

    use super::{IFractionVault, FractionPeriod, ContractFunction};
    use starknet::{ClassHash, ContractAddress};
    use starknet::{
        get_caller_address, 
        get_contract_address, 
        call_contract_syscall, 
        get_block_info, // get block timestamp
    };
    

    #[storage]
    struct Storage{
        owner: ContractAddress,
        erc20_token_class_hash: ClassHash,
        counter_contracts_to_user: LegacyMap::<ContractAddress,ContractAddress>,
        functions: LegacyMap::<felt252, ContractFunction> // map the function name to the function selector hash
    }

    #[constructor]
    fn constructor(ref self: ContractState, erc20_class_hash: ClassHash){
        self.owner.write(get_caller_address());
        self.erc20_token_class_hash.write(erc20_class_hash);
    }

    #[abi(embed_v0)]
    impl FracationVault of IFractionVault<ContractState>{
        fn deposit_contract(
            ref self: ContractState, 
                name: felt252, 
                contract_address: ContractAddress,
                fraction_period: FractionPeriod
            ){
                // need to check to make sure the contract has not already been deposited
                // assert(self.counter_contracts.read(contract_address) == 0, "contract has already been deposited");
                let call_data = array![].span(); // need to access contract address to set as the owner
                let result = call_contract_syscall(
                    contract_address, 
                    self.functions.read('set_owner').selector, 
                    call_data
                );
                self.counter_contracts_to_user.write(contract_address, get_caller_address());
                let token_supply = process_fraction_period(fraction_period);
                // deploy nft contract
                // mint to all nfts to caller

        }
        
        fn call_function(
            ref self: ContractState, 
            contract_address: ContractAddress, 
            function_name: felt252, 
            call_data: Array<felt252>
        ){
            let function = self.functions.read(function_name);
            if function.require_owner{
                let caller = get_caller_address();
                assert(self.owner.read() == caller, 'caller is not owner');
            }
            let result = call_contract_syscall(
                contract_address,     
                function.selector, 
                call_data.span()
            );
        }
        // validate transfer_ownership and withdraw function and approve
        fn add_function(ref self: ContractState, function_name: felt252, function_selector: felt252, require_owner: bool){
            assert(get_caller_address() == self.owner.read(), 'caller is not owner');
            let function = ContractFunction{
                name: function_name, 
                selector: function_selector,
                require_owner: require_owner
            };
            self.functions.write(function_name, function);
        }

        // fn get_controller(ref self: ContractState) -> ContractAdress{
        //    
        // }

        // add distribute function
    }
    


    fn process_fraction_period(fraction_period: FractionPeriod) -> u256{
        let value = match fraction_period{
            FractionPeriod::MINUTELY => {31536000_u256},
            FractionPeriod::HOURLY => {8760_u256},
            FractionPeriod::DAILY => { 365_u256 },
            FractionPeriod::MONTHLY => {12_u256},
            FractionPeriod::YEARLY => {1_u256},
        };
        value
    }

}