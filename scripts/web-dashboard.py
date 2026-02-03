#!/usr/bin/env python3
"""
Operator Test Dashboard - Web Interface
Version: 1.0
Requires: Flask, paramiko
Install: pip3 install flask paramiko
"""

from flask import Flask, render_template, jsonify, request
import subprocess
import json
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

app = Flask(__name__)

REMOTE_HOST = os.environ.get('REMOTE_HOST', 'rdu2')
REMOTE_BASE_DIR = '/root/test-rose/certsuite'
REPORT_DIR = '/var/www/html'  # Where report_* directories are created

# Setup logging
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'dashboard.log')

# Configure logging format
log_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# File handler with rotation (10MB max, keep 5 backups)
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Setup logger
logger = logging.getLogger('dashboard')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("=" * 60)
logger.info("Dashboard started")
logger.info(f"Log file: {LOG_FILE}")
logger.info(f"Remote host: {REMOTE_HOST}")
logger.info("=" * 60)

def ssh_command(cmd, log_cmd=False):
    """Execute SSH command and return output"""
    try:
        if log_cmd:
            logger.debug(f"SSH command: {cmd[:100]}...")
        result = subprocess.run(
            ['ssh', REMOTE_HOST, cmd],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0 and result.stderr:
            logger.warning(f"SSH command returned non-zero: {result.stderr[:200]}")
        return result.stdout
    except subprocess.TimeoutExpired:
        logger.error(f"SSH command timed out: {cmd[:100]}...")
        return "Error: Command timed out"
    except Exception as e:
        logger.error(f"SSH command failed: {str(e)}")
        return f"Error: {str(e)}"

def safe_int(value, default=0):
    """Safely convert a string to int, handling multi-line output"""
    try:
        # Take only the first line and strip whitespace
        first_line = value.strip().split('\n')[0].strip()
        return int(first_line) if first_line else default
    except (ValueError, IndexError):
        return default

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get current test status"""
    # Check if test is running
    is_running = ssh_command('tmux has-session -t operator-test 2>/dev/null && echo "true" || echo "false"').strip() == 'true'
    
    # Test progress tracking
    current_op = ''
    current_state = ''
    tests_completed = 0
    tests_total = 0
    tests_remaining = 0
    report_name = ''
    
    if is_running:
        # Get current operator from tmux output (handle wrapped lines)
        current_op = ssh_command('tmux capture-pane -t operator-test -p -S -100 2>/dev/null | grep "package=" | tail -1 | sed "s/.*package= //" | awk \'{print $1}\'').strip()
        
        # Get current state from the last few lines of tmux output
        recent_output = ssh_command('tmux capture-pane -t operator-test -p -S -20 2>/dev/null | tail -15').strip()
        
        # Detect current state from output
        if 'run CNF suite' in recent_output or 'Running' in recent_output:
            current_state = 'Running certsuite'
        elif 'install operator' in recent_output:
            current_state = 'Installing'
        elif 'Wait for CSV' in recent_output:
            current_state = 'Waiting for CSV'
        elif 'Remove operator' in recent_output or 'deleted' in recent_output:
            current_state = 'Cleanup'
        elif 'Wait for cleanup' in recent_output:
            current_state = 'Waiting for cleanup'
        elif 'Parse claim file' in recent_output:
            current_state = 'Processing results'
        elif 'Label' in recent_output:
            current_state = 'Labeling resources'
        elif 'Wait for package' in recent_output:
            current_state = 'Waiting for package'
        else:
            current_state = 'Processing'
        
        # Find the latest report directory in /var/www/html
        latest_report_dir = ssh_command(f'ls -td {REPORT_DIR}/report_* 2>/dev/null | head -1').strip()
        if latest_report_dir:
            report_name = os.path.basename(latest_report_dir)
            
            # Get total operators from operator-list.txt
            total_raw = ssh_command(f'wc -l < "{latest_report_dir}/operator-list.txt" 2>/dev/null || echo 0')
            tests_total = safe_int(total_raw)
            
            # Count completed tests by counting subdirectories (each operator gets a folder)
            completed_raw = ssh_command(f'find "{latest_report_dir}" -maxdepth 1 -type d | wc -l')
            # Subtract 1 for the parent directory itself
            tests_completed = max(0, safe_int(completed_raw) - 1)
            tests_remaining = max(0, tests_total - tests_completed)
        
        if current_op:
            logger.info(f"Test running - {current_op} [{current_state}] ({tests_completed}/{tests_total}) - {report_name}")
    
    return jsonify({
        'test_running': is_running,
        'current_operator': current_op,
        'current_state': current_state,
        'tests_completed': tests_completed,
        'tests_total': tests_total,
        'tests_remaining': tests_remaining,
        'report_name': report_name,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/results/latest')
def get_latest_results():
    """Get latest test results"""
    # Find the latest report directory in /var/www/html
    latest_report_dir = ssh_command(f'ls -td {REPORT_DIR}/report_* 2>/dev/null | head -1').strip()
    
    if not latest_report_dir:
        logger.debug("No report directories found")
        return jsonify({'error': 'No test reports found'})
    
    report_name = os.path.basename(latest_report_dir)
    
    # Find the log file inside the report directory (output_*.log)
    latest_log = ssh_command(f'ls -t "{latest_report_dir}"/output_*.log 2>/dev/null | head -1').strip()
    
    if not latest_log:
        return jsonify({'error': 'No log file found in report', 'report': report_name})
    
    # Count from the log file
    total_raw = ssh_command(f'grep -c "^\\*\\*\\*\\*\\*\\*\\*\\*\\*" "{latest_log}" 2>/dev/null || echo 0')
    success_raw = ssh_command(f'grep -c "operator .* installed" "{latest_log}" 2>/dev/null || echo 0')
    failed_raw = ssh_command(f'grep -c "Operator failed to install" "{latest_log}" 2>/dev/null || echo 0')
    
    total = safe_int(total_raw)
    success = safe_int(success_raw)
    failed = safe_int(failed_raw)
    success_rate = round((success / total * 100) if total > 0 else 0, 1)
    
    # Log results periodically (only when there are results)
    if total > 0:
        logger.info(f"Results: {success}/{total} passed ({success_rate}%), {failed} failed - {report_name}")
    
    return jsonify({
        'report_name': report_name,
        'log_file': latest_log,
        'total': total,
        'success': success,
        'failed': failed,
        'success_rate': success_rate
    })

@app.route('/api/test/start', methods=['POST'])
def start_test():
    """Start test execution"""
    logger.info(">>> TEST START requested")
    
    # Check if already running
    is_running = ssh_command('tmux has-session -t operator-test 2>/dev/null && echo "true" || echo "false"').strip() == 'true'
    if is_running:
        logger.warning("Test start rejected - test already running")
        return jsonify({'error': 'Test already running'}), 400
    
    # Start test
    ssh_command(f'tmux new-session -d -s operator-test "cd {REMOTE_BASE_DIR} && ./run-ocp-4.20-test-v2.sh"')
    
    logger.info("Test started successfully")
    return jsonify({'status': 'Test started', 'timestamp': datetime.now().isoformat()})

@app.route('/api/test/stop', methods=['POST'])
def stop_test():
    """Stop test execution"""
    logger.info(">>> TEST STOP requested")
    ssh_command('tmux kill-session -t operator-test 2>/dev/null')
    logger.info("Test stopped")
    return jsonify({'status': 'Test stopped'})

@app.route('/api/cleanup', methods=['POST'])
def cleanup_cluster():
    """Clean cluster"""
    logger.info(">>> CLEANUP requested")
    logger.info("Starting cluster cleanup...")
    output = ssh_command('bash /tmp/cleanup-all-test-operators-v2.sh')
    logger.info("Cleanup completed")
    return jsonify({'status': 'Cleanup complete', 'output': output})

@app.route('/api/live-output')
def get_live_output():
    """Get live test output - capture full scrollback buffer"""
    # Use -S - to capture entire scrollback history, then get last 200 lines
    output = ssh_command('tmux capture-pane -t operator-test -p -S - 2>/dev/null | tail -200').strip()
    return jsonify({'output': output})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
