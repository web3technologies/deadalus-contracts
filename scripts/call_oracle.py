import asyncio
import argparse

from deploy_modules import update_oracle


def main():
    parser = argparse.ArgumentParser(description='Script to deploy smart contracts.')
    parser.add_argument('--deploy-env', dest='deploy_env', type=str, help='Deployment environment (e.g., dev, int, prod)')
    parser.add_argument('--contract-address', dest="contract_address", type=str, help="Contract address of the oracle")
    args = parser.parse_args()
    asyncio.run(update_oracle(args.deploy_env, contract_address=args.contract_address))


if __name__ == "__main__":
    main()