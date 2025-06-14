#!/usr/bin/env python3

import os
import json
import time
import argparse
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class B1TRPCClient:
    def __init__(self):
        self.host = os.getenv('B1T_RPC_HOST', '127.0.0.1')
        self.port = int(os.getenv('B1T_RPC_PORT', 8332))
        self.user = os.getenv('B1T_RPC_USER')
        self.password = os.getenv('B1T_RPC_PASS')
        self.timeout = int(os.getenv('B1T_RPC_TIMEOUT', 30))
        self.max_retries = int(os.getenv('B1T_RPC_MAX_RETRIES', 3))
        self.retry_delay = float(os.getenv('B1T_RPC_RETRY_DELAY', 1.0))
        
        self.url = f'http://{self.host}:{self.port}'
        self.session = requests.Session()
        self.session.auth = (self.user, self.password)
        self.session.headers.update({'Content-Type': 'application/json'})
        
        print(f"RPC Client initialized: {self.url}")
    
    def call(self, method, params=None):
        """Make a single RPC call"""
        if params is None:
            params = []
        
        payload = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': 1
        }
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(self.url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                
                result = response.json()
                if 'error' in result and result['error']:
                    raise Exception(f"RPC Error: {result['error']}")
                
                return result.get('result')
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"RPC call failed (attempt {attempt + 1}): {e}. Retrying...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"RPC call failed after {self.max_retries} attempts: {e}")
                    return None
    
    def batch_call(self, calls):
        """Make multiple RPC calls in a single batch request"""
        if not calls:
            return []
        
        payload = []
        for i, (method, params) in enumerate(calls):
            payload.append({
                'jsonrpc': '2.0',
                'method': method,
                'params': params or [],
                'id': i
            })
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(self.url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                
                results = response.json()
                if not isinstance(results, list):
                    results = [results]
                
                # Sort results by id to maintain order
                results.sort(key=lambda x: x.get('id', 0))
                
                return [r.get('result') if 'error' not in r or not r['error'] else None for r in results]
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"Batch RPC call failed (attempt {attempt + 1}): {e}. Retrying...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"Batch RPC call failed after {self.max_retries} attempts: {e}")
                    return [None] * len(calls)

def update_status(current_block, start_block, total_blocks, phase="analysis"):
    """Update analysis status to a file that can be read by the web app"""
    try:
        blocks_processed = current_block - start_block + 1
        progress = (blocks_processed / total_blocks) * 100 if total_blocks > 0 else 0
        status_data = {
            'current_block': current_block,
            'start_block': start_block,
            'total_blocks': total_blocks,
            'blocks_processed': blocks_processed,
            'progress': min(progress, 100),
            'phase': phase,
            'timestamp': time.time()
        }
        
        with open('/tmp/b1t_analysis_status.json', 'w') as f:
            json.dump(status_data, f)
    except Exception as e:
        print(f"Warning: Could not update status file: {e}")

def analyze_blocks_rpc(start_block, end_block, batch_size=1000, verbose=False, show_all_zeros=False, min_zeros=2, min_inputs=1, exclude_coinbase=False):
    """Analyze blocks using RPC with two-phase approach"""
    print(f'Analyzing blocks {start_block} to {end_block} with batch size {batch_size}...')
    
    rpc = B1TRPCClient()
    
    stats = {
        'blocks_analyzed': 0,
        'transactions_analyzed': 0,
        'coinbase_transactions': 0,
        'multi_input_transactions': 0,
        'transactions_with_zeros': defaultdict(int),
        'special_transactions': 0
    }
    
    # Phase 1: Collect all transactions with min_zeros+ leading zeros
    zero_transactions = []  # List of (block_height, txid, leading_zeros, is_coinbase)
    
    start_time = time.time()
    total_blocks = end_block - start_block + 1
    
    # Initialize status
    update_status(start_block, start_block, total_blocks, "phase1")
    
    print(f"\n=== PHASE 1: Collecting transactions with {min_zeros}+ leading zeros ===")
    
    for batch_start in range(start_block, end_block + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_block)
        
        if verbose or batch_start % (batch_size * 10) == start_block:
            elapsed = time.time() - start_time
            rate = stats['blocks_analyzed'] / elapsed if elapsed > 0 else 0
            print(f'Processing batch {batch_start}-{batch_end}, Rate: {rate:.2f} blocks/sec, Zero TXs found: {len(zero_transactions)}')
        
        # Update status every batch
        update_status(batch_start, start_block, total_blocks, "phase1")
        
        # Batch get block hashes
        hash_calls = [('getblockhash', [height]) for height in range(batch_start, batch_end + 1)]
        block_hashes = rpc.batch_call(hash_calls)
        
        # Batch get block data
        block_calls = [('getblock', [block_hash]) for block_hash in block_hashes if block_hash]
        block_data_list = rpc.batch_call(block_calls)
        
        # Process blocks
        for i, block_data in enumerate(block_data_list):
            if not block_data or 'tx' not in block_data:
                continue
            
            block_height = batch_start + i
            txids = block_data['tx']
            
            stats['blocks_analyzed'] += 1
            stats['transactions_analyzed'] += len(txids)
            
            # Check each transaction for leading zeros
            for j, txid in enumerate(txids):
                leading_zeros = 0
                for char in txid:
                    if char == '0':
                        leading_zeros += 1
                    else:
                        break
                
                if leading_zeros >= min_zeros:
                    stats['transactions_with_zeros'][leading_zeros] += 1
                    is_coinbase = j == 0  # First transaction is coinbase
                    zero_transactions.append((block_height, txid, leading_zeros, is_coinbase))
    
    phase1_time = time.time() - start_time
    print(f"\nPhase 1 completed in {phase1_time:.2f} seconds")
    print(f"Found {len(zero_transactions)} transactions with {min_zeros}+ leading zeros")
    
    # Phase 2: Analyze transaction details for collected transactions
    print(f"\n=== PHASE 2: Analyzing {len(zero_transactions)} transactions with {min_zeros}+ leading zeros ===")
    phase2_start = time.time()
    
    special_txs = []
    zero_txs = []
    
    if zero_transactions:
        print(f"Found {len(zero_transactions)} transactions to analyze in detail...")
        
        # Process in batches to avoid overwhelming the RPC
        tx_batch_size = 100
        
        for i in range(0, len(zero_transactions), tx_batch_size):
            batch = zero_transactions[i:i + tx_batch_size]
            
            if verbose or i % (tx_batch_size * 10) == 0:
                progress = (i / len(zero_transactions)) * 100
                print(f'Analyzing transaction details: {progress:.1f}% ({i}/{len(zero_transactions)})')
            
            # Update status for phase 2
            current_tx = i + len(batch)
            tx_progress = (current_tx / len(zero_transactions)) * 100 if len(zero_transactions) > 0 else 100
            update_status(end_block, start_block, total_blocks, f"phase2 ({tx_progress:.1f}% of transactions)")
            
            # Batch get transaction data
            tx_calls = [('getrawtransaction', [txid, True]) for _, txid, _, _ in batch]
            tx_data_list = rpc.batch_call(tx_calls)
            
            # Process transaction data
            for j, tx_data in enumerate(tx_data_list):
                if not tx_data:
                    continue
                
                block_height, txid, leading_zeros, is_coinbase = batch[j]
                
                num_inputs = len(tx_data.get('vin', []))
                num_outputs = len(tx_data.get('vout', []))
                
                if is_coinbase:
                    stats['coinbase_transactions'] += 1
                
                # Only count multi-input for non-coinbase transactions
                if num_inputs > 1 and not is_coinbase:
                    stats['multi_input_transactions'] += 1
                
                # Special transaction: min_zeros+ zeros + at least min_inputs input + optionally exclude coinbase
                coinbase_filter = not is_coinbase if exclude_coinbase else True
                if leading_zeros >= min_zeros and num_inputs >= min_inputs and coinbase_filter:
                    stats['special_transactions'] += 1
                    special_txs.append({
                        'block': block_height,
                        'txid': txid,
                        'zeros': leading_zeros,
                        'inputs': num_inputs,
                        'outputs': num_outputs,
                        'coinbase': is_coinbase
                    })
                
                # All transactions with min_zeros+ zeros
                if leading_zeros >= min_zeros and show_all_zeros and coinbase_filter:
                    zero_txs.append({
                        'block': block_height,
                        'txid': txid,
                        'zeros': leading_zeros,
                        'inputs': num_inputs,
                        'outputs': num_outputs,
                        'coinbase': is_coinbase
                    })
        
        phase2_time = time.time() - phase2_start
        print(f"\nPhase 2 completed in {phase2_time:.2f} seconds")
    
    end_time = time.time()
    total_elapsed = end_time - start_time
    
    print('\n\n=== ANALYSIS SUMMARY ===')
    print(f'Blocks analyzed: {stats["blocks_analyzed"]}')
    print(f'Transactions analyzed: {stats["transactions_analyzed"]}')
    print(f'Coinbase transactions: {stats["coinbase_transactions"]}')
    print(f'Multi-input transactions: {stats["multi_input_transactions"]}')
    
    zero_count = sum(stats['transactions_with_zeros'].values())
    print(f'Transactions with {min_zeros}+ leading zeros: {zero_count}')
    
    if stats['transactions_with_zeros']:
        for zeros, count in sorted(stats['transactions_with_zeros'].items()):
            print(f'  {zeros} leading zeros: {count} transactions')
    
    print(f'SPECIAL transactions ({min_zeros}+ zeros + at least {min_inputs} input + non-coinbase): {stats["special_transactions"]}')
    
    if special_txs:
        print('\nSpecial transactions found:')
        for tx in special_txs:
            print(f'  Block {tx["block"]}: {tx["txid"]} ({tx["zeros"]} zeros, {tx["inputs"]} inputs, {tx["outputs"]} outputs)')
    
    if show_all_zeros and zero_txs:
        print(f'\nAll transactions with {min_zeros}+ leading zeros:')
        for tx in zero_txs:
            coinbase_str = ' (COINBASE)' if tx["coinbase"] else ''
            print(f'  Block {tx["block"]}: {tx["txid"]} ({tx["zeros"]} zeros, {tx["inputs"]} inputs, {tx["outputs"]} outputs){coinbase_str}')
    
    print(f'\nTotal analysis time: {total_elapsed:.2f} seconds')
    print(f'Rate: {stats["blocks_analyzed"] / total_elapsed:.2f} blocks/sec')
    print(f'Phase 1 (collection): {phase1_time:.2f}s, Phase 2 (analysis): {total_elapsed - phase1_time:.2f}s')
    
    # Final status update
    update_status(end_block, start_block, total_blocks, "completed")
    
    return stats, special_txs, zero_txs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze Bitcoin blocks for special transactions using RPC')
    parser.add_argument('--start', type=int, required=True, help='Start block height')
    parser.add_argument('--end', type=int, required=True, help='End block height')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for block processing (default: 1000)')
    parser.add_argument('--min-zeros', type=int, default=2, help='Minimum leading zeros to consider (default: 2)')
    parser.add_argument('--min-inputs', type=int, default=1, help='Minimum inputs for special transactions (default: 1)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--show-all-zeros', action='store_true', help='Show all transactions with min_zeros+ leading zeros')
    parser.add_argument('--exclude-coinbase', action='store_true', help='Exclude coinbase transactions from results')
    
    args = parser.parse_args()
    
    analyze_blocks_rpc(args.start, args.end, args.batch_size, args.verbose, args.show_all_zeros, args.min_zeros, args.min_inputs, args.exclude_coinbase)