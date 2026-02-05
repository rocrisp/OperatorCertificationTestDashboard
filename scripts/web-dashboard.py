#!/usr/bin/env python3
"""
Operator Test Dashboard - Web Interface
Version: 1.0
Requires: Flask, paramiko
Install: pip3 install flask paramiko
"""

from flask import Flask, render_template, jsonify, request, Response
import subprocess
import json
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

app = Flask(__name__)

# Configuration from environment variables
REMOTE_HOST = os.environ.get('REMOTE_HOST', 'rdu2')
REMOTE_BASE_DIR = os.environ.get('REMOTE_BASE_DIR', '/root/test-rose/certsuite')
REPORT_DIR = os.environ.get('REPORT_DIR', '/var/www/html')
DASHBOARD_PORT = int(os.environ.get('DASHBOARD_PORT', '5001'))
SSH_KEY_PATH = os.environ.get('SSH_KEY_PATH', '')  # Optional: path to SSH private key
SSH_USER = os.environ.get('SSH_USER', '')  # Optional: SSH username

# Catalog configuration - can be overridden by environment variables
# If not set, will be auto-discovered from cluster
REDHAT_CATALOG_INDEX = os.environ.get('REDHAT_CATALOG_INDEX', '')
CERTIFIED_CATALOG_INDEX = os.environ.get('CERTIFIED_CATALOG_INDEX', '')

# Default fallback indexes (used if env not set and cluster discovery fails)
DEFAULT_REDHAT_INDEX = 'registry.redhat.io/redhat/redhat-operator-index:v4.21'
DEFAULT_CERTIFIED_INDEX = 'registry.redhat.io/redhat/certified-operator-index:v4.21'

# KUBECONFIG path for test execution
KUBECONFIG_PATH = os.environ.get('KUBECONFIG_PATH', '~/.kcli/clusters/cluster1/auth/kubeconfig')

# Demo mode - use mock data instead of SSH
DEMO_MODE = os.environ.get('DEMO_MODE', 'false').lower() == 'true'

# Setup logging
LOG_DIR = os.environ.get('LOG_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'))
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
logger.info(f"Demo mode: {DEMO_MODE}")
logger.info("=" * 60)

# ============== DEMO MODE DATA ==============
# Sample data for demonstration when remote host is not available
import random
from datetime import timedelta

DEMO_OPERATORS = [
    'cluster-logging', 'elasticsearch-operator', 'kiali-ossm', 'jaeger-product',
    'servicemeshoperator', 'openshift-gitops-operator', 'web-terminal', 
    'advanced-cluster-management', 'multicluster-engine', 'openshift-pipelines-operator-rh',
    'rhods-operator', 'nfd', 'nvidia-gpu-operator', 'local-storage-operator',
    'ocs-operator', 'odf-operator', 'metallb-operator', 'cert-manager-operator'
]

DEMO_REPORTS = [
    {'name': 'report_2026-02-03_14-30-00_EST', 'total': 47, 'installed': 45, 'failed': 2},
    {'name': 'report_2026-02-02_10-15-00_EST', 'total': 51, 'installed': 51, 'failed': 0},
    {'name': 'report_2026-02-01_16-45-00_EST', 'total': 38, 'installed': 36, 'failed': 2},
    {'name': 'report_2026-01-31_09-00-00_EST', 'total': 42, 'installed': 40, 'failed': 2},
    {'name': 'report_2026-01-30_14-20-00_EST', 'total': 55, 'installed': 55, 'failed': 0},
    {'name': 'report_2026-01-29_11-30-00_EST', 'total': 33, 'installed': 31, 'failed': 2},
    {'name': 'report_2026-01-28_15-45-00_EST', 'total': 48, 'installed': 47, 'failed': 1},
    {'name': 'report_2026-01-27_08-30-00_EST', 'total': 44, 'installed': 42, 'failed': 2},
    {'name': 'report_2026-01-26_13-00-00_EST', 'total': 50, 'installed': 50, 'failed': 0},
    {'name': 'report_2026-01-25_10-45-00_EST', 'total': 39, 'installed': 37, 'failed': 2},
]

# Simulated test state for demo
demo_test_state = {
    'running': True,
    'start_time': datetime.now() - timedelta(minutes=random.randint(5, 45)),
    'current_index': random.randint(5, 15),
    'total': 20
}

def get_demo_status():
    """Return demo status data"""
    elapsed = datetime.now() - demo_test_state['start_time']
    # Simulate progress
    progress_rate = elapsed.total_seconds() / 180  # ~3 min per operator
    current_idx = min(int(progress_rate) + 5, demo_test_state['total'])
    
    return {
        'running': demo_test_state['running'],
        'current_operator': DEMO_OPERATORS[current_idx % len(DEMO_OPERATORS)] if demo_test_state['running'] else None,
        'total': demo_test_state['total'],
        'completed': current_idx,
        'installed': current_idx - 1,
        'remaining': max(0, demo_test_state['total'] - current_idx),
        'start_time': demo_test_state['start_time'].strftime('%Y-%m-%dT%H:%M:%S'),
        'report_name': f"report_{demo_test_state['start_time'].strftime('%Y-%m-%d_%H-%M-%S')}_EST"
    }

def get_demo_live_output():
    """Return demo live output"""
    current = get_demo_status()
    op = current['current_operator'] or 'cluster-logging'
    output_lines = [
        "=" * 60,
        f"Operator Certification Test Suite - Demo Mode",
        "=" * 60,
        "",
        f"Testing operator: {op}",
        f"  package= {op}",
        "",
        "Installing operator...",
        f"  subscription.operators.coreos.com/{op} created",
        "  Waiting for CSV to be ready...",
        f"  operator {op} installed successfully",
        "",
        "Running certsuite tests...",
        "  [INFO] Running test: operator-install",
        "  [PASS] operator-install",
        "  [INFO] Running test: operator-crd-versioning",
        "  [PASS] operator-crd-versioning", 
        "  [INFO] Running test: operator-crd-openapi-schema",
        "  [PASS] operator-crd-openapi-schema",
        "  [INFO] Running test: operator-olm-subscription",
        "  [PASS] operator-olm-subscription",
        "",
        f"Progress: {current['completed']}/{current['total']} operators completed",
        f"Elapsed: {(datetime.now() - demo_test_state['start_time']).seconds // 60} minutes",
        "",
        "=" * 60,
    ]
    return '\n'.join(output_lines)

def get_demo_reports(limit=10):
    """Return demo reports data"""
    reports = []
    for r in DEMO_REPORTS[:limit]:
        date_str = r['name'].replace('report_', '')
        reports.append({
            'name': r['name'],
            'path': f"/var/www/html/{r['name']}",
            'date': date_str,
            'total': r['total'],
            'installed': r['installed'],
            'failed': r['failed']
        })
    return reports

def get_demo_report_summary(report_name):
    """Return demo report summary"""
    # Find matching report or use defaults
    report_data = next((r for r in DEMO_REPORTS if r['name'] == report_name), DEMO_REPORTS[0])
    
    total = report_data['total']
    installed = report_data['installed']
    failed = report_data['failed']
    
    # Generate operator lists
    all_ops = DEMO_OPERATORS * 3  # Expand list
    random.seed(hash(report_name))  # Consistent results per report
    tested_ops = random.sample(all_ops, min(total, len(all_ops)))
    installed_ops = tested_ops[:installed]
    failed_ops = tested_ops[installed:installed+failed] if failed > 0 else []
    other_ops = tested_ops[installed+failed:]
    
    return {
        'report_name': report_name,
        'tested': len(tested_ops),
        'installed': len(installed_ops),
        'failed': len(failed_ops),
        'other': len(other_ops),
        'tested_operators': tested_ops,
        'installed_operators': installed_ops,
        'failed_operators': failed_ops,
        'other_operators': other_ops
    }

def get_demo_csv(report_name):
    """Return demo CSV data"""
    summary = get_demo_report_summary(report_name)
    lines = ['operator,status,install_time,test_result']
    for op in summary['installed_operators']:
        lines.append(f'{op},installed,45s,PASS')
    for op in summary['failed_operators']:
        lines.append(f'{op},failed,0s,FAIL')
    for op in summary['other_operators']:
        lines.append(f'{op},unknown,0s,SKIP')
    return '\n'.join(lines)

# ============== END DEMO MODE DATA ==============

def ssh_command(cmd, log_cmd=False, timeout=30):
    """Execute SSH command and return output"""
    try:
        if log_cmd:
            logger.debug(f"SSH command: {cmd[:100]}...")
        
        # Build SSH command with optional key and user
        ssh_cmd = ['ssh']
        if SSH_KEY_PATH:
            ssh_cmd.extend(['-i', SSH_KEY_PATH])
        # Suppress known_hosts warnings with LogLevel=ERROR
        ssh_cmd.extend([
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'LogLevel=ERROR'
        ])
        
        # Add user@host or just host
        if SSH_USER:
            ssh_cmd.append(f'{SSH_USER}@{REMOTE_HOST}')
        else:
            ssh_cmd.append(REMOTE_HOST)
        
        ssh_cmd.append(cmd)
        
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        # Only log real errors, not SSH warnings about known hosts
        if result.returncode != 0 and result.stderr and 'Warning:' not in result.stderr:
            logger.warning(f"SSH command failed (exit {result.returncode}): {result.stderr[:200]}")
        return result.stdout
    except subprocess.TimeoutExpired:
        logger.error(f"SSH command timed out after {timeout}s: {cmd[:100]}...")
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

def discover_catalog_indexes():
    """Discover catalog index images from the cluster's catalogsources"""
    redhat_index = REDHAT_CATALOG_INDEX
    certified_index = CERTIFIED_CATALOG_INDEX
    
    # If env vars are set, use them
    if redhat_index and certified_index:
        logger.info(f"Using catalog indexes from environment: redhat={redhat_index}, certified={certified_index}")
        return redhat_index, certified_index
    
    # Try to discover from cluster
    try:
        if not redhat_index:
            discovered = ssh_command("oc get catalogsource redhat-operators -n openshift-marketplace -o jsonpath='{.spec.image}'").strip()
            if discovered and 'registry.redhat.io' in discovered:
                redhat_index = discovered
                logger.info(f"Discovered Red Hat catalog index from cluster: {redhat_index}")
            else:
                redhat_index = DEFAULT_REDHAT_INDEX
                logger.info(f"Using default Red Hat catalog index: {redhat_index}")
        
        if not certified_index:
            discovered = ssh_command("oc get catalogsource certified-operators -n openshift-marketplace -o jsonpath='{.spec.image}'").strip()
            if discovered and 'registry.redhat.io' in discovered:
                certified_index = discovered
                logger.info(f"Discovered Certified catalog index from cluster: {certified_index}")
            else:
                certified_index = DEFAULT_CERTIFIED_INDEX
                logger.info(f"Using default Certified catalog index: {certified_index}")
    except Exception as e:
        logger.warning(f"Failed to discover catalog indexes: {e}")
        redhat_index = redhat_index or DEFAULT_REDHAT_INDEX
        certified_index = certified_index or DEFAULT_CERTIFIED_INDEX
    
    return redhat_index, certified_index

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get current test status"""
    # Return demo data if in demo mode
    if DEMO_MODE:
        return jsonify(get_demo_status())
    
    # Check if test is running (tmux session exists = test running)
    is_running = ssh_command('tmux has-session -t operator-test 2>/dev/null && echo "true" || echo "false"').strip() == 'true'
    
    # Test progress tracking
    current_op = ''
    current_state = ''
    tests_completed = 0
    tests_total = 0
    tests_remaining = 0
    report_name = ''
    start_time = ''
    
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
            
            # Extract start time from report name (report_2026-02-03_11-43-57_EST)
            # Format: report_YYYY-MM-DD_HH-MM-SS_TZ
            try:
                time_part = report_name.replace('report_', '')  # 2026-02-03_11-43-57_EST
                parts = time_part.rsplit('_', 1)  # Split off timezone ['2026-02-03_11-43-57', 'EST']
                date_time = parts[0]  # 2026-02-03_11-43-57
                date_str, time_str = date_time.split('_')  # ['2026-02-03', '11-43-57']
                time_str = time_str.replace('-', ':')  # 11:43:57
                # ISO format for JavaScript: 2026-02-03T11:43:57
                start_time = f"{date_str}T{time_str}"
            except:
                start_time = ''
            
            # Get total operators from operator-list.txt (filter empty lines)
            total_raw = ssh_command(f'grep -c "." "{latest_report_dir}/operator-list.txt" 2>/dev/null || echo 0')
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
        'start_time': start_time,
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

@app.route('/api/cluster/info')
def get_cluster_info():
    """Get comprehensive cluster information"""
    if DEMO_MODE:
        return jsonify({
            'version': '4.21.0',
            'status': 'demo',
            'user': 'demo-user',
            'api_url': 'https://api.demo-cluster.example.com:6443',
            'redhat_catalog': DEFAULT_REDHAT_INDEX,
            'certified_catalog': DEFAULT_CERTIFIED_INDEX,
            'nodes': {'total': 3, 'ready': 3, 'not_ready': 0},
            'catalog_sources': [
                {'name': 'redhat-operators', 'status': 'READY'},
                {'name': 'certified-operators', 'status': 'READY'},
                {'name': 'community-operators', 'status': 'READY'}
            ],
            'installed_operators': [
                {'namespace': 'openshift-logging', 'name': 'cluster-logging.v5.8.0', 'status': 'Succeeded'},
                {'namespace': 'openshift-operators-redhat', 'name': 'elasticsearch-operator.v5.8.0', 'status': 'Succeeded'}
            ],
            'subscriptions': [
                {'name': 'cluster-logging', 'namespace': 'openshift-logging'},
                {'name': 'elasticsearch-operator', 'namespace': 'openshift-operators-redhat'}
            ]
        })
    
    try:
        # Get cluster version
        version = ssh_command("oc get clusterversion -o jsonpath='{.items[0].status.desired.version}'").strip()
        
        # Get API URL
        api_url = ssh_command("oc whoami --show-server").strip()
        
        # Get current user
        whoami = ssh_command("oc whoami").strip()
        status = 'connected' if whoami else 'disconnected'
        
        # Get catalog indexes
        redhat_index, certified_index = discover_catalog_indexes()
        
        # Get node status
        nodes_total = safe_int(ssh_command("oc get nodes --no-headers 2>/dev/null | wc -l"))
        nodes_ready = safe_int(ssh_command("oc get nodes --no-headers 2>/dev/null | grep ' Ready' | wc -l"))
        
        # Get catalog sources
        catalog_raw = ssh_command("oc get catalogsource -n openshift-marketplace --no-headers 2>/dev/null")
        catalog_sources = []
        if catalog_raw:
            for line in catalog_raw.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 1:
                        name = parts[0]
                        status = parts[-1] if len(parts) > 1 else 'Unknown'
                        catalog_sources.append({'name': name, 'status': status})
        
        # Get installed operators (CSVs) with details
        csv_raw = ssh_command("oc get csv -A --no-headers 2>/dev/null | grep Succeeded")
        installed_operators = []
        if csv_raw:
            for line in csv_raw.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        installed_operators.append({
                            'namespace': parts[0],
                            'name': parts[1],
                            'status': 'Succeeded'
                        })
        
        # Get subscriptions
        subs_raw = ssh_command("oc get subscriptions -A --no-headers 2>/dev/null")
        subscriptions = []
        if subs_raw:
            for line in subs_raw.strip().split('\n')[:20]:  # Limit to 20
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        subscriptions.append({'namespace': parts[0], 'name': parts[1]})
        
        return jsonify({
            'version': version or 'unknown',
            'status': status,
            'user': whoami,
            'api_url': api_url,
            'redhat_catalog': redhat_index,
            'certified_catalog': certified_index,
            'nodes': {
                'total': nodes_total,
                'ready': nodes_ready,
                'not_ready': nodes_total - nodes_ready
            },
            'catalog_sources': catalog_sources,
            'installed_operators': installed_operators,
            'subscriptions': subscriptions
        })
    except Exception as e:
        logger.error(f"Cluster info error: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/api/test/config')
def get_test_config():
    """Get current test configuration"""
    # Load operator lists from environment or use defaults
    redhat_operators_env = os.environ.get('REDHAT_OPERATORS', '')
    certified_operators_env = os.environ.get('CERTIFIED_OPERATORS', '')
    
    if redhat_operators_env:
        redhat_operators = [op.strip() for op in redhat_operators_env.split(',') if op.strip()]
    else:
        # Default operator list
        redhat_operators = [
            "lvms-operator+", "odf-operator+", "ocs-operator+", "advanced-cluster-management+",
            "multicluster-engine+", "topology-aware-lifecycle-manager", "sriov-network-operator",
            "local-storage-operator", "cluster-logging", "compliance-operator", "odf-csi-addons-operator",
            "cincinnati-operator", "nfd", "ptp-operator", "rhsso-operator", "file-integrity-operator",
            "mcg-operator", "openshift-cert-manager-operator", "openshift-gitops-operator",
            "quay-operator", "servicemeshoperator3", "metallb-operator", "kubevirt-hyperconverged",
            "gatekeeper-operator-product", "ansible-automation-platform-operator", "mtc-operator",
            "redhat-oadp-operator", "openshift-pipelines-operator-rh", "kiali-ossm",
            "kubernetes-nmstate-operator", "rhacs-operator", "kernel-module-management-hub",
            "kernel-module-management", "mta-operator", "loki-operator", "amq-broker-rhel8",
            "amq-streams", "amq7-interconnect-operator", "lifecycle-agent", "numaresources-operator",
            "volsync-product", "rhbk-operator", "cluster-observability-operator",
            "openshift-custom-metrics-autoscaler-operator", "node-healthcheck-operator",
            "self-node-remediation", "tempo-product"
        ]
    
    if certified_operators_env:
        certified_operators = [op.strip() for op in certified_operators_env.split(',') if op.strip()]
    else:
        certified_operators = [
            "sriov-fec", "crunchy-postgres-operator","cloud-native-postgresql", "mongodb-enterprise", "vault-secrets-operator"
        ]
    
    # Auto-discover catalog indexes from cluster (or use env vars/defaults)
    if DEMO_MODE:
        redhat_index = DEFAULT_REDHAT_INDEX
        certified_index = DEFAULT_CERTIFIED_INDEX
    else:
        redhat_index, certified_index = discover_catalog_indexes()
    
    return jsonify({
        'catalogs': [
            {
                'name': 'Red Hat Operators',
                'index': redhat_index,
                'operators': redhat_operators
            },
            {
                'name': 'Certified Operators', 
                'index': certified_index,
                'operators': certified_operators
            }
        ]
    })

@app.route('/api/test/start', methods=['POST'])
def start_test():
    """Start test execution with optional custom configuration"""
    logger.info(">>> TEST START requested")
    
    if DEMO_MODE:
        # Reset demo test state to simulate a new test starting
        demo_test_state['running'] = True
        demo_test_state['start_time'] = datetime.now()
        demo_test_state['current_index'] = 0
        logger.info("Demo mode: Simulated test start")
        return jsonify({'status': 'Test started (demo mode)', 'message': 'Demo test simulation started'})
    
    # Check if test is already running (tmux session exists)
    is_running = ssh_command('tmux has-session -t operator-test 2>/dev/null && echo "true" || echo "false"').strip() == 'true'
    if is_running:
        logger.warning("Test start rejected - test already running")
        return jsonify({'error': 'Test already running'}), 400
    
    # Run pre-test setup: disable default catalogs
    disable_catalog_script = os.environ.get('DISABLE_CATALOG_SCRIPT', '/root/test-rose/kcli-platform/disable-catalog.sh')
    logger.info(f"Running pre-test setup: {disable_catalog_script}")
    disable_result = ssh_command(f'bash {disable_catalog_script} 2>&1')
    logger.info(f"Disable catalog result: {disable_result[:200] if disable_result else 'OK'}")
    
    # Get custom configuration if provided
    data = request.get_json() or {}
    
    if 'catalogs' in data and data['catalogs']:
        # Build custom test script
        commands = ['#!/bin/bash', 'set -e']  # Add shebang and exit on error
        for catalog in data['catalogs']:
            if catalog.get('operators'):
                operators_str = ' '.join(catalog['operators'])
                index = catalog.get('index', 'registry.redhat.io/redhat/redhat-operator-index:v4.20')
                # Quotes are preserved by heredoc
                commands.append(f'time ./script/run-basic-batch-operators-test.sh {index} "{operators_str}"')
        
        if len(commands) > 2:  # More than just shebang and set -e
            # Create a temporary test script using heredoc to preserve quotes
            script_lines = '\n'.join(commands)
            create_script_cmd = f'''cat > {REMOTE_BASE_DIR}/run-custom-test.sh << 'EOFSCRIPT'
{script_lines}
EOFSCRIPT
chmod +x {REMOTE_BASE_DIR}/run-custom-test.sh'''
            ssh_command(create_script_cmd)
            ssh_command(f'tmux new-session -d -s operator-test "export KUBECONFIG={KUBECONFIG_PATH} && cd {REMOTE_BASE_DIR} && ./run-custom-test.sh"')
            logger.info(f"Custom test started with {len(commands) - 2} catalog(s)")
        else:
            return jsonify({'error': 'No operators specified'}), 400
    else:
        # Use default test script
        ssh_command(f'tmux new-session -d -s operator-test "export KUBECONFIG={KUBECONFIG_PATH} && cd {REMOTE_BASE_DIR} && ./run-ocp-4.20-test-v2.sh"')
        logger.info("Default test started")
    
    return jsonify({'status': 'Test started', 'timestamp': datetime.now().isoformat()})

@app.route('/api/test/stop', methods=['POST'])
def stop_test():
    """Stop test execution"""
    logger.info(">>> TEST STOP requested")
    
    if DEMO_MODE:
        demo_test_state['running'] = False
        logger.info("Demo mode: Simulated test stop")
        return jsonify({'status': 'Test stopped (demo mode)'})
    
    # Kill the tmux session to stop the test
    ssh_command('tmux kill-session -t operator-test 2>/dev/null')
    logger.info("Test stopped (killed tmux session)")
    return jsonify({'status': 'Test stopped'})

@app.route('/api/cleanup', methods=['POST'])
def cleanup_cluster():
    """Clean cluster"""
    logger.info(">>> CLEANUP requested")
    
    if DEMO_MODE:
        logger.info("Demo mode: Simulated cleanup")
        return jsonify({'status': 'Cleanup completed (demo mode)'})
    logger.info("Starting cluster cleanup...")
    output = ssh_command('bash /tmp/cleanup-all-test-operators-v2.sh')
    logger.info("Cleanup completed")
    return jsonify({'status': 'Cleanup complete', 'output': output})

@app.route('/api/live-output')
def get_live_output():
    """Get live test output - capture full scrollback buffer"""
    if DEMO_MODE:
        return jsonify({'output': get_demo_live_output()})
    
    # Use -S - to capture entire scrollback history, then get last 200 lines
    output = ssh_command('tmux capture-pane -t operator-test -p -S - 2>/dev/null | tail -200').strip()
    return jsonify({'output': output})

@app.route('/api/completed-tests')
def get_completed_tests():
    """Get list of completed tests with status"""
    # Get latest report directory
    latest_report_dir = ssh_command(f'ls -td {REPORT_DIR}/report_* 2>/dev/null | head -1').strip()
    
    if not latest_report_dir:
        return jsonify({'error': 'No reports found', 'tests': []})
    
    report_name = os.path.basename(latest_report_dir)
    
    # Get list of completed operator folders
    folders_raw = ssh_command(f'ls -d "{latest_report_dir}"/*/ 2>/dev/null | xargs -I {{}} basename {{}}')
    completed_operators = [f.strip() for f in folders_raw.strip().split('\n') if f.strip()]
    
    # Get pass/fail status from log file
    log_file = ssh_command(f'ls -t "{latest_report_dir}"/output_*.log 2>/dev/null | head -1').strip()
    
    status_map = {}
    if log_file:
        # Get installed operators (success)
        installed_raw = ssh_command(f'grep "operator .* installed" "{log_file}" 2>/dev/null | sed "s/operator \\(.*\\) installed/\\1/"')
        for op in installed_raw.strip().split('\n'):
            op = op.strip()
            if op:
                status_map[op] = 'passed'
        
        # Get failed operators
        failed_raw = ssh_command(f'grep "Operator failed to install" "{log_file}" 2>/dev/null')
        # Parse context to find which operator failed
        failed_context = ssh_command(f'grep -B5 "Operator failed to install" "{log_file}" 2>/dev/null | grep "package=" | sed "s/.*package= \\([^ ]*\\).*/\\1/"')
        for op in failed_context.strip().split('\n'):
            op = op.strip()
            if op:
                status_map[op] = 'failed'
    
    # Build test list with status
    tests = []
    for op in completed_operators:
        tests.append({
            'name': op,
            'status': status_map.get(op, 'completed')
        })
    
    # Sort: failed first, then by name
    tests.sort(key=lambda x: (0 if x['status'] == 'failed' else 1, x['name']))
    
    return jsonify({
        'report': report_name,
        'tests': tests,
        'total': len(tests),
        'passed': sum(1 for t in tests if t['status'] == 'passed'),
        'failed': sum(1 for t in tests if t['status'] == 'failed')
    })

@app.route('/api/reports')
def list_reports():
    """List available report directories with summary stats"""
    # Default to 10 reports, can be overridden with ?limit=N parameter
    limit = request.args.get('limit', 10, type=int)
    limit = min(max(limit, 1), 50)  # Clamp between 1 and 50
    
    if DEMO_MODE:
        return jsonify({'reports': get_demo_reports(limit)})
    
    reports_raw = ssh_command(f'ls -td {REPORT_DIR}/report_* 2>/dev/null | head -{limit}')
    report_names = [os.path.basename(r) for r in reports_raw.strip().split('\n') if r]
    
    # Build report list with summary stats
    reports = []
    for report_name in report_names:
        report_dir = f"{REPORT_DIR}/{report_name}"
        
        # Get total tested operators by counting subdirectories (matches View modal)
        # This counts operators that actually ran, not just planned
        total_raw = ssh_command(f'find "{report_dir}" -maxdepth 1 -type d | wc -l')
        total = max(0, safe_int(total_raw) - 1)  # Subtract 1 for parent dir
        
        # Get installed count from log
        log_file = ssh_command(f'ls -t "{report_dir}"/output_*.log 2>/dev/null | head -1').strip()
        installed = 0
        failed = 0
        
        if log_file:
            installed_raw = ssh_command(f'grep -c "operator .* installed" "{log_file}" 2>/dev/null || echo 0')
            installed = safe_int(installed_raw)
            
            failed_raw = ssh_command(f'grep -c "Operator failed to install" "{log_file}" 2>/dev/null || echo 0')
            failed = safe_int(failed_raw)
        
        reports.append({
            'name': report_name,
            'total': total,
            'installed': installed,
            'failed': failed
        })
    
    return jsonify({'reports': reports})

@app.route('/api/report-summary')
def get_report_summary():
    """Get summary stats for a specific report"""
    report_name = request.args.get('report', None)
    
    if not report_name:
        return jsonify({'error': 'Report name required'}), 400
    
    if DEMO_MODE:
        return jsonify(get_demo_report_summary(report_name))
    
    report_dir = f"{REPORT_DIR}/{report_name}"
    
    # Check if report exists
    exists = ssh_command(f'test -d "{report_dir}" && echo "yes" || echo "no"').strip()
    if exists != 'yes':
        return jsonify({'error': 'Report not found'}), 404
    
    # Get list of completed operator folders (operators that have been tested)
    folders_raw = ssh_command(f'ls -d "{report_dir}"/*/ 2>/dev/null | xargs -I {{}} basename {{}}')
    tested_operators = set(f.strip() for f in folders_raw.strip().split('\n') if f.strip())
    
    # Get pass/fail status from log file
    log_file = ssh_command(f'ls -t "{report_dir}"/output_*.log 2>/dev/null | head -1').strip()
    
    installed_list = []
    failed_list = []
    
    if log_file:
        # Get installed operators (success) - "operator X installed"
        installed_raw = ssh_command(f'grep "operator .* installed" "{log_file}" 2>/dev/null | sed "s/operator \\(.*\\) installed/\\1/"')
        for op in installed_raw.strip().split('\n'):
            op = op.strip()
            if op:
                installed_list.append(op)
        
        # Get failed operators - "Operator failed to install"
        failed_context = ssh_command(f'grep -B5 "Operator failed to install" "{log_file}" 2>/dev/null | grep "package=" | sed "s/.*package= \\([^ ]*\\).*/\\1/"')
        for op in failed_context.strip().split('\n'):
            op = op.strip()
            if op:
                failed_list.append(op)
    
    # Make lists unique
    installed_list = sorted(set(installed_list))
    failed_list = sorted(set(failed_list))
    
    # Find operators that are in tested but not in installed or failed (in progress or other)
    installed_set = set(installed_list)
    failed_set = set(failed_list)
    other_list = sorted(tested_operators - installed_set - failed_set)
    
    # Parse date/time from report name
    try:
        time_part = report_name.replace('report_', '')
        parts = time_part.rsplit('_', 1)
        date_str, time_str = parts[0].split('_')
        time_str = time_str.replace('-', ':')
        tz = parts[1] if len(parts) > 1 else ''
    except:
        date_str = ''
        time_str = ''
        tz = ''
    
    return jsonify({
        'report': report_name,
        'date': date_str,
        'time': time_str,
        'timezone': tz,
        'tested': len(tested_operators),
        'installed': len(installed_list),
        'failed': len(failed_list),
        'other': len(other_list),
        'tested_list': sorted(tested_operators),
        'installed_list': installed_list,
        'failed_list': failed_list,
        'other_list': other_list,
        'url': f'http://10.1.24.2/{report_name}/'
    })

@app.route('/api/download/csv')
def download_csv():
    """Download results.csv from the latest or specified report"""
    report_name = request.args.get('report', None)
    
    if DEMO_MODE:
        if not report_name:
            report_name = DEMO_REPORTS[0]['name']
        csv_content = get_demo_csv(report_name)
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={report_name}_results.csv'}
        )
    
    # Get the report directory
    if report_name:
        report_dir = f"{REPORT_DIR}/{report_name}"
    else:
        # Get latest report
        report_dir = ssh_command(f'ls -td {REPORT_DIR}/report_* 2>/dev/null | head -1').strip()
    
    if not report_dir:
        return jsonify({'error': 'No reports found'}), 404
    
    report_name = os.path.basename(report_dir)
    csv_path = f"{report_dir}/results.csv"
    
    logger.info(f">>> CSV DOWNLOAD requested: {csv_path}")
    
    # Check if file exists
    exists = ssh_command(f'test -f "{csv_path}" && echo "yes" || echo "no"').strip()
    if exists != 'yes':
        return jsonify({'error': 'CSV file not found'}), 404
    
    # Fetch the CSV content (longer timeout for large files)
    csv_content = ssh_command(f'cat "{csv_path}"', log_cmd=False, timeout=120)
    
    if csv_content.startswith('Error:'):
        return jsonify({'error': csv_content}), 500
    
    logger.info(f"CSV download complete: {len(csv_content)} bytes")
    
    # Return as downloadable file
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=results_{report_name}.csv'}
    )

@app.route('/api/download/csv/combined')
def download_combined_csv():
    """Download combined results.csv from multiple reports"""
    # Get list of reports to combine (comma-separated) or default to latest 5
    reports_param = request.args.get('reports', None)
    
    if DEMO_MODE:
        if reports_param:
            report_names = reports_param.split(',')
        else:
            report_names = [DEMO_REPORTS[0]['name']]
        
        combined_csv = []
        header_added = False
        for rn in report_names:
            csv_content = get_demo_csv(rn)
            lines = csv_content.split('\n')
            if not header_added:
                combined_csv.extend(lines)
                header_added = True
            else:
                combined_csv.extend(lines[1:])  # Skip header
        
        return Response(
            '\n'.join(combined_csv),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=combined_results.csv'}
        )
    
    if reports_param:
        report_names = reports_param.split(',')
    else:
        # Get latest report only by default
        latest = ssh_command(f'ls -td {REPORT_DIR}/report_* 2>/dev/null | head -1').strip()
        report_names = [os.path.basename(latest)] if latest else []
    
    if not report_names:
        return jsonify({'error': 'No reports found'}), 404
    
    logger.info(f">>> COMBINED CSV DOWNLOAD requested: {report_names}")
    
    combined_csv = []
    header_added = False
    
    for report_name in report_names:
        csv_path = f"{REPORT_DIR}/{report_name}/results.csv"
        exists = ssh_command(f'test -f "{csv_path}" && echo "yes" || echo "no"').strip()
        
        if exists == 'yes':
            content = ssh_command(f'cat "{csv_path}"', log_cmd=False, timeout=120)
            lines = content.strip().split('\n')
            
            if lines:
                if not header_added:
                    # Add header from first file
                    combined_csv.append(lines[0])
                    header_added = True
                # Add data rows (skip header in subsequent files)
                combined_csv.extend(lines[1:] if header_added else lines)
    
    if not combined_csv:
        return jsonify({'error': 'No CSV data found'}), 404
    
    combined_content = '\n'.join(combined_csv)
    logger.info(f"Combined CSV download complete: {len(combined_content)} bytes from {len(report_names)} reports")
    
    return Response(
        combined_content,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=combined_results.csv'}
    )

if __name__ == '__main__':
    debug_mode = os.environ.get('DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=DASHBOARD_PORT, debug=debug_mode)
