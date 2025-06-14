#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = '/root/b1t-web-analyzer/analysis.db'

def check_rpc_config():
    """Check and display RPC configuration."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if rpc_config table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rpc_config'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("RPC config table does not exist. Creating...")
            cursor.execute('''
                CREATE TABLE rpc_config (
                    id INTEGER PRIMARY KEY,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    timeout INTEGER DEFAULT 30
                )
            ''')
            
            # Insert default configuration
            cursor.execute('''
                INSERT INTO rpc_config (id, host, port, username, password, timeout)
                VALUES (1, '127.0.0.1', 8332, 'rpcuser', 'rpcpassword', 30)
            ''')
            conn.commit()
            print("Default RPC configuration created.")
        else:
            print("RPC config table exists.")
        
        # Display current configuration
        cursor.execute('SELECT * FROM rpc_config')
        configs = cursor.fetchall()
        
        if configs:
            print("\nCurrent RPC configurations:")
            for config in configs:
                print(f"ID: {config[0]}, Host: {config[1]}, Port: {config[2]}, Username: {config[3]}, Password: {config[4]}, Timeout: {config[5]}")
        else:
            print("No RPC configurations found.")
            
        conn.close()
        
    except Exception as e:
        print(f"Error checking RPC config: {e}")

def check_bit_config():
    """Check if bit.conf exists and display relevant settings."""
    bit_conf_path = '/root/.bit/bit.conf'
    
    if os.path.exists(bit_conf_path):
        print(f"\nbit.conf found at {bit_conf_path}")
        try:
            with open(bit_conf_path, 'r') as f:
                content = f.read()
                print("\nbit.conf content:")
                print(content)
        except Exception as e:
            print(f"Error reading bit.conf: {e}")
    else:
        print(f"\nbit.conf not found at {bit_conf_path}")
        print("Creating default bit.conf...")
        
        try:
            os.makedirs('/root/.bit', exist_ok=True)
            with open(bit_conf_path, 'w') as f:
                f.write("""# B1t Core configuration
server=1
rpcuser=rpcuser
rpcpassword=rpcpassword
rpcallowip=127.0.0.1
rpcport=8332
daemon=1
""")
            print("Default bit.conf created.")
        except Exception as e:
            print(f"Error creating bit.conf: {e}")

if __name__ == '__main__':
    print("Checking RPC configuration...")
    check_rpc_config()
    check_bit_config()
    print("\nDone.")