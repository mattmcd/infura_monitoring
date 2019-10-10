import requests
import os
import json
from collections import defaultdict
from functools import partial
from itertools import chain
import asyncio
import websockets
from etherscan.contracts import Contract as EsContract
from web3 import Web3
import eth_abi
from eth_utils import decode_hex


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

CONTRACT_ADDRESS = config['contract_address'] if 'contract_address' in config else ''
INFURA_PROJECT_ID = config['infura_project_id']
ETHERSCAN_API_KEY = config['etherscan_api_key']


def get_contract_events(
        contract_address=CONTRACT_ADDRESS,
        from_block=0,
        topics=None,
        infura_project_id=INFURA_PROJECT_ID
):
    if topics is None:
        topics = []
    req = requests.post(
        f'https://mainnet.infura.io/v3/{infura_project_id}',
        json={
            "jsonrpc": "2.0",
            "method": "eth_getLogs",
            "params": [{"address": contract_address.lower(), "fromBlock": hex(from_block), "topics": topics}],
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


def get_block_by_number(block_number=None, show_details=False, infura_project_id=INFURA_PROJECT_ID):
    req = requests.post(
        f'https://mainnet.infura.io/v3/{infura_project_id}',
        json={
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [hex(block_number), show_details],
            "id": 2
        }
    )
    resp = req.json()
    res = resp['result']
    res['timestamp'] = int(res['timestamp'], 16)  # Convert to Unix timestamp
    return res


async def subscribe(contract_address=CONTRACT_ADDRESS, topics=None, infura_project_id=INFURA_PROJECT_ID):
    if topics is None:
        topics = []
    subscribe_args = {
            "jsonrpc": "2.0",
            "method": "eth_subscribe",
            "params": ["logs", {"address": contract_address.lower(), "topics": topics}],
            "id": 1
        }
    ws_url = f'wss://mainnet.infura.io/ws/{infura_project_id}'
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps(subscribe_args))
        subscribe_id = await ws.recv()
        print(subscribe_id)
        block_hashes = defaultdict(int)
        last_block_hash = ''
        while True:
            message_str = await ws.recv()
            message = json.loads(message_str)['params']['result']
            # Simple handler to count transactions per block and show any removed transactions
            block_hashes[message['blockHash']] += 1
            if message['removed']:
                print('REMOVED')
                print(message)
            else:
                if message['blockHash'] != last_block_hash:
                    if last_block_hash != '':
                        print(last_block_hash + ': ' + str(block_hashes[last_block_hash]))
                    last_block_hash = message['blockHash']


def get_contract_abi(
        contract_address=CONTRACT_ADDRESS,
        etherscan_api_key=ETHERSCAN_API_KEY
):
    es_api = EsContract(address=contract_address, api_key=etherscan_api_key)
    abi = json.loads(es_api.get_abi())
    return abi


def get_event_interface(abi):
    """Get details of the event interfaces specified in the contract ABI
    See https://codeburst.io/deep-dive-into-ethereum-logs-a8d2047c7371

    :param abi: Contract ABI as list of dicts
    :return: Event interfaces as dict
    """
    events = [i for i in abi if i['type'] == 'event']
    interfaces = {
        e['name']: {
            'topic': Web3.toHex(
                Web3.keccak(text=e['name'] + '(' + ','.join([i['type'] for i in e['inputs']]) + ')')
            ),
            'names': [i['name'] for i in e['inputs'] if not i['indexed']],
            'types': [i['type'] for i in e['inputs'] if not i['indexed']],
            'indexed_names': [i['name'] for i in e['inputs'] if i['indexed']],
            'indexed_types': [i['type'] for i in e['inputs'] if i['indexed']],
        } for e in events
    }

    # Add decoders
    def decoder(interface, log):
        non_indexed = zip(
            interface['names'],
            eth_abi.decode_abi(interface['types'], decode_hex(log['data'])))
        indexed = zip(
            interface['indexed_names'],
            [eth_abi.decode_single(t, decode_hex(v)) for t, v in zip(interface['indexed_types'], log['topics'][1:])]
        )
        return dict(chain(non_indexed, indexed))

    for e, i in interfaces.items():
        interfaces[e]['decode'] = partial(decoder, i)
    return interfaces
