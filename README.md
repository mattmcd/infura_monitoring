# Event Monitoring with Infura
Making use of Infura [improved eth_getLogs](https://blog.infura.io/faster-logs-and-events-e43e2fa13773)
to observe token transactions.  

Etherscan API is used to retrieve contract ABI.

## Setup
Create file config.json and enter your [Infura](https://infura.io/) project ID,
and  [Etherscan](https://etherscan.io) API key.  
Can also enter a default contract address.


    {
      "contract_address": "0x10dB9941E65DA3B7FDB0Cd05B1fd434Cb8B18158",
      "infura_project_id": "(your Infura project id)",
      "etherscan_api_key": "(your Etherscan API key)"
    }



## Example usage
Example using [Tether stablecoin](https://etherscan.io/token/0xdac17f958d2ee523a2206206994597c13d831ec7).  We get
the ABI, find the topic for Transfer event and get these.

    from infmon.io import (get_contract_abi, get_event_interface, 
        get_current_block, get_contract_events, subscribe)
    token_address = '0xdAC17F958D2ee523a2206206994597C13D831ec7' # Tether
    token_abi = get_contract_abi(token_address)
    token_interface = get_event_interface(token_abi)
    # RPC interface - get token transfers in last 10 blocks
    transfers = get_contract_events(
        token_address, 
        from_block=get_current_block() - 10,  
        topics=[token_interface['Transfer']['topic']])

    # Display 
    [token_interface['Transfer']['decode'](t) for t in transfers]
    
    # Subscription interface - WIP not quite working yet
    await subscribe(token_address, 
                    topics=[token_interface['Transfer']['topic']])