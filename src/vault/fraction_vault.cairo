use starknet::ContractAddress;
use starknet::ClassHash;


#[derive(Copy, Drop,Serde,starknet::Store)]
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
            deposit_contract_address: ContractAddress
        ) -> ContractAddress;
    fn call_function(ref self: TContractState, contract_address: ContractAddress, function_selector: felt252, call_data: Array<felt252>);
    fn add_function(ref self: TContractState, function_selector: felt252, require_owner: bool);
    fn get_controller(self: @TContractState, deposited_contract_address: ContractAddress) -> ContractAddress;
    fn get_nft_address(self: @TContractState, deposited_contract_address: ContractAddress) -> ContractAddress;
    fn get_function(self: @TContractState, selector: felt252) -> ContractFunction;
    fn get_deposited_contracts(self: @TContractState) -> Array<ContractAddress>;
    fn get_contract_id(self: @TContractState) -> u256;
}


#[starknet::contract]
mod FractionVault {

    use core::poseidon::poseidon_hash_span;
    use core::traits::TryInto;
    use core::array::{SpanTrait, ArrayTrait};
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


    #[event]
    #[derive(Drop, starknet::Event)]
    enum Event {
        ContractDeposit: ContractDeposit,
    }

    #[derive(Drop, starknet::Event)]
    struct ContractDeposit {
        contract: ContractAddress,
        nft_contract: ContractAddress
    }

    #[storage]
    struct Storage{
        owner: ContractAddress,
        deposited_contracts_to_nft_contract: LegacyMap::<ContractAddress, ContractAddress>,
        functions: LegacyMap::<felt252, ContractFunction>, // map the function name to the function selector hash
        time_oracle_address: ContractAddress,
        nft_contract_class_hash: ClassHash,
        contract_id: u256,
        contract_id_to_contract: LegacyMap::<u256, ContractAddress> 
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
                deposit_contract_address: ContractAddress
            ) -> ContractAddress{
                let current_caller = get_caller_address();
                // deploy nft contract
                let num_nft: u256 = 2;
                let current_caller_felt: felt252 = current_caller.into();
                let mut nft_call_data = array!['Fraction', 'FRT', current_caller_felt];
                num_nft.serialize(ref nft_call_data);
                let transaction_nonce: felt252 = get_tx_info().unbox().nonce;
                let deploy_result: SyscallResult = deploy_syscall(
                    self.nft_contract_class_hash.read(),
                    generate_salt(current_caller, transaction_nonce), // important for preventing address collision
                    nft_call_data.span(),
                    true
                );
                let nft_address: ContractAddress = match deploy_result {
                    Result::Ok((_nft_contract_address, _return_data)) =>{
                        let current_contract_id = self.contract_id.read();
                        self.contract_id_to_contract.write(current_contract_id, deposit_contract_address);
                        self.contract_id.write(current_contract_id + 1);
                        self.deposited_contracts_to_nft_contract.write(deposit_contract_address, _nft_contract_address);
                        self.emit(ContractDeposit{contract: deposit_contract_address, nft_contract:_nft_contract_address});
                        _nft_contract_address
                    },
                    Result::Err(_) => {
                        panic!("error in deploy")
                    }
                };
                nft_address
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
            call_contract_syscall(
                contract_address,     
                function.selector, 
                call_data.span()
            ).expect('error in contract call');
        }
        // validate transfer_ownership and withdraw function and approve
        fn add_function(
            ref self: ContractState, 
            function_selector: felt252, 
            require_owner: bool
        ){
            let function = ContractFunction{
                selector: function_selector,
                require_owner: require_owner
            };
            self.functions.write(function_selector, function);
        }

        fn get_controller(
            self: @ContractState, 
            deposited_contract_address: ContractAddress
        ) -> ContractAddress{
            let oracle_address = self.time_oracle_address.read();
            // // let dispatcher = ITimeOracleDispatcher{contract_address: oracle_address};
            let oracle_call = call_contract_syscall(
                oracle_address,     
                selector!("get_time"), 
                array![].span()
            );
            let current_unix_time: u256 = match oracle_call{
                Result::Ok(return_span) =>{
                    let casted_time = *return_span.at(0);
                    let new_time: u256 = casted_time.try_into().unwrap();
                    new_time
                },
                Result::Err(_)=>{
                    panic!("failure in call")
                }
            };
            let time_result_unix_interval = current_unix_time % 90;
            let nft_id: u256 = if time_result_unix_interval > 45 {
                let nft_id: u256 = 2;
                nft_id
            } else{
                let nft_id: u256 = 1;
                nft_id
            };
            let mut arr = array![];
            nft_id.serialize(ref arr);
            let result = call_contract_syscall(
                self.deposited_contracts_to_nft_contract.read(deposited_contract_address),     
                selector!("owner_of"),
                arr.span()
            );
            let address = result.expect('error in contract call');
            let tmp = *address.at(0);
            let nft_owner_address: ContractAddress = tmp.try_into().unwrap();
            nft_owner_address
        }

        fn get_nft_address(self: @ContractState, deposited_contract_address: ContractAddress) -> ContractAddress{
            self.deposited_contracts_to_nft_contract.read(deposited_contract_address)
        }

        fn get_function(self: @ContractState, selector: felt252) -> ContractFunction{
            self.functions.read(selector)
        }
        
        fn get_contract_id(self: @ContractState) -> u256{
            self.contract_id.read()
        }

        fn get_deposited_contracts(self: @ContractState) -> Array<ContractAddress>{
            let mut arr1 = ArrayTrait::<ContractAddress>::new();
            let mut idx = 0;
            let contract_id = self.contract_id.read();
            loop {
                if idx < contract_id{
                    arr1.append(self.contract_id_to_contract.read(idx));
                    idx += 1;
                } else {
                    break;
                }
            };
            arr1
        }

    }
    
    fn process_fraction_period(fraction_period: FractionPeriod) -> u256{
        let value = match fraction_period {
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