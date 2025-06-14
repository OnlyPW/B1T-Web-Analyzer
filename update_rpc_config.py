#!/usr/bin/env python3
import sqlite3

DB_PATH = '/root/b1t-web-analyzer/analysis.db'

def update_rpc_config():
    """Update RPC configuration with correct credentials."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Update existing configuration
        cursor.execute('''
            UPDATE rpc_config 
            SET host = '127.0.0.1',
                port = 8332,
                username = 'bitrpc_OnlyPW',
                password = '97bBe22qXTQec11CDyr7V3ehyOU52MCV27Dx4qMI',
                timeout = 30
            WHERE id = 1
        ''')
        
        # If no rows were updated, insert new configuration
        if cursor.rowcount == 0:
            cursor.execute('''
                INSERT INTO rpc_config (id, host, port, username, password, timeout)
                VALUES (1, '127.0.0.1', 8332, 'bitrpc_OnlyPW', '97bBe22qXTQec11CDyr7V3ehyOU52MCV27Dx4qMI', 30)
            ''')
            print("New RPC configuration inserted.")
        else:
            print("RPC configuration updated.")
        
        conn.commit()
        
        # Verify the update
        cursor.execute('SELECT * FROM rpc_config WHERE id = 1')
        config = cursor.fetchone()
        
        if config:
            print(f"\nUpdated configuration:")
            print(f"Host: {config[1]}")
            print(f"Port: {config[2]}")
            print(f"Username: {config[3]}")
            print(f"Password: {config[4][:10]}...")
            print(f"Timeout: {config[5]}")
        
        conn.close()
        print("\nRPC configuration update completed successfully.")
        
    except Exception as e:
        print(f"Error updating RPC config: {e}")

if __name__ == '__main__':
    update_rpc_config()