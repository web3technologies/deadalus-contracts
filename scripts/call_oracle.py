import asyncio
import argparse

from deploy_modules import update_oracle


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