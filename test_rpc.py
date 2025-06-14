#!/usr/bin/env python3
import requests
import json

def test_rpc_connection():
    """Test RPC connection to B1t node."""
    url = 'http://127.0.0.1:8332'
    username = 'bitrpc_OnlyPW'
    password = '97bBe22qXTQec11CDyr7V3ehyOU52MCV27Dx4qMI'
    
    payload = {
        'method': 'getblockcount',
        'params': [],
        'jsonrpc': '2.0',
        'id': 1
    }
    
    headers = {'content-type': 'application/json'}
    
    try:
        print(f"Testing RPC connection to {url}...")
        print(f"Username: {username}")
        print(f"Password: {password[:10]}...")
        
        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=headers,
            auth=(username, password),
            timeout=30
        )
        
        print(f"\nHTTP Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if 'result' in result:
                print(f"\nSuccess! Current block height: {result['result']}")
                return True
            elif 'error' in result:
                print(f"\nRPC Error: {result['error']}")
                return False
        else:
            print(f"\nHTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"\nConnection Error: {e}")
        print("Make sure the B1t node is running and RPC is enabled.")
        return False
    except Exception as e:
        print(f"\nException: {e}")
        return False

if __name__ == '__main__':
    test_rpc_connection()