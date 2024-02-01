# fmt:
# 	scarb fmt 

# clean:
# 	scarb clean

# build: clean
# 	scarb build

# test: 
# 	snforge test

# deploy: build
# 	@./scripts/deploy.sh

starkli-declare:
	starkli declare $(target) --rpc https://starknet-sepolia.public.blastapi.io/rpc/v0_6 --account ~/.starkli-wallets/deployer/account.json --keystore ~/.starkli-wallets/deployer/keystore.json

starkli-deploy:
	starkli deploy $(hash) --watch $(input) --rpc https://starknet-sepolia.public.blastapi.io/rpc/v0_6 --account ~/.starkli-wallets/deployer/account.json --keystore ~/.starkli-wallets/deployer/keystore.json