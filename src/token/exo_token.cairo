#[starknet::contract]
mod ExoToken {
    use openzeppelin::token::erc20::ERC20Component;
    use starknet::ContractAddress;

    component!(path: ERC20Component, storage: erc20, event: ERC20Event);

    #[abi(embed_v0)]
    impl ERC20Impl = ERC20Component::ERC20Impl<ContractState>;
    #[abi(embed_v0)]
    impl ERC20MetadataImpl = ERC20Component::ERC20MetadataImpl<ContractState>;
    #[abi(embed_v0)]
    impl ERC20CamelOnlyImpl = ERC20Component::ERC20CamelOnlyImpl<ContractState>;
    impl InternalImpl = ERC20Component::InternalImpl<ContractState>;

    // The maximum number of holders allowed before launch.
    // Once reached, transfers are disabled until EXO token is launched.
    const MAX_HOLDERS_BEFORE_LAUNCH: u8 = 10;

    #[storage]
    struct Storage {
        pre_launch_holders_count: u8,
        team_allocation: u256,
        #[substorage(v0)]
        erc20: ERC20Component::Storage
    }

    #[event]
    #[derive(Drop, starknet::Event)]
    enum Event {
        #[flat]
        ERC20Event: ERC20Component::Event
    }

    #[constructor]
    fn constructor(ref self: ContractState, fixed_supply: u256, recipient: ContractAddress) {
        let name = 'Exo Token';
        let symbol = 'EXO';

        self.erc20.initializer(name, symbol);
        self.erc20._mint(recipient, fixed_supply);
    }
}
