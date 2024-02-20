from decouple import config
from starknet_py.constants import DEFAULT_DEPLOYER_ADDRESS
from starknet_py.net.models import StarknetChainId


class DeployerConfig:
    
    def __init__(self, account_address, private_key, node_url, udc_address=DEFAULT_DEPLOYER_ADDRESS, chain_id=StarknetChainId.GOERLI, developer_account=None) -> None:
        self.account_address = account_address
        self.private_key = private_key
        self.node_url = node_url
        self.udc_address = udc_address
        self.chain_id=chain_id
        self.developer_account=developer_account
        
    @classmethod
    def get_config(cls, deploy_env):
        if deploy_env == 'dev':
            dev_deployer_config = cls(
                account_address=config("DEV_ACCOUNT_ADDRESS"),
                private_key=config("DEV_PRIVATE_KEY"),
                node_url=config("DEV_NODE_URL"),
                udc_address="0x41A78E741E5AF2FEC34B695679BC6891742439F7AFB8484ECD7766661AD02BF",
                developer_account=config("DEVELOPER_ACCOUNT")       ## account created in Argent, Braavos etc
            )
        elif deploy_env == 'int':
            dev_deployer_config = cls(
                account_address=config("INT_ACCOUNT_ADDRESS"),
                private_key=config("INT_PRIVATE_KEY"),
                node_url=config("INT_NODE_URL"),
            )
        else:
            raise ValueError(f"{deploy_env} is not available for deployment.")
        return dev_deployer_config