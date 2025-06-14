#!/usr/bin/env python3
import sqlite3

DB_PATH = '/root/b1t-web-analyzer/analysis.db'

def add_min_zeros_column():
    """Add min_zeros column to analysis_jobs table if it doesn't exist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if min_zeros column exists
        cursor.execute("PRAGMA table_info(analysis_jobs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'min_zeros' not in columns:
            print("Adding min_zeros column to analysis_jobs table...")
            cursor.execute('ALTER TABLE analysis_jobs ADD COLUMN min_zeros INTEGER DEFAULT 8')
            conn.commit()
            print("min_zeros column added successfully.")
        else:
            print("min_zeros column already exists.")
        
        # Display table structure
        cursor.execute("PRAGMA table_info(analysis_jobs)")
        columns = cursor.fetchall()
        
        print("\nCurrent analysis_jobs table structure:")
        for column in columns:
            print(f"  {column[1]} {column[2]} (nullable: {not column[3]}, default: {column[4]})")
        
        conn.close()
        print("\nDatabase update completed successfully.")
        
    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == '__main__':
    add_min_zeros_column()