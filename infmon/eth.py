import os
import json
from web3.middleware import construct_sign_and_send_raw_middleware
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

    acct = w3.eth.account.from_key(credentials['mainnet']['key'])
    w3.middleware_onion.add(construct_sign_and_send_raw_middleware(acct))
    w3.eth.defaultAccount = acct.address

    return w3


def get_contract(name, w3=None, address=None, abi=None):
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
    if w3 is None:
        # Return contract details as dict
        # NB: address may be non-checksum version which can cause problems downstream
        return contract_details
    else:
        contract_details['address'] = w3.toChecksumAddress(contract_details['address'])
        # Remove ctor and default
        contract_details['abi'] = [f for f in contract_details['abi'] if 'name' in f]
        return w3.eth.contract(**contract_details)
