#!/usr/bin/python3
from web3 import Web3
import requests
import json
from sys import argv
import argparse


def init(verbose:bool=False):
    w3 = Web3(Web3.HTTPProvider(args.node))
    if verbose == True:
        if w3.is_connected():
            print(f"connected to node")
        else:
            print("failed to connect to node")
    return w3

information = {}

def ret_addr_contents(address: str, other_contents:list=None):
    zeros = 0
    contents: list = []

    for i in address[2:]:
        if "0" == i:
            zeros += 1
    if zeros > 0: 
        contents.append(zeros)

    if other_contents != None:
        for idx in other_contents:
            if idx in address:
                contents.append(idx)

    if "42069" in address:
        contents.append("42069")
    elif "69" in address:
        contents.append("69")
    elif "420" in address:
        contents.append("420")

    return contents

class ContractInfo:
    def __init__(self, contract_address:str, api_key:str):
        self.contract_address = contract_address
        self.api_key = api_key

    def get_contract_abi_from_etherscan(self):
        url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={self.contract_address}&apikey={self.api_key}"
        response = requests.get(url)
        data = response.json()
        if data['status'] == '1':
            return data['result']
        else:
            raise ValueError(f"Failed to fetch ABI for {self.contract_address}. Error: {data.get('message')}")

    def get_contract_creation_tx_from_etherscan(self):
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={self.contract_address}&sort=asc&apikey={self.api_key}"
        response = requests.get(url)
        data = response.json()
        if data['status'] == '1' and len(data['result']) > 0:
            return data['result'][0]['hash']
        else:
            raise ValueError(f"Failed to fetch transactions for {self.contract_address}. Error: {data.get('message')}")

    def calc_age(self, verbose=False):
        if verbose:
            print("calculating the age of the contract...")
        creation_tx = self.get_contract_creation_tx_from_etherscan()
        block_number = w3.eth.get_transaction(creation_tx)['blockNumber']
        block_timestamp = w3.eth.get_block(block_number)['timestamp']

        current_timestamp = w3.eth.get_block('latest')['timestamp']
        age_in_seconds = current_timestamp - block_timestamp
        days = age_in_seconds // (24 * 3600)
        age_in_seconds %= (24 * 3600)
        hours = age_in_seconds // 3600
        age_in_seconds %= 3600
        minutes = age_in_seconds // 60
        age_str = f"{days}d:{hours}h:{minutes}m"

        return age_str

    def ens_bal_txs(self, verbose=False):
        if verbose:
            print("checking balance...")
        wei = w3.eth.get_balance(self.contract_address)
        balance = w3.from_wei(wei, "ether")
        balance = f"{balance} ETH"
        
        if verbose:
            print("checking ens...")
        ens = w3.ens.name(self.contract_address)
        if ens == None:
            ens = "ETH address does not have an ENS"

        if verbose:
            print("checking txs...")
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={self.contract_address}&startblock=0&endblock=99999999&sort=asc&apikey={self.api_key}"
        response = requests.get(url)
        txs = response.json().get('result', [])
        if len(txs) == 10000:
            txs = "max display cap of 10000: was hit, check etherscan for a more accurate display of TXS"
        else:
            return len(txs)

        return balance, ens, txs

    def functions(self, verbose=False):
        if verbose:
            print("grabbing all functions...\n")
        data = self.get_contract_abi_from_etherscan()
        func_names = []

        if data != None:
            json_data = json.loads(data)
            function_entries = [entry for entry in json_data if entry["type"] == "function"]
            for function in function_entries:
                func_names.append(function["name"])
        else:
            print("api request failed")

        return func_names

def handler(address, key, special_contents:list=None):
    contract = ContractInfo(address, key)
    bal, ens, txs = contract.ens_bal_txs(True)
    age = contract.calc_age(True)
    
    functions = contract.functions(True)
    information["ENS: "] = ens
    information["BALANCE: "] = bal
    information["TXS: "] = txs
    information["AGE: "] = age
    information["FUNCTIONS: "] = functions

    for k, v in information.items():
        print(f"{k}{v}")
    
    if special_contents != None:
        contents = ret_addr_contents(address, special_contents)
        print(f"""Address Contents Information:
    {contents[0]} Zeros
Other Contents Include:
    {contents}\n""")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Contract Information Displayer")
    parser.add_argument("--key", help="etherscan api key", type=str)
    parser.add_argument("--node", help="node endpoint (go to infura)", type=str)
    parser.add_argument("--address", help="contract address", type=str)
    parser.add_argument("--special", type=str, nargs="?", help="Comma-separated special values")
    args = parser.parse_args()

    #print(args.key, args.node, args.address)
    w3 = init(True) # args.node)
    if isinstance(args.special, str):
        special_ = args.special.split(",")
        handler(args.address, args.key, special_)
    else:
        handler(args.address, args.key)
