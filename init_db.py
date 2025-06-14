#!/usr/bin/env python3
import sqlite3

def init_database():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect('analyzer.db')
    cursor = conn.cursor()
    
    # Create analysis_jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_block INTEGER NOT NULL,
            end_block INTEGER NOT NULL,
            batch_size INTEGER DEFAULT 1000,
            min_zeros INTEGER DEFAULT 2,
            min_inputs INTEGER DEFAULT 1,
        show_all_zeros BOOLEAN DEFAULT FALSE,
            exclude_coinbase BOOLEAN DEFAULT TRUE,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            results TEXT,
            error_message TEXT
        )
    ''')
    
    # Create analysis_results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            block_number INTEGER,
            transaction_hash TEXT,
            leading_zeros INTEGER,
            num_inputs INTEGER,
            is_special BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES analysis_jobs (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()