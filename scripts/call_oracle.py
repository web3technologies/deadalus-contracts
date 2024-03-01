import asyncio
import argparse
import time
from starknet_py.net.client_errors import ClientError
from starknet_py.contract import Contract
from starknet_simple_deploy import DeployerConfig


async def update_oracle(deploy_env, contract_address, chain):
    deployer_config = DeployerConfig.get_config(deploy_env, chain=chain).init_account()
    oracle_contract = await Contract.from_address(provider=deployer_config.account, address=contract_address)
    while True:
        curr_time = int(time.time())
        try:
            tx = await oracle_contract.functions["set_time"].invoke_v3(
                unix_timestamp=curr_time,
                auto_estimate=True
            )
        except ClientError as e:
            continue
        # wait for contract to be confirmed to prevent nonce issues
        await deployer_config.account.client.wait_for_tx(tx.hash)
        contract_time = await oracle_contract.functions["get_time"].call()
        print(f"Current contract time is: {contract_time[0]}")
        div = contract_time[0] % 90
        if div > 45:
            print("2 is owner")
        else:
            print("1 is owner")


def main():
    parser = argparse.ArgumentParser(description='Script to deploy smart contracts.')
    # positional
    parser.add_argument('deploy_env', type=str, help='Deployment environment (e.g., dev, int, prod)')
    parser.add_argument('contract_address', type=str, help="Contract address of the oracle")
    # optional
    parser.add_argument('--chain', dest='chain', default="GOERLI", type=str, help='Chain (e.g., GOERLI, SEPOLIA-INTEGRATION, SEPOLIA-TEST, MAINNET)')
    args = parser.parse_args()
    asyncio.run(
        update_oracle(
            args.deploy_env, contract_address=args.contract_address, chain=args.chain
        )
    )


if __name__ == "__main__":
    main()
