from decouple import config
from starknet_py.constants import DEFAULT_DEPLOYER_ADDRESS
from starknet_py.net.models import StarknetChainId
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.signer.stark_curve_signer import KeyPair


class DeployerConfig:
    
    def __init__(self, 
                 account_address, 
                 private_key, 
                 node_url, 
                 udc_address=DEFAULT_DEPLOYER_ADDRESS, 
                 chain_id=StarknetChainId.GOERLI, 
                 developer_account=None
    ) -> None:
        self.account_address = account_address
        self.private_key = private_key
        self.node_url = node_url
        self.udc_address = udc_address
        self.chain_id=chain_id
        self.developer_account=developer_account
        self.key_pair = None
        self.client = None
        self.account = None
        
    @classmethod
    def get_config(cls, deploy_env, chain=None):
        if deploy_env == 'dev':
            dev_deployer_config = cls(
                account_address=config("DEV_ACCOUNT_ADDRESS"),
                private_key=config("DEV_PRIVATE_KEY"),
                node_url=config("DEV_NODE_URL"),
                developer_account=config("DEVELOPER_ACCOUNT"),       ## account created in Argent, Braavos etc
                chain_id=cls.get_chain_id(chain)
            )
        elif deploy_env == 'int':
            if chain == "GOERLI":
                dev_deployer_config = cls(
                    account_address=config("INT_GOERLI_ACCOUNT_ADDRESS"),
                    private_key=config("INT_GOERLI_PRIVATE_KEY"),
                    node_url=config("INT_GOERLI_NODE_URL"),
                    chain_id=cls.get_chain_id(chain)
                )
            elif chain in ("SEPOLIA-TEST", "SEPOLIA-INTEGRATION"):
                dev_deployer_config = cls(
                    account_address=config("INT_SEPOLIA_ACCOUNT_ADDRESS"),
                    private_key=config("INT_SEPOLIA_PRIVATE_KEY"),
                    node_url=config("INT_SEPOLIA_NODE_URL"),
                    chain_id=cls.get_chain_id(chain)
                )
            else:
                raise ValueError(f"Chain: {chain} is not an available chain.")
            
        else:
            raise ValueError(f"{deploy_env} is not available for deployment.")
        return dev_deployer_config
    
    @classmethod
    def get_chain_id(cls, chain):
        if chain == "GOERLI":
            chain_id = StarknetChainId.GOERLI
        elif chain == "SEPOLIA-INTEGRATION":
            chain_id = StarknetChainId.SEPOLIA_INTEGRATION
        elif chain == "SEPOLIA-TEST":
            chain_id = StarknetChainId.SEPOLIA_TESTNET
        elif chain == "MAINNET":
            chain_id = StarknetChainId.MAINNET
        else:
            raise ValueError(f"Chain: {chain} is not an available chain.")
        return chain_id
    
    def init_account(self):
        self.key_pair = KeyPair.from_private_key(self.private_key)
        self.client = FullNodeClient(node_url=self.node_url)
        self.account = Account(
            address=self.account_address,
            client=self.client,
            key_pair=self.key_pair,
            chain=self.chain_id
        )
        return self