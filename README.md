# Deadalus Contracts

## Starknet Denver 2024 Hacker House

This project represents the contracts I developed during the Starknet Denver 2024 Hacker House on Team Deadalus.

The contracts allow a user to deposit an asset into the Vault contract which fractionalizes it into many nfts. The nft's represent control over the deposited contract over a given period of time. The Vault acts as a proxy and performs caller validation ensuring the current caller is the "controller" of the contract. A custom oracle has been developed in order to gather the correct time.

Here is the official project repository: https://github.com/orgs/deadalus-labs/repositories