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



## Example usage - RPC interface
Example using [Tether stablecoin](https://etherscan.io/token/0xdac17f958d2ee523a2206206994597c13d831ec7).  We get
the ABI, find the topic for Transfer event and get these events.  This could be used as the ETL step for a 
data science application e.g. get all Transfers over a given time period and do some [graph analysis](https://networkx.github.io/).


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
    
    
## Example usage - websocket subscription
To drive a user interface in realtime we woudl like to get events streamed from a websocket.
These events can then be stored in a backend cache database to service frontend clients with the state
of the system.  

A complication arises due to [chain reorganization events](https://blog.ethereum.org/2015/08/08/chain-reorganisation-depth-expectations/)
which will cause already seen transactions to be reverted.  Fortunately the Infura 
[eth_subscribe](https://infura.io/docs/ethereum/wss/eth_subscribe) websockets endpoint resends previously sent logs 
on the old chain with the `removed` attribute set to true so these can be handled.  

The example below is a work in progress with a simple message handler that prints counts of Transfer events in 
each block if there are not removed transactions, and prints any removed transactions otherwise.

    # Subscription interface 
    await subscribe(token_address, topics=[token_interface['Transfer']['topic']])
    
    # Results below:
    # Initial response with subscription ID
    {"jsonrpc":"2.0","id":1,"result":"0x1feed340b2f854185bd4cfcee65748d"}
    # Normal blocks with count of Transfer events in block 
    0x1754f43ba29f72b487889ed1dc58df214f13bcdb014a06b04aaad8e0344e27af: 9
    0x0da94fb67c84ee22d9bb6e6ba806e533e90fa7e8e5704bf6d74aaeb210c791d7: 16
    # Block reorganization produces transactions with removed set to True
    REMOVED
    {'removed': True, 'logIndex': '0x7', 'transactionIndex': '0x32', 
     'transactionHash': '0xc0b35d02011026f6dee695c40b69a972949bddb40ffe0d21391f2c23572b2a2f', 
      'blockHash': '0xc4dc057c1fa6742128befb189d82ef727b0555fd3066f974e23864c3c4f09416', 
      'blockNumber': '0x84a7fb', 'address': '0xdAC17F958D2ee523a2206206994597C13D831ec7', 
      'data': '0x0000000000000000000000000000000000000000000000000000000103d10fc0', 
      'topics': ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef', 
      '0x0000000000000000000000000a98fb70939162725ae66e626fe4b52cff62c2e5', 
      '0x000000000000000000000000adba6097a5c63c586aa7c9ee5665ffa746f7f255']}
    REMOVED
    {'removed': True, 'logIndex': '0x8', 'transactionIndex': '0x33', 
     'transactionHash': '0x925555803b5e083237deb13bb1be2a0ff12a7cc3e680553faa7fe76b83627f73', 
     'blockHash': '0xc4dc057c1fa6742128befb189d82ef727b0555fd3066f974e23864c3c4f09416', 
     'blockNumber': '0x84a7fb', 'address': '0xdAC17F958D2ee523a2206206994597C13D831ec7', 
     'data': '0x000000000000000000000000000000000000000000000000000000002878b7c0', 
     'topics': ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef', 
     '0x0000000000000000000000000a98fb70939162725ae66e626fe4b52cff62c2e5', 
     '0x000000000000000000000000cca1bbbc2c907afd731c2158e80172531e74cd72']}
    ... # More removed transactions
    # Next block    
    0xc4dc057c1fa6742128befb189d82ef727b0555fd3066f974e23864c3c4f09416: 74
    0xf65a34ff8c131c3508f52a432b45e7a5d2c34bf2a4d8996c4e18d55d045a47dc: 36
    0x16a18d1351190a69f7df34b7b5336deb3e257b9fb7b4b347b2e7962911aa6215: 15
    0xb88fba7fba0b343335e2c1f5816e741a07631b86909ac106db91e45d4bbbfc59: 15
    
# Interesting contracts

## Tokens

Use [EthPlorer API](https://github.com/EverexIO/Ethplorer/wiki/Ethplorer-API) to retrieve list of top traded tokens as json

     curl https://api.ethplorer.io/getTopTokens?apiKey=freekey -o cache/ethplorer_top20200523.json
     
## dYdX DEX
[Contract Addresses](https://docs.dydx.exchange/#/contracts)

    from infmon.eth import read_credentials, connect, get_contract
    read_credentials('/home/mattmcd/.mattmcd')  # Populates environment variables
    w3 = connect()   # Connects to mainnet via Infura and sets defaultAccount 
    
    # Populate cache if needed - commented out 
    # c = get_contract('dYdX_SoloMargin', '0x1E0447b19BB6EcFdAe1e4AE1694b0C3659614e4e')
    
    # Connect to contract
    solo = w3.eth.contract(**get_contract('dYdX_SoloMargin'))
    
    solo.all_functions()
    Out[7]: 
    [<Function ownerSetSpreadPremium(uint256,tuple)>,
     <Function getIsGlobalOperator(address)>,
     <Function getMarketTokenAddress(uint256)>,
     ...
     <Function getAdjustedAccountValues(tuple)>,
     <Function getMarketMarginPremium(uint256)>,
     <Function getMarketInterestRate(uint256)>]
    
    me = w3.eth.defaultAccount
    
    solo.functions.getMarket(0).call({'from': me.address})
    Out[10]: 
    ('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
     (17223105496066458626271, 101489418110876542971309),
     (1010406097301649461, 1001404702877850791, 1590241097),
     '0xf61AE328463CD997C7b58e7045CdC613e1cFdb69',
     '0x7538651D874b7578CF52152c9ABD8f6617a38403',
     (0,),
     (0,),
     False)