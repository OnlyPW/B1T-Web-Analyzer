#!/usr/bin/env python3
"""
Script to check application logs and analyze failed jobs
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = '/root/b1t-web-analyzer/analyzer.db'

def check_failed_jobs():
    """Check for failed jobs and their error messages"""
    print("=== Checking Failed Jobs ===")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all failed jobs
        cursor.execute('''
            SELECT id, name, start_block, end_block, status, created_at, 
                   started_at, completed_at, error_message
            FROM analysis_jobs 
            WHERE status = 'failed'
            ORDER BY created_at DESC
        ''')
        
        failed_jobs = cursor.fetchall()
        
        if not failed_jobs:
            print("No failed jobs found.")
        else:
            print(f"Found {len(failed_jobs)} failed jobs:")
            print()
            
            for job in failed_jobs:
                print(f"Job ID: {job[0]}")
                print(f"Name: {job[1]}")
                print(f"Block Range: {job[2]} - {job[3]}")
                print(f"Status: {job[4]}")
                print(f"Created: {job[5]}")
                print(f"Started: {job[6] or 'N/A'}")
                print(f"Completed: {job[7] or 'N/A'}")
                print(f"Error Message: {job[8] or 'No error message'}")
                print("-" * 50)
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking failed jobs: {e}")

def check_recent_jobs():
    """Check recent jobs and their status"""
    print("\n=== Recent Jobs Status ===")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get recent jobs
        cursor.execute('''
            SELECT id, name, start_block, end_block, status, created_at, 
                   started_at, completed_at, error_message
            FROM analysis_jobs 
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        
        recent_jobs = cursor.fetchall()
        
        if not recent_jobs:
            print("No jobs found.")
        else:
            print(f"Last {len(recent_jobs)} jobs:")
            print()
            
            for job in recent_jobs:
                print(f"Job {job[0]}: {job[1]} ({job[4]})")
                print(f"  Range: {job[2]} - {job[3]}")
                print(f"  Created: {job[5]}")
                if job[8]:  # error_message
                    print(f"  Error: {job[8]}")
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking recent jobs: {e}")

def check_database_integrity():
    """Check database integrity and structure"""
    print("\n=== Database Integrity Check ===")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables in database: {[table[0] for table in tables]}")
        
        # Check job counts
        cursor.execute('SELECT COUNT(*) FROM analysis_jobs')
        job_count = cursor.fetchone()[0]
        print(f"Total jobs: {job_count}")
        
        cursor.execute('SELECT COUNT(*) FROM analysis_results')
        result_count = cursor.fetchone()[0]
        print(f"Total results: {result_count}")
        
        # Check status distribution
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM analysis_jobs 
            GROUP BY status
        ''')
        status_counts = cursor.fetchall()
        print("\nJob status distribution:")
        for status, count in status_counts:
            print(f"  {status}: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database integrity: {e}")

def check_rpc_connection():
    """Check RPC connection status"""
    print("\n=== RPC Connection Check ===")
    
    try:
        import requests
        import configparser
        
        # Read bit.conf
        conf_path = '/root/.bit/bit.conf'
        if os.path.exists(conf_path):
            config = configparser.ConfigParser()
            config.read(conf_path)
            
            rpc_user = None
            rpc_password = None
            rpc_port = 8332
            
            with open(conf_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('rpcuser='):
                        rpc_user = line.split('=', 1)[1]
                    elif line.startswith('rpcpassword='):
                        rpc_password = line.split('=', 1)[1]
                    elif line.startswith('rpcport='):
                        rpc_port = int(line.split('=', 1)[1])
            
            print(f"RPC Config - User: {rpc_user}, Port: {rpc_port}")
            
            # Test RPC connection
            url = f'http://127.0.0.1:{rpc_port}'
            auth = (rpc_user, rpc_password)
            
            payload = {
                'jsonrpc': '1.0',
                'id': 'test',
                'method': 'getblockcount',
                'params': []
            }
            
            response = requests.post(url, json=payload, auth=auth, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    print(f"RPC Connection: SUCCESS - Block height: {result['result']}")
                else:
                    print(f"RPC Connection: ERROR - {result.get('error', 'Unknown error')}")
            else:
                print(f"RPC Connection: FAILED - HTTP {response.status_code}")
                
        else:
            print(f"bit.conf not found at {conf_path}")
            
    except Exception as e:
        print(f"Error checking RPC connection: {e}")

if __name__ == '__main__':
    print(f"B1T Web Analyzer Log Check - {datetime.now()}")
    print("=" * 60)
    
    check_database_integrity()
    check_recent_jobs()
    check_failed_jobs()
    check_rpc_connection()
    
    print("\n=== Log Check Complete ===")