use starknet::ContractAddress;


#[starknet::interface]
trait IFlat<TContractState> {
    fn toogle_door(ref self: TContractState);
    fn get_door_state(self: @TContractState) -> bool;
    fn withdraw(ref self: TContractState, amount: u256, contract_address: ContractAddress);
}

#[starknet::contract]
mod Flat {
    use super::IFlat;

    use openzeppelin::access::ownable::OwnableComponent;
    use openzeppelin::token::erc20::{ERC20ABIDispatcher, ERC20ABIDispatcherTrait};
    use deadalus::utils::storage::StoreSpanFelt252;
    use starknet::{
        SyscallResult, ClassHash, ContractAddress, get_caller_address, call_contract_syscall,
    };

    component!(path: OwnableComponent, storage: ownable, event: OwnableEvent);

    #[storage]
    struct Storage {
        image: Span<felt252>,
        door_open: bool,
        #[substorage(v0)]
        ownable: OwnableComponent::Storage,
    }

    #[constructor]
    fn constructor(ref self: ContractState, image: Span<felt252>, initial_owner: ContractAddress) {
        self.image.write(image);
        self.ownable.initializer(initial_owner);
        self.door_open.write(false);
    }

    #[abi(embed_v0)]
    impl OwnableImpl = OwnableComponent::OwnableImpl<ContractState>;

    impl OwnableInternalImpl = OwnableComponent::InternalImpl<ContractState>;

    #[event]
    #[derive(Drop, starknet::Event)]
    enum Event {
        CounterIncreased: CounterIncreased,
        OwnableEvent: OwnableComponent::Event
    }

    #[derive(Drop, starknet::Event)]
    struct CounterIncreased {
        counter: u32
    }

    #[abi(embed_v0)]
    impl Flat of IFlat<ContractState> {
        fn toogle_door(ref self: ContractState) {
            self.ownable.assert_only_owner();
            self.door_open.write(!self.door_open.read());
        }

        fn get_door_state(self: @ContractState) -> bool {
            self.door_open.read()
        }

        fn withdraw(ref self: ContractState, amount: u256, contract_address: ContractAddress) {
            self.ownable.assert_only_owner();
            let dispatcher = ERC20ABIDispatcher { contract_address };
            let owner = self.ownable.owner();
            dispatcher.transfer(owner, amount);
        }
    }
}
#[cfg(test)]
mod tests {
    use snforge_std::{declare, ContractClassTrait};

    use starknet::ContractAddress;
    use deadalus::example_contracts::flat::{IFlatDispatcher, IFlatDispatcherTrait};
    #[test]
    fn test_deploy() {
        let contract = declare('Flat');
        let constructor_data = array![
            2, 'test', 'test', 0x045f03850a3e47a896e9da998011ec42f2f282b02d8b0914f9e7f1ba17ab0266
        ];

        let contract_address = contract.deploy(@constructor_data).unwrap();

        let dispatcher = IFlatDispatcher { contract_address };
        dispatcher.toogle_door();
        let door_state = dispatcher.get_door_state();
        assert(door_state == true, 'door not opened');
    }
}

