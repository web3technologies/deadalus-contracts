use starknet::ContractAddress;
use starknet::ClassHash;


#[derive(Copy, Drop, starknet::Store)]
struct ContractFunction{
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
            deposit_contract_address: ContractAddress,
            fraction_period: FractionPeriod
        );
    fn call_function(ref self: TContractState, contract_address: ContractAddress, function_selector: felt252, call_data: Array<felt252>);
    fn add_function(ref self: TContractState, function_selector: felt252, require_owner: bool);
    fn get_controller(ref self: TContractState, deposited_contract_address: ContractAddress) -> ContractAddress;
}


#[starknet::contract]
mod FractionVault {

    use core::poseidon::poseidon_hash_span;
    use core::traits::TryInto;
    use core::array::SpanTrait;
    use core::keccak::keccak_u256s_le_inputs;
    use core::result::Result;
    use super::{IFractionVault, FractionPeriod, ContractFunction};
    use starknet::{SyscallResult, ClassHash, ContractAddress, Felt252TryIntoContractAddress};

    use starknet::{
        deploy_syscall,
        get_caller_address, 
        get_contract_address,
        get_tx_info, 
        call_contract_syscall, 
        get_block_info, // get block timestamp
        contract_address_try_from_felt252
    };
    
    use deadalus::oracle::time_oracle::{ITimeOracleDispatcher, ITimeOracleDispatcherTrait};
    // use deadalus::fraction::fraction_nft::{IFractionNFTDispatcher, IFractionNFTDispatcherTrait};

    #[storage]
    struct Storage{
        owner: ContractAddress,
        deposited_contracts_to_nft_contract: LegacyMap::<ContractAddress, ContractAddress>,
        functions: LegacyMap::<felt252, ContractFunction>, // map the function name to the function selector hash
        time_oracle_address: ContractAddress,
        time_oracle_selector: felt252,
        nft_contract_class_hash: ClassHash
    }

    #[constructor]
    fn constructor(
        ref self: ContractState,
        time_oracle_address: ContractAddress,
        nft_contract_class_hash: ClassHash
        ){
        self.owner.write(get_caller_address());
        self.time_oracle_address.write(time_oracle_address);
        self.nft_contract_class_hash.write(nft_contract_class_hash);
    }

    #[abi(embed_v0)]
    impl FracationVault of IFractionVault<ContractState>{
        fn deposit_contract(
            ref self: ContractState, 
                deposit_contract_address: ContractAddress,
                fraction_period: FractionPeriod
            ){
                let current_caller = get_caller_address();
                let call_data = array![].span(); // need to access contract address to set as the owner
                let result = call_contract_syscall(
                    deposit_contract_address,
                    self.functions.read('set_owner').selector, 
                    call_data
                );
                match result{
                    Result::Ok(_) =>{},
                    Result::Err(_) => {panic!("Error in set owner call");}
                }
                // deploy nft contract
                let current_caller_felt: felt252 = current_caller.into();
                let nft_call_data = array!['Fraction', 'FRT', current_caller_felt, '2'].span();
                let transaction_nonce: felt252 = get_tx_info().unbox().nonce;
                let deploy_result: SyscallResult = deploy_syscall(
                    self.nft_contract_class_hash.read(),
                    generate_salt(current_caller, transaction_nonce), // important for preventing address collision
                    nft_call_data,
                    deploy_from_zero: false
                );
                match deploy_result {
                    Result::Ok((_contract_address, _return_data)) =>{
                        self.deposited_contracts_to_nft_contract.write(deposit_contract_address, _contract_address);
                    },
                    Result::Err(_) => {
                        panic!("error in deploy");
                    }
                }
        }
        
        fn call_function(
            ref self: ContractState, 
            contract_address: ContractAddress, 
            function_selector: felt252, 
            call_data: Array<felt252>
        ){
            let function = self.functions.read(function_selector);
            if function.require_owner{
                let caller = get_caller_address();
                let current_controller = self.get_controller(contract_address);
                assert(current_controller == caller, 'Caller is not in control');
            }
            let result = call_contract_syscall(
                contract_address,     
                function.selector, 
                call_data.span()
            );
            match result{
                    Result::Ok(_) =>{},
                    Result::Err(_) => {panic!("Error in set contract syscall");}
            }
        }
        // validate transfer_ownership and withdraw function and approve
        fn add_function(
            ref self: ContractState, 
            function_selector: felt252, 
            require_owner: bool
        ){
            let function = ContractFunction{
                selector: function_selector, // can use keccak algo to calculate selector name instead of requiring input?
                require_owner: require_owner
            };
            self.functions.write(function_selector, function);
        }

        fn get_controller(
            ref self: ContractState, 
            deposited_contract_address: ContractAddress
        ) -> ContractAddress{
            let oracle_address = self.time_oracle_address.read();
            let dispatcher = ITimeOracleDispatcher{contract_address: oracle_address};
            let let_time_result_uinx = dispatcher.get_time();
            let nft_address = self.deposited_contracts_to_nft_contract.read(deposited_contract_address);
            let interval = let_time_result_uinx % 60;
            let mut nft_id = '1';
            if interval > 30 {
                nft_id = '2';
            };
            let result = call_contract_syscall(
                nft_address,     
                selector!("ownerOf"),
                array![nft_id].span()
            );
            match result {
                Result::Ok(_address)=>{
                    let tmp = *_address.at(0);
                    let tmp_addr: ContractAddress = tmp.try_into().unwrap();
                    tmp_addr
                },
                Result::Err(_) => {
                    panic!("error in contract call");
                    get_caller_address()
                }
            }
        }
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

    // needed to provide randomness to the contract address
    fn generate_salt(address: ContractAddress, nonce: felt252) -> felt252{
        let values = array![address.into(), nonce];
        let salt = poseidon_hash_span(values.span());
        salt
    }

}



// how to serialize mapping data to FE
// how to use ?
// how to configure sntest