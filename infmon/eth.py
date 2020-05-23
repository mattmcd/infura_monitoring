import os
import json
import web3
from pathlib import Path
from infmon.io import get_contract_abi


def read_credentials(cred_dir):
    with open(os.path.join(cred_dir, 'credentials.json'), 'r') as f:
        os.environ['CREDENTIALS'] = f.read()


def connect():
    credentials = json.loads(os.environ.get('CREDENTIALS'))
    os.environ['WEB3_INFURA_PROJECT_ID'] = credentials['infura']['project_id']
    os.environ['WEB3_INFURA_API_SECRET'] = credentials['infura']['secret']

    if credentials['infura']['network'] == 'kovan':
        from web3.auto.infura.kovan import w3
    else:
        from web3.auto.infura import w3

    assert w3.isConnected()

    w3.eth.defaultAccount = w3.eth.account.from_key(credentials['mainnet']['key'])

    return w3


def get_contract(name, address=None, abi=None):
    credentials = json.loads(os.environ.get('CREDENTIALS'))
    cache_dir = Path(__file__).parent / "../cache"
    if not cache_dir.is_dir():
        os.mkdir(cache_dir)
    cache_file = cache_dir / f'{name}.json'
    if cache_file.is_file():
        with open(cache_file, 'r') as f:
            contract_details = json.load(f)
    else:
        if abi is None:
            abi = get_contract_abi(
                address,
                etherscan_api_key=credentials['etherscan']['api_key']
            )
        contract_details = {
            'address': address,
            'abi': abi
        }
        with open(cache_file, 'w') as f:
            json.dump(contract_details, f)
    return contract_details
