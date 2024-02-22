use starknet::ContractAddress;
use starknet::ClassHash;


#[derive(Copy, Drop, starknet::Store)]
struct ContractFunction{
    name: felt252,
    selector: felt252,
    require_owner: bool
}


#[derive(Copy, Drop, starknet::Store)]
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
    fn call_function(ref self: TContractState, contract_address: ContractAddress, function_name: felt252, call_data: Array<felt252>);
    fn add_function(ref self: TContractState, function_name: felt252, function_selector: felt252, require_owner: bool);
}


#[starknet::contract]
mod FractionVaultFactory {

    use super::{IFractionVaultFactory, FractionPeriod, ContractFunction};
    use starknet::ClassHash;
    use starknet::ContractAddress;
    
    use starknet::get_caller_address;
    use starknet::get_contract_address;
    use starknet::call_contract_syscall;

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
    impl FracationVaultFactory of IFractionVaultFactory<ContractState>{
        fn deposit_contract(
            ref self: ContractState, 
                name: felt252, 
                contract_address: ContractAddress,
                // fraction_period: FractionPeriod
            ){
                // need to check to make sure the contract has not already been deposited
                // assert(self.counter_contracts.read(contract_address) == 0, "contract has already been deposited");
                self.counter_contracts_to_user.write(contract_address, get_caller_address());
                let call_data = array![].span(); // need to access contract address to set as the owner
                let result = call_contract_syscall(
                    contract_address, 
                    self.functions.read('set_owner').selector, 
                    call_data
                );
                // should we create a liquidity pool automatically?
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

        fn add_function(ref self: ContractState, function_name: felt252, function_selector: felt252, require_owner: bool){
            assert(get_caller_address() == self.owner.read(), 'caller is not owner');
            let function = ContractFunction{
                name: function_name, 
                selector: function_selector,
                require_owner: require_owner
            };
            self.functions.write(function_name, function);
        }
    }

}