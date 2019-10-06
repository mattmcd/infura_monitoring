import requests
import os
import json
from collections import defaultdict
from etherscan.contracts import Contract as EsContract
from web3 import Web3


def read_config():
    # Load default api keys and default contract address from config file
    # Alternative: could get from environment variables?
    config_file = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    if os.path.isfile(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = defaultdict(str)
    return config


config = read_config()

CONTRACT_ADDRESS = config['contract_address']
INFURA_PROJECT_ID = config['infura_project_id']
ETHERSCAN_API_KEY = config['etherscan_api_key']


def get_contract_events(
        contract_address=CONTRACT_ADDRESS,
        from_block=0,
        infura_project_id=INFURA_PROJECT_ID
):
    req = requests.post(
        f'https://mainnet.infura.io/v3/{infura_project_id}',
        json={
            "jsonrpc": "2.0",
            "method": "eth_getLogs",
            "params": [{"address": contract_address.lower(), "fromBlock": hex(from_block)}],
            "id": 1
        }
    )
    resp = req.json()
    return resp['result']


def get_current_block(infura_project_id=INFURA_PROJECT_ID):
    req = requests.post(
        f'https://mainnet.infura.io/v3/{infura_project_id}',
        json={
            "jsonrpc": "2.0",
            "method": "eth_blockNumber",
            "params": [],
            "id": 2
        }
    )
    resp = req.json()
    return int(resp['result'], 16)


def get_contract_abi(
        contract_address=CONTRACT_ADDRESS,
        etherscan_api_key=ETHERSCAN_API_KEY
):
    eth_api = EsContract(address=contract_address, api_key=etherscan_api_key)
    abi = json.loads(eth_api.get_abi())
    return abi


def get_topics(abi):
    events = [i for i in abi if i['type'] == 'event']
    topics = {e['name']: Web3.keccak(
        text=e['name'] + '(' + ','.join([i['type'] for i in e['inputs']]) + ')'
    ) for e in events}
    return topics
