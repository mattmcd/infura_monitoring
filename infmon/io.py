import requests


def get_contract_events(
        contract_address=None,
        from_block=0,
        infura_project_id=None
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


def get_current_block(infura_project_id=None):
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
