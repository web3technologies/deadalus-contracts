use starknet::ClassHash;


#[starknet::interface]
trait ICounterFactory<TContractState>{
    fn deploy_counter_contract(ref self: TContractState);
    fn set_counter_classhash(ref self: TContractState, class_hash: ClassHash);
}


#[starknet::contract]
mod CounterFactory{
    use super::ICounterFactory;
    use starknet::ClassHash;
    use starknet::ContractAddress;
    use starknet::SyscallResult;

    use starknet::syscalls::deploy_syscall;
    use starknet::get_caller_address;
    use starknet::info::get_contract_address;

   #[storage]
   struct Storage{
        owner: ContractAddress,
        counter_contracts: LegacyMap::<ContractAddress, u256>,
        counter_contract_class_hash: ClassHash, // need this in order to deploy,
        counter_id: u256
   }

   #[constructor]
   fn constructor(ref self: ContractState){
        self.owner.write(get_caller_address());
   }

    #[abi(embed_v0)]
    impl CounterFactory of ICounterFactory<ContractState>{
        fn deploy_counter_contract(ref self: ContractState){
            let arr = array!['']; // empty call data
            let call_data_snapshot = arr.span(); // create immutable snapshot
            let deploy_result: SyscallResult = deploy_syscall(
                self.counter_contract_class_hash.read(),
                '1', // how to generate a salt?
                call_data_snapshot,
                deploy_from_zero: false
            );
            match deploy_result {
                Result::Ok((_contract_address, _return_data)) =>{
                    self.counter_contracts.write(_contract_address, 1);
                },
                Result::Err(_) => {
                    panic!("error in contract call");
                }
            }
        }
        fn set_counter_classhash(ref self: ContractState, class_hash: ClassHash){
            let caller: ContractAddress = get_caller_address();
            assert(caller == self.owner.read(), 'caller is not owner');
            self.counter_contract_class_hash.write(class_hash);
        }
    }

}