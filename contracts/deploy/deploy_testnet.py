'''
A simple Python script to deploy contracts and then do a smoke test for them.
'''
import click
from populus import Project
from ethereum.utils import encode_hex
from eth_utils import pad_left, remove_0x_prefix
from utils.utils import (
    check_succesful_tx,
    wait,
    pack
)


@click.command()
@click.option(
    '--chain',
    default='kovan',
    help='Chain to deploy on: kovan | ropsten | rinkeby | tester | privtest'
)
@click.option(
    '--owner',
    help='Contracts owner, default: web3.eth.accounts[0]'
)
@click.option(
    '--challenge-period',
    default=500,
    help='Challenge period in number of blocks.'
)
@click.option(
    '--supply',
    default=10000000,
    help='Token contract supply (number of total issued tokens).'
)
@click.option(
    '--token-name',
    default='CustomToken',
    help='Token contract name.'
)
@click.option(
    '--token-decimals',
    default=18,
    help='Token contract number of decimals.'
)
@click.option(
    '--token-symbol',
    default='TKN',
    help='Token contract symbol.'
)
@click.option(
    '--token-address',
    help='Already deployed token address.'
)
def main(**kwargs):
    project = Project()

    chain_name = kwargs['chain']
    owner = kwargs['owner']
    challenge_period = kwargs['challenge_period']
    supply = kwargs['supply']
    token_name = kwargs['token_name']
    token_decimals = kwargs['token_decimals']
    token_symbol = kwargs['token_symbol']
    token_address = kwargs['token_address']
    supply *= 10**(token_decimals)
    txn_wait = 250

    assert challenge_period >= 500, 'Challenge period should be >= 500 blocks'

    if chain_name == 'rinkeby':
        txn_wait = 500

    print('''Make sure {} chain is running, you can connect to it and it is synced,
          or you'll get timeout'''.format(chain_name))

    with project.get_chain(chain_name) as chain:
        web3 = chain.web3
        print('Web3 provider is', web3.currentProvider)

        owner = owner or web3.eth.accounts[0]
        assert owner
        assert web3.eth.getBalance(owner) > 0, 'Account with insuficient funds.'
        print('Owner is', owner)

        token = chain.provider.get_contract_factory('CustomToken')

        if not token_address:
            txhash = token.deploy(
                args=[supply, token_name, token_symbol, token_decimals],
                transaction={'from': owner}
            )
            receipt = check_succesful_tx(chain.web3, txhash, txn_wait)
            token_address = receipt['contractAddress']
            print(token_name, 'address is', token_address)

        microraiden_contract = chain.provider.get_contract_factory('RaidenMicroTransferChannels')
        txhash = microraiden_contract.deploy(args=[token_address, challenge_period])
        receipt = check_succesful_tx(chain.web3, txhash, txn_wait)
        microraiden_address = receipt['contractAddress']

        print('RaidenMicroTransferChannels address is', microraiden_address)

        abi_encoded_args = encode_hex(pad_left(pack(
            remove_0x_prefix(token_address),
            challenge_period),
            128, '0'
        ))

        print('RaidenMicroTransferChannels arguments', token_address, challenge_period)
        print('RaidenMicroTransferChannels abi encoded constructor arguments:', abi_encoded_args)


if __name__ == '__main__':
    main()
