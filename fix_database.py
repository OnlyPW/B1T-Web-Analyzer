#!/usr/bin/env python3
"""
Database fix script for B1T Web Analyzer
Fixes timestamp issues and ensures proper database structure
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'analyzer.db'

def fix_database():
    """Fix database structure and data issues."""
    print("Fixing database structure and data...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if we need to add missing columns
        cursor.execute("PRAGMA table_info(analysis_jobs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add missing columns if they don't exist
        if 'started_at' not in columns:
            print("Adding started_at column...")
            cursor.execute('ALTER TABLE analysis_jobs ADD COLUMN started_at TIMESTAMP')
        
        if 'completed_at' not in columns:
            print("Adding completed_at column...")
            cursor.execute('ALTER TABLE analysis_jobs ADD COLUMN completed_at TIMESTAMP')
        
        # Fix any jobs that are stuck in 'pending' status
        print("Checking for stuck jobs...")
        cursor.execute("SELECT COUNT(*) FROM analysis_jobs WHERE status = 'pending'")
        pending_count = cursor.fetchone()[0]
        
        if pending_count > 0:
            print(f"Found {pending_count} pending jobs. Updating their status...")
            # Set old pending jobs to failed if they're more than 1 hour old
            cursor.execute("""
                UPDATE analysis_jobs 
                SET status = 'failed', 
                    error_message = 'Job was stuck in pending status - reset by database fix',
                    completed_at = CURRENT_TIMESTAMP
                WHERE status = 'pending' 
                AND datetime(created_at) < datetime('now', '-1 hour')
            """)
        
        # Update any jobs missing timestamps
        print("Fixing missing timestamps...")
        cursor.execute("""
            UPDATE analysis_jobs 
            SET started_at = created_at 
            WHERE status IN ('running', 'completed', 'failed') 
            AND started_at IS NULL
        """)
        
        cursor.execute("""
            UPDATE analysis_jobs 
            SET completed_at = created_at 
            WHERE status IN ('completed', 'failed') 
            AND completed_at IS NULL
        """)
        
        conn.commit()
        print("Database fixes applied successfully!")
        
        # Show current job status
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM analysis_jobs 
            GROUP BY status
        """)
        status_counts = cursor.fetchall()
        
        print("\nCurrent job status summary:")
        for status, count in status_counts:
            print(f"  {status}: {count} jobs")
        
    except Exception as e:
        print(f"Error fixing database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    if os.path.exists(DB_PATH):
        fix_database()
    else:
        print(f"Database file {DB_PATH} not found. Run the main application first to create it.")