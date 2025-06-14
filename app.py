#!/usr/bin/env python3
"""
B1T Web Analyzer - Flask Web Interface for Blockchain Analysis

This application provides a web interface for configuring and running
blockchain analysis tasks using RPC connections.
"""

import os
import sqlite3
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from dotenv import load_dotenv
import subprocess
import sys
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app.logger.setLevel(logging.DEBUG)

# Database configuration
DB_PATH = 'analyzer.db'

# Global variables for tracking analysis status and job queue
analysis_status = {
    'running': False,
    'progress': 0,
    'current_block': 0,
    'total_blocks': 0,
    'start_time': None,
    'results': None,
    'error': None,
    'current_job_id': None,
    'current_job_name': None
}

# Job queue management
job_queue = []
queue_lock = threading.Lock()
queue_worker_thread = None
queue_worker_running = False

def init_database():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DB_PATH)
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
            status TEXT DEFAULT 'pending', -- pending, queued, running, completed, failed
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
    
    # Create rpc_config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rpc_config (
            id INTEGER PRIMARY KEY,
            host TEXT DEFAULT 'localhost',
            port INTEGER DEFAULT 8332,
            username TEXT,
            password TEXT,
            timeout INTEGER DEFAULT 30,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default RPC config if not exists
    cursor.execute('SELECT COUNT(*) FROM rpc_config')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO rpc_config (host, port, username, password, timeout)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            os.environ.get('RPC_HOST', '127.0.0.1'),
            int(os.environ.get('RPC_PORT', 8332)),
            os.environ.get('RPC_USER', 'bitrpc_OnlyPW'),
            os.environ.get('RPC_PASS', '97bBe22qXTQec11CDyr7V3ehyOU52MCV27Dx4qMI'),
            int(os.environ.get('RPC_TIMEOUT', 30))
        ))
    
    conn.commit()
    conn.close()

def get_rpc_config():
    """Get RPC configuration from database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT host, port, username, password, timeout FROM rpc_config WHERE id = 1')
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'host': result[0],
            'port': result[1],
            'username': result[2],
            'password': result[3],
            'timeout': result[4]
        }
    return None

def make_rpc_call(method, params=None):
    """Make RPC call to B1t node."""
    config = get_rpc_config()
    if not config:
        return None
    
    url = f"http://{config['host']}:{config['port']}"
    headers = {'content-type': 'application/json'}
    
    payload = {
        'method': method,
        'params': params or [],
        'jsonrpc': '2.0',
        'id': 1
    }
    
    try:
        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=headers,
            auth=(config['username'], config['password']),
            timeout=config['timeout']
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'result' in result:
                return result['result']
            elif 'error' in result:
                print(f"RPC Error: {result['error']}")
                return None
        else:
            print(f"HTTP Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"RPC Exception: {str(e)}")
        return None

def get_blockchain_height():
    """Get current blockchain height."""
    return make_rpc_call('getblockcount')

def get_blockchain_info():
    """Get blockchain information including current height and progress."""
    block_count = make_rpc_call('getblockcount')
    blockchain_info = make_rpc_call('getblockchaininfo')
    
    if block_count is not None and blockchain_info is not None:
        return {
            'height': block_count,
            'blocks': blockchain_info.get('blocks', block_count),
            'headers': blockchain_info.get('headers', block_count),
            'verification_progress': blockchain_info.get('verificationprogress', 1.0),
            'chain': blockchain_info.get('chain', 'unknown')
        }
    return None

def parse_analysis_output(output):
    """Parse the analysis output and extract structured data."""
    parsed_data = {
        'blocks_analyzed': 0,
        'transactions_analyzed': 0,
        'coinbase_transactions': 0,
        'multi_input_transactions': 0,
        'zero_transactions': 0,
        'zero_breakdown': {},
        'special_transactions': 0,
        'special_transaction_details': [],
        'analysis_time': 0,
        'rate': 0,
        'phase1_time': 0,
        'phase2_time': 0
    }
    
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Parse summary statistics
        if 'Blocks analyzed:' in line:
            parsed_data['blocks_analyzed'] = int(line.split(':')[1].strip())
        elif 'Transactions analyzed:' in line:
            parsed_data['transactions_analyzed'] = int(line.split(':')[1].strip())
        elif 'Coinbase transactions:' in line:
            parsed_data['coinbase_transactions'] = int(line.split(':')[1].strip())
        elif 'Multi-input transactions:' in line:
            parsed_data['multi_input_transactions'] = int(line.split(':')[1].strip())
        elif 'Transactions with' in line and 'leading zeros:' in line:
            try:
                # Extract the number after the colon
                value_str = line.split(':')[1].strip()
                parsed_data['zero_transactions'] = int(value_str)
                app.logger.debug(f"Parsed zero_transactions: {value_str} -> {parsed_data['zero_transactions']}")
            except (ValueError, IndexError) as e:
                app.logger.error(f"Failed to parse zero_transactions from line: '{line}' - Error: {e}")
                parsed_data['zero_transactions'] = 0
        elif 'SPECIAL transactions' in line:
            parsed_data['special_transactions'] = int(line.split(':')[1].strip())
        elif 'Total analysis time:' in line:
            try:
                time_str = line.split(':')[1].strip().replace(' seconds', '')
                parsed_data['analysis_time'] = float(time_str)
            except (ValueError, IndexError) as e:
                app.logger.warning(f"Could not parse analysis time from line: {line} - {e}")
                parsed_data['analysis_time'] = 0.0
        elif 'Rate:' in line and 'blocks/sec' in line:
            try:
                rate_str = line.split(':')[1].strip().replace(' blocks/sec', '')
                # Handle cases like "0.00, Zero TXs found"
                if ',' in rate_str:
                    rate_str = rate_str.split(',')[0].strip()
                parsed_data['rate'] = float(rate_str)
            except (ValueError, IndexError) as e:
                app.logger.warning(f"Could not parse rate from line: {line} - {e}")
                parsed_data['rate'] = 0.0
        elif 'Phase 1 (collection):' in line:
            try:
                parts = line.split(',')
                phase1_time = parts[0].split(':')[1].strip().replace('s', '')
                phase2_time = parts[1].split(':')[1].strip().replace('s', '')
                parsed_data['phase1_time'] = float(phase1_time)
                parsed_data['phase2_time'] = float(phase2_time)
            except (ValueError, IndexError) as e:
                app.logger.warning(f"Could not parse phase times from line: {line} - {e}")
                parsed_data['phase1_time'] = 0.0
                parsed_data['phase2_time'] = 0.0
        
        # Parse zero breakdown
        if ' leading zeros:' in line and 'transactions' in line:
            try:
                parts = line.strip().split(' ')
                if len(parts) >= 4:
                    zeros = parts[0]
                    count = parts[3]
                    # Skip lines with '+' in zeros as they are summary lines
                    if '+' not in zeros:
                        parsed_data['zero_breakdown'][zeros] = int(count)
                        app.logger.debug(f"Parsed zero breakdown: {zeros} -> {count}")
                    else:
                        app.logger.debug(f"Skipping summary line with '+': {line}")
            except (ValueError, IndexError) as e:
                app.logger.error(f"Failed to parse zero breakdown from line: '{line}' - Error: {e}")
                continue
        
        # Parse special transactions
        if 'Block ' in line and ':' in line and 'zeros' in line and 'inputs' in line:
            # Extract transaction details
            parts = line.split(':')
            if len(parts) >= 2:
                block_part = parts[0].strip()
                tx_part = parts[1].strip()
                
                block_num = block_part.replace('Block ', '')
                tx_details = tx_part.split(' ')
                
                if len(tx_details) >= 1:
                    tx_hash = tx_details[0]
                    
                    # Extract additional info from parentheses
                    paren_info = ''
                    if '(' in line and ')' in line:
                        paren_info = line[line.find('(')+1:line.find(')')]
                    
                    parsed_data['special_transaction_details'].append({
                        'block': block_num,
                        'hash': tx_hash,
                        'details': paren_info
                    })
    
    return parsed_data

def add_job_to_queue(job_id, name, start_block, end_block, batch_size, min_zeros, min_inputs, show_all_zeros, exclude_coinbase):
    """Add a job to the processing queue."""
    global queue_worker_thread, queue_worker_running
    
    with queue_lock:
        job_queue.append({
            'job_id': job_id,
            'name': name,
            'start_block': start_block,
            'end_block': end_block,
            'batch_size': batch_size,
            'min_zeros': min_zeros,
            'min_inputs': min_inputs,
            'show_all_zeros': show_all_zeros,
            'exclude_coinbase': exclude_coinbase
        })
        
        # Update job status to queued
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE analysis_jobs 
            SET status = 'queued'
            WHERE id = ?
        ''', (job_id,))
        conn.commit()
        conn.close()
        
        app.logger.info(f"Job {job_id} ({name}) added to queue. Queue length: {len(job_queue)}")
        
        # Start queue worker if not running
        if not queue_worker_running:
            start_queue_worker()

def start_queue_worker():
    """Start the queue worker thread."""
    global queue_worker_thread, queue_worker_running
    
    if queue_worker_running:
        return
        
    queue_worker_running = True
    queue_worker_thread = threading.Thread(target=queue_worker, daemon=True)
    queue_worker_thread.start()
    app.logger.info("Queue worker started")

def queue_worker():
    """Worker thread that processes jobs from the queue."""
    global queue_worker_running
    
    app.logger.info("Queue worker thread started")
    
    while queue_worker_running:
        job = None
        
        with queue_lock:
            if job_queue:
                job = job_queue.pop(0)
                app.logger.info(f"Processing job {job['job_id']} from queue. Remaining jobs: {len(job_queue)}")
        
        if job:
            try:
                run_analysis_job(
                    job['job_id'], job['name'], job['start_block'], job['end_block'],
                    job['batch_size'], job['min_zeros'], job['min_inputs'],
                    job['show_all_zeros'], job['exclude_coinbase']
                )
            except Exception as e:
                app.logger.error(f"Error processing job {job['job_id']}: {e}")
                # Update job status to failed
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE analysis_jobs 
                        SET status = 'failed', completed_at = CURRENT_TIMESTAMP, error_message = ?
                        WHERE id = ?
                    ''', (f"Queue processing error: {str(e)}", job['job_id']))
                    conn.commit()
                    conn.close()
                except Exception as db_error:
                    app.logger.error(f"Failed to update job {job['job_id']} status: {db_error}")
        else:
            # No jobs in queue, wait a bit
            time.sleep(1)
            
            # Check if we should stop the worker (no jobs for a while)
            with queue_lock:
                if not job_queue:
                    queue_worker_running = False
                    app.logger.info("Queue worker stopping - no jobs in queue")
                    break
    
    app.logger.info("Queue worker thread ended")

def get_queue_status():
    """Get current queue status."""
    with queue_lock:
        return {
            'queue_length': len(job_queue),
            'jobs': [{
                'job_id': job['job_id'],
                'name': job['name'],
                'start_block': job['start_block'],
                'end_block': job['end_block']
            } for job in job_queue],
            'worker_running': queue_worker_running
        }

def run_analysis_job(job_id, name, start_block, end_block, batch_size, min_zeros, min_inputs, show_all_zeros, exclude_coinbase):
    """Run the analysis job in a separate thread."""
    global analysis_status
    
    try:
        analysis_status['running'] = True
        analysis_status['progress'] = 0
        analysis_status['current_block'] = start_block
        analysis_status['total_blocks'] = end_block - start_block + 1
        analysis_status['start_time'] = datetime.now()
        analysis_status['error'] = None
        analysis_status['results'] = None
        analysis_status['current_job_id'] = job_id
        analysis_status['current_job_name'] = name
        
        # Update job status to running
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE analysis_jobs 
            SET status = 'running', started_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (job_id,))
        conn.commit()
        conn.close()
        
        # Build command arguments
        cmd = [
            sys.executable, 'final_analyzer_rpc.py',
            '--start', str(start_block),
            '--end', str(end_block),
            '--batch-size', str(batch_size),
            '--min-zeros', str(min_zeros),
            '--min-inputs', str(min_inputs),
            '--verbose'
        ]
        
        if show_all_zeros:
            cmd.append('--show-all-zeros')
            
        if exclude_coinbase:
            cmd.append('--exclude-coinbase')
        
        # Log the command being executed
        app.logger.info(f"Starting analysis job {job_id}: {' '.join(cmd)}")
        app.logger.info(f"Job parameters - Name: {name}, Blocks: {start_block}-{end_block}, Batch: {batch_size}, Show zeros: {show_all_zeros}")
        
        # Run the analysis
        app.logger.info(f"Executing analysis command for job {job_id}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='/root/b1t-web-analyzer')
        
        app.logger.info(f"Analysis job {job_id} completed with return code: {result.returncode}")
        
        if result.returncode == 0:
            app.logger.info(f"Job {job_id} completed successfully")
            # Parse results and store in database
            parsed_analysis = parse_analysis_output(result.stdout)
            results_data = {
                'output': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode,
                'parsed': parsed_analysis
            }
            
            # Update job as completed
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                results_json = json.dumps(results_data)
                app.logger.debug(f"Saving results for job {job_id}, JSON length: {len(results_json)}")
                app.logger.debug(f"Results JSON preview (first 200 chars): {results_json[:200]}...")
                cursor.execute('''
                    UPDATE analysis_jobs 
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP, results = ?
                    WHERE id = ?
                ''', (results_json, job_id))
                conn.commit()
                app.logger.info(f"Job {job_id} results saved successfully")
            except Exception as e:
                app.logger.error(f"Failed to save results for job {job_id}: {e}")
                cursor.execute('''
                    UPDATE analysis_jobs 
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP, error_message = ?
                    WHERE id = ?
                ''', (f"Failed to save results: {str(e)}", job_id))
                conn.commit()
            finally:
                conn.close()
            
            analysis_status['results'] = results_data
            app.logger.info(f"Job {job_id} results stored in database")
        else:
            # Handle error
            error_msg = f"Analysis failed with return code {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            app.logger.error(f"Job {job_id} failed: {error_msg}")
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE analysis_jobs 
                SET status = 'failed', completed_at = CURRENT_TIMESTAMP, error_message = ?
                WHERE id = ?
            ''', (error_msg, job_id))
            conn.commit()
            conn.close()
            
            analysis_status['error'] = error_msg
            
    except Exception as e:
        error_msg = f"Exception during analysis: {str(e)}"
        app.logger.error(f"Job {job_id} failed with exception: {error_msg}")
        analysis_status['error'] = error_msg
        
        # Update job status to failed
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE analysis_jobs 
                SET status = 'failed', completed_at = CURRENT_TIMESTAMP, error_message = ?
                WHERE id = ?
            ''', (error_msg, job_id))
            conn.commit()
            conn.close()
        except Exception as db_error:
            app.logger.error(f"Failed to update job {job_id} status in database: {db_error}")
    
    finally:
        analysis_status['running'] = False
        analysis_status['progress'] = 100
        analysis_status['current_job_id'] = None
        analysis_status['current_job_name'] = None

@app.route('/')
def index():
    """Main dashboard page."""
    # Get recent jobs
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, start_block, end_block, status, created_at, completed_at
        FROM analysis_jobs 
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    recent_jobs = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', recent_jobs=recent_jobs, analysis_status=analysis_status)

@app.route('/new_job')
def new_job():
    """New analysis job form."""
    return render_template('new_job.html')

@app.route('/submit_job', methods=['POST'])
def submit_job():
    """Submit new analysis job."""
    try:
        name = request.form['name']
        start_block = int(request.form['start_block'])
        end_block = int(request.form['end_block'])
        batch_size = int(request.form.get('batch_size', 1000))
        min_zeros = int(request.form.get('min_zeros', 2))
        min_inputs = int(request.form.get('min_inputs', 1))

        show_all_zeros = 'show_all_zeros' in request.form
        exclude_coinbase = 'exclude_coinbase' in request.form
        
        if start_block >= end_block:
            flash('Start block must be less than end block', 'error')
            return redirect(url_for('new_job'))
        
        # Insert job into database
        app.logger.info(f"Connecting to database: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if database and table exist
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_jobs';")
            table_exists = cursor.fetchone()
            app.logger.info(f"Table analysis_jobs exists: {table_exists is not None}")
            
            if table_exists:
                cursor.execute("PRAGMA table_info(analysis_jobs);")
                columns = cursor.fetchall()
                app.logger.info(f"Table columns: {columns}")
                
                # Check specifically for min_inputs column
                min_inputs_exists = any('min_inputs' in str(col) for col in columns)
                app.logger.info(f"min_inputs column exists: {min_inputs_exists}")
            
            app.logger.info(f"Attempting to insert job with values: name={name}, start_block={start_block}, end_block={end_block}, batch_size={batch_size}, min_zeros={min_zeros}, min_inputs={min_inputs}, show_all_zeros={show_all_zeros}, exclude_coinbase={exclude_coinbase}")
            
            cursor.execute('''
                INSERT INTO analysis_jobs (name, start_block, end_block, batch_size, min_zeros, min_inputs, show_all_zeros, exclude_coinbase)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, start_block, end_block, batch_size, min_zeros, min_inputs, show_all_zeros, exclude_coinbase))
            job_id = cursor.lastrowid
            conn.commit()
            app.logger.info(f"Successfully inserted job with ID: {job_id}")
            
        except Exception as e:
            app.logger.error(f"Database error: {str(e)}")
            app.logger.error(f"Database path: {DB_PATH}")
            conn.rollback()
            flash(f'Error submitting job: {str(e)}', 'error')
            return redirect(url_for('new_job'))
        finally:
            conn.close()
        
        # Add job to queue instead of starting immediately
        add_job_to_queue(job_id, name, start_block, end_block, batch_size, min_zeros, min_inputs, show_all_zeros, exclude_coinbase)
        
        flash(f'Analysis job "{name}" added to queue successfully!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'Error submitting job: {str(e)}', 'error')
        return redirect(url_for('new_job'))

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    """Job detail page."""
    app.logger.info(f"Viewing job detail for job ID: {job_id}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, start_block, end_block, batch_size, min_zeros, min_inputs, show_all_zeros,
               status, created_at, started_at, completed_at, results, error_message
        FROM analysis_jobs 
        WHERE id = ?
    ''', (job_id,))
    job = cursor.fetchone()
    conn.close()
    
    if not job:
        app.logger.warning(f"Job with ID {job_id} not found")
        flash('Job not found', 'error')
        return redirect(url_for('index'))
    
    app.logger.info(f"Job {job_id} status: {job[8]}, created: {job[9]}")
    
    # Parse results if available
    results = None
    app.logger.debug(f"Job {job_id} results column type: {type(job[12])}, value: {repr(job[12])[:200]}...")
    
    if job[12] and job[12].strip():  # results column - check for non-empty string
        app.logger.debug(f"Attempting to parse JSON for job {job_id}")
        try:
            results = json.loads(job[12])
            app.logger.info(f"Job {job_id} has results with {len(results)} entries")
        except json.JSONDecodeError as e:
            app.logger.error(f"JSON decode error for job {job_id}: {e}")
            app.logger.error(f"Raw results data (first 200 chars): {repr(job[12][:200])}")
        except Exception as e:
            app.logger.error(f"Unexpected error parsing results for job {job_id}: {e}")
            app.logger.error(f"Raw results data (first 200 chars): {repr(job[12][:200])}")
    
    # Log error message if present
    if job[13]:  # error_message column
        app.logger.error(f"Job {job_id} has error: {job[13]}")
    
    return render_template('job_detail.html', job=job, results=results, analysis_status=analysis_status)

# RPC configuration removed - settings are managed via .env file

@app.route('/api/status')
def api_status():
    """API endpoint for getting analysis status."""
    return jsonify(analysis_status)

@app.route('/api/blockchain_info')
def api_blockchain_info():
    """API endpoint for getting blockchain information."""
    info = get_blockchain_info()
    if info:
        return jsonify(info)
    else:
        return jsonify({'error': 'Unable to connect to blockchain node'}), 500

@app.route('/api/analysis_status')
def api_analysis_status():
    """API endpoint for getting current analysis status."""
    # Try to read status from file first
    try:
        with open('/tmp/b1t_analysis_status.json', 'r') as f:
            file_status = json.load(f)
            
        # Check if status is recent (within last 30 seconds)
        if time.time() - file_status.get('timestamp', 0) < 30:
            return jsonify({
                'running': analysis_status['running'],
                'progress': file_status.get('progress', 0),
                'current_block': file_status.get('current_block', 0),
                'total_blocks': file_status.get('total_blocks', 0),
                'phase': file_status.get('phase', 'unknown'),
                'blocks_processed': file_status.get('blocks_processed', 0),
                'current_job_id': analysis_status.get('current_job_id'),
                'current_job_name': analysis_status.get('current_job_name')
            })
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    
    # Fallback to in-memory status
    return jsonify({
        'running': analysis_status['running'],
        'progress': analysis_status['progress'],
        'current_block': analysis_status['current_block'],
        'total_blocks': analysis_status['total_blocks'],
        'phase': 'unknown',
        'blocks_processed': 0,
        'current_job_id': analysis_status.get('current_job_id'),
        'current_job_name': analysis_status.get('current_job_name')
    })

@app.route('/api/queue_status')
def api_queue_status():
    """API endpoint for getting current queue status."""
    queue_status = get_queue_status()
    return jsonify(queue_status)

@app.route('/api/delete_all_jobs', methods=['POST'])
def api_delete_all_jobs():
    """API endpoint for deleting all jobs (admin function)."""
    app.logger.info("Request to delete all jobs received")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Count existing jobs before deletion
        cursor.execute('SELECT COUNT(*) FROM analysis_jobs')
        job_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM analysis_results')
        result_count = cursor.fetchone()[0]
        
        app.logger.info(f"Deleting {job_count} jobs and {result_count} results")
        
        # Delete all analysis results first (foreign key constraint)
        cursor.execute('DELETE FROM analysis_results')
        app.logger.info("Deleted all analysis results")
        
        # Delete all analysis jobs
        cursor.execute('DELETE FROM analysis_jobs')
        app.logger.info("Deleted all analysis jobs")
        
        # Reset auto-increment counter
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="analysis_jobs"')
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="analysis_results"')
        app.logger.info("Reset auto-increment counters")
        
        conn.commit()
        conn.close()
        
        app.logger.info(f"Successfully deleted all {job_count} jobs and {result_count} results")
        return jsonify({'success': True, 'message': f'All {job_count} jobs deleted successfully'})
    except Exception as e:
        app.logger.error(f"Error deleting all jobs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/jobs')
def jobs_list():
    """List all jobs page."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, start_block, end_block, status, created_at, completed_at
        FROM analysis_jobs 
        ORDER BY created_at DESC
    ''')
    jobs = cursor.fetchall()
    conn.close()
    
    return render_template('jobs_list.html', jobs=jobs)

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)