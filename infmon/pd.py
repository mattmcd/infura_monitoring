import pandas as pd


def create_dataframe(tx_interface, tx_list, delete_cols=None, keep_cols=None):
    """Turn transaction data into pandas dataframe

    :param tx_interface: event interface returned by io.get_event_interface
    :param tx_list: list of transactions returned by io.get_contract_events
    :param delete_cols: transaction metadata to delete, default ['data' (after parsing), 'logIndex']
    :param keep_cols: transaction metadata to keep, default ['blockNumber', 'blockHash', 'transactionHash']
    :return: dataframe of transaction data and metadata
    """
    if delete_cols is None:
        delete_cols = ['data', 'logIndex']
    if keep_cols is None:
        keep_cols = ['blockNumber', 'blockHash', 'transactionHash']
    df_temp = pd.DataFrame(tx_list)

    df = df_temp.join(
        pd.DataFrame([tx_interface['decode'](t) for t in tx_list])
    ).drop(
        columns=delete_cols
    ).loc[:, keep_cols + tx_interface['indexed_names'] + tx_interface['names']]
    return df.copy()
