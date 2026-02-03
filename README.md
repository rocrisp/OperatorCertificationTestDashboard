# Operator Certification Test Dashboard

**Version:** 1.0
**Created:** February 3, 2026
**Purpose:** Comprehensive dashboard for running and monitoring OpenShift operator certification tests

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [macOS Quick Start](#-macos-quick-start)
3. [Directory Structure](#directory-structure)
4. [Installation](#installation)
5. [Dashboard Options](#dashboard-options)
6. [Quick Start](#quick-start)
7. [Features](#features)
8. [Usage Guide](#usage-guide)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Configuration](#advanced-configuration)

---

## 🎯 Overview

This dashboard provides a unified interface for managing operator certification tests on OpenShift clusters. It consolidates all the tools, scripts, and documentation created during the testing process.

### Key Capabilities

- ✅ **Pre-Flight Validation** - Ensure cluster is ready for testing
- ✅ **One-Click Cleanup** - Remove all test operators and resources
- ✅ **Test Execution** - Start and monitor full test suite
- ✅ **Live Monitoring** - Real-time progress tracking
- ✅ **Results Analysis** - Comprehensive test results and comparisons
- ✅ **Quick Fixes** - Manual interventions for common issues
- ✅ **Script Management** - Sync and update remote scripts

---

## 🍎 macOS Quick Start

Get the web dashboard running in under 2 minutes:

```bash
# 1. Clone the repository (if you haven't already)
git clone https://github.com/rocrisp/OperatorCertificationTestDashboard.git
cd OperatorCertificationTestDashboard

# 2. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the web dashboard
./scripts/web-dashboard.py

# 5. Open in browser
# Navigate to: http://localhost:5001
```

**Note:** On macOS, you must use a virtual environment because the system Python is externally managed. Each time you open a new terminal, activate the venv first:
```bash
cd ~/OperatorCertificationTestDashboard
source venv/bin/activate
./scripts/web-dashboard.py
```

---

## 📁 Directory Structure

```
~/operator-test-dashboard/
├── scripts/               # All executable scripts
│   ├── dashboard.sh      # Main CLI dashboard
│   ├── web-dashboard.py  # Web-based dashboard (Python/Flask)
│   ├── cleanup-all-test-operators-v2.sh
│   ├── pre-flight-checks.sh
│   ├── live-monitor.sh
│   ├── run-basic-batch-operators-test.sh
│   └── run-ocp-4.20-test-v2.sh
├── docs/                  # Documentation and analysis
│   ├── test-run-*.md     # Test run summaries
│   ├── *-failure-*.md    # Failure analyses
│   └── implementation-*.md
├── config/                # Configuration files
│   └── dashboard.conf    # Main configuration
├── results/               # Test results (downloaded logs)
├── backups/               # Script backups
└── README.md             # This file
```

---

## 🚀 Installation

### Prerequisites

- macOS or Linux workstation
- SSH access to remote OpenShift cluster (configured as 'rdu2')
- SSH key authentication set up
- `oc` CLI tool installed locally (optional, for local operations)

### Setup Steps

```bash
# 1. Navigate to dashboard directory
cd ~/operator-test-dashboard

# 2. Make all scripts executable
chmod +x scripts/*.sh scripts/*.py 2>/dev/null

# 3. Install Python dependencies (for web dashboard)
pip3 install flask paramiko

# 4. Configure remote connection
# Edit config/dashboard.conf if your remote host is not 'rdu2'
vi config/dashboard.conf

# 5. Test connection
ssh rdu2 'echo "Connection successful"'

# 6. Sync initial scripts to remote
./scripts/dashboard.sh  # Choose option [9] to sync scripts
```

---

## 🎨 Dashboard Options

### Option 1: CLI Dashboard (Recommended for Terminal Users)

**Best For:**
- Terminal/CLI enthusiasts
- Automation and scripting
- Remote SSH sessions
- Low bandwidth connections

**Features:**
- Text-based menu interface
- Real-time status updates
- Direct terminal output
- No additional dependencies

**Launch:**
```bash
cd ~/operator-test-dashboard
./scripts/dashboard.sh
```

### Option 2: Web Dashboard (Recommended for GUI Users)

**Best For:**
- GUI preference
- Multiple simultaneous users
- Remote access from any device
- Modern browser experience

**Features:**
- Browser-based interface
- REST API endpoints
- Real-time updates (AJAX)
- Responsive design

**Launch:**
```bash
cd ~/operator-test-dashboard
./scripts/web-dashboard.py
# Open browser to: http://localhost:5000
```

### Option 3: Hybrid Approach

Use both dashboards:
- CLI for quick operations
- Web dashboard for monitoring and visualization

---

## 🏃 Quick Start

### Running Your First Test

```bash
# 1. Launch CLI dashboard
cd ~/operator-test-dashboard
./scripts/dashboard.sh

# 2. Run pre-flight checks
# Select: [1] Pre-Flight Checks

# 3. Clean cluster (if needed)
# Select: [2] Clean Cluster

# 4. Start test
# Select: [3] Start Test

# 5. Monitor progress
# Select: [4] Monitor Test
# (or press Ctrl+C and let it run in background)

# 6. View results (after ~3 hours)
# Select: [5] View Test Results
```

---

## ✨ Features

### 1. Pre-Flight Checks

**Purpose:** Validate cluster state before testing

**Checks Include:**
- Cluster connectivity
- Leftover catalog sources
- Test namespaces status
- Required operators presence
- Unexpected operators
- Node health
- Failed/pending pods
- OLM health
- Disk space
- Running test processes
- **Stale webhooks** (NEW!)

**Usage:**
```bash
# CLI Dashboard: Option [1]
# Manual: ssh rdu2 'bash /tmp/pre-flight-checks.sh'
```

### 2. Cluster Cleanup

**Purpose:** Remove all test operators and resources

**Deletes:**
- All subscriptions in test namespaces
- All CSVs (except system operators)
- Failed InstallPlans
- **Webhook configurations** (NEW!)
- Test namespaces
- Catalogsources

**Safety Features:**
- Confirmation prompt
- Backup suggestions
- Force-delete for stuck resources
- Comprehensive logging

**Usage:**
```bash
# CLI Dashboard: Option [2]
# Manual: ssh rdu2 'bash /tmp/cleanup-all-test-operators-v2.sh'
```

### 3. Test Execution

**Purpose:** Run full operator certification test suite

**Features:**
- Automatic pre-flight checks
- Tmux session management
- Progress tracking
- Error recovery
- Result archiving

**Test Suite:**
- 52 operators total
- ~3 hour execution time
- Automatic CSV labeling
- Isolated testing

**Usage:**
```bash
# CLI Dashboard: Option [3]
# Manual: ssh rdu2 'cd /root/test-rose/certsuite && ./run-ocp-4.20-test-v2.sh'
```

### 4. Live Monitoring

**Purpose:** Real-time test progress tracking

**Displays:**
- Current operator being tested
- Recent log output
- Elapsed time
- Estimated completion

**Refresh:** Every 30 seconds (configurable)

**Usage:**
```bash
# CLI Dashboard: Option [4]
# Manual: ssh rdu2 'bash /tmp/live-monitor.sh'
```

### 5. Results Analysis

**Purpose:** Comprehensive test results and comparison

**Provides:**
- Success/failure counts
- Success rate percentage
- Failed operator list
- Historical comparison
- Downloadable logs

**Usage:**
```bash
# CLI Dashboard: Option [5]
```

### 6. Quick Fixes

**Purpose:** Manual interventions for common issues

**Available Fixes:**
1. Delete stale webhooks
2. Approve pending InstallPlans
3. Delete failed InstallPlans
4. Restart catalog pod
5. Check operator logs

**Usage:**
```bash
# CLI Dashboard: Option [8]
```

### 7. Script Synchronization

**Purpose:** Update remote scripts from local versions

**Syncs:**
- Cleanup script (v2)
- Pre-flight checks
- Monitoring scripts
- Test runner (if modified)

**Usage:**
```bash
# CLI Dashboard: Option [9]
```

---

## 📖 Usage Guide

### Typical Test Workflow

```
1. Pre-Flight Checks
   ↓
2. Clean Cluster (if needed)
   ↓
3. Start Test
   ↓
4. Monitor Progress (optional)
   ↓
5. Wait ~3 hours
   ↓
6. View Results
   ↓
7. Analyze Failures (if any)
   ↓
8. Apply Fixes (if needed)
   ↓
9. Re-test Failed Operators
```

### Best Practices

**Before Testing:**
1. ✅ Always run pre-flight checks
2. ✅ Clean cluster for consistent results
3. ✅ Verify no stale webhooks
4. ✅ Check available disk space
5. ✅ Note start time for tracking

**During Testing:**
1. ✅ Don't interrupt tmux session
2. ✅ Monitor periodically (not constantly)
3. ✅ Keep SSH connection stable
4. ✅ Don't manually modify operators

**After Testing:**
1. ✅ Download logs locally
2. ✅ Document results
3. ✅ Compare with previous runs
4. ✅ Identify failure patterns
5. ✅ Clean cluster before next test

### Common Operations

**Check Test Status:**
```bash
ssh rdu2 'tmux has-session -t operator-test 2>/dev/null && echo "Running" || echo "Not running"'
```

**View Live Output:**
```bash
ssh rdu2 'tmux capture-pane -t operator-test -p | tail -30'
```

**Attach to Test Session:**
```bash
ssh rdu2 'tmux attach -t operator-test'
# Press Ctrl+B then D to detach
```

**Stop Test:**
```bash
ssh rdu2 'tmux kill-session -t operator-test'
```

**Download Latest Results:**
```bash
latest=$(ssh rdu2 'ls -t /root/test-rose/certsuite/test-run-*.log | head -1')
scp rdu2:$latest ~/operator-test-dashboard/results/
```

---

## 🔧 Troubleshooting

### Issue: Test Fails on First Operators

**Symptom:** lvms-operator, odf-operator, ocs-operator fail immediately

**Cause:** Stale webhook configuration (`csv.odf.openshift.io`)

**Solution:**
```bash
# Option 1: Use dashboard Quick Fix [8.1]
# Option 2: Manual fix
ssh rdu2 'oc delete mutatingwebhookconfiguration csv.odf.openshift.io'
ssh rdu2 'oc delete installplan --all -n openshift-storage'
```

### Issue: CSVs Not Appearing

**Symptom:** "Waiting for csv..." repeating

**Possible Causes:**
1. InstallPlan not approved (approval: Manual)
2. Webhook blocking CSV creation
3. OLM issues

**Solution:**
```bash
# Check InstallPlans
ssh rdu2 'oc get installplan -n openshift-storage'

# Approve if needed
ssh rdu2 'for plan in $(oc get installplan -n openshift-storage -o name); do
  oc patch $plan -n openshift-storage --type merge -p "{\"spec\":{\"approved\":true}}";
done'
```

### Issue: Test Hangs/Doesn't Progress

**Symptom:** Same operator for > 15 minutes

**Solution:**
```bash
# Check if tmux session is still active
ssh rdu2 'tmux has-session -t operator-test && echo "Running" || echo "Stopped"'

# View current output
ssh rdu2 'tmux capture-pane -t operator-test -p | tail -50'

# If truly hung, restart
ssh rdu2 'tmux kill-session -t operator-test'
# Then restart via dashboard
```

### Issue: SSH Connection Drops

**Symptom:** Cannot connect to rdu2

**Solution:**
```bash
# Re-add SSH key
expect << 'EOF'
spawn ssh-add ~/.ssh/cnfcert
expect "Enter passphrase"
send "unix1234\r"
expect eof
EOF

# Test connection
ssh rdu2 'echo "Connected"'
```

### Issue: Cleanup Script Fails

**Symptom:** Resources not deleting

**Solution:**
```bash
# Force delete stuck resources
ssh rdu2 'oc patch csv <csv-name> -n openshift-storage -p "{\"metadata\":{\"finalizers\":null}}" --type=merge'
ssh rdu2 'oc delete csv <csv-name> -n openshift-storage --force --grace-period=0'
```

---

## ⚙️ Advanced Configuration

### Customizing Test List

**Edit:** `~/operator-test-dashboard/scripts/run-ocp-4.20-test-v2.sh`

```bash
# Remove operators by deleting from list
# Example: Remove jaeger, cloud-native-postgresql

time ./script/run-basic-batch-operators-test.sh \
  registry.redhat.io/redhat/redhat-operator-index:v4.20 \
  "lvms-operator+ odf-operator+ ... tempo-product"
  # Note: jaeger removed

time ./script/run-basic-batch-operators-test.sh \
  registry.redhat.io/redhat/certified-operator-index:v4.20 \
  "sriov-fec mongodb-enterprise vault-secrets-operator"
  # Note: cloud-native-postgresql removed
```

### Adding Custom Operators

```bash
# Add to appropriate catalog test
# Use + suffix for persistent operators
# Use - suffix for test namespace
```

### Adjusting Timeouts

**Edit:** `~/operator-test-dashboard/scripts/run-basic-batch-operators-test.sh`

**Line 322:** CSV timeout
```bash
timeout_seconds=100  # Increase for slower operators
```

**Line 248:** Package manifest timeout
```bash
timeout_seconds=600  # Increase for slow catalog
```

### Remote Host Configuration

**Edit:** `~/operator-test-dashboard/config/dashboard.conf`

```bash
REMOTE_HOST=your-cluster-hostname
REMOTE_USER=your-username
REMOTE_BASE_DIR=/path/to/certsuite
```

### Notification Configuration (Future)

```bash
# Edit config/dashboard.conf
ENABLE_NOTIFICATIONS=true
NOTIFICATION_EMAIL=your-email@example.com
NOTIFICATION_SLACK_WEBHOOK=https://hooks.slack.com/...
```

---

## 📊 Dashboard Recommendations

Based on your usage patterns and requirements, here are recommendations for the ideal dashboard setup:

### Recommended Setup: Hybrid CLI + Web

**Primary Interface:** CLI Dashboard (`dashboard.sh`)
- Use for starting tests
- Use for cleanup operations
- Use for quick status checks

**Secondary Interface:** Web Dashboard (`web-dashboard.py`)
- Use for monitoring long-running tests
- Use for results analysis
- Use for sharing status with team

### Workflow Automation

```bash
#!/bin/bash
# Example: Automated daily test script
cd ~/operator-test-dashboard

# 1. Pre-flight check
./scripts/dashboard.sh --non-interactive --preflight || exit 1

# 2. Clean cluster
./scripts/dashboard.sh --non-interactive --cleanup

# 3. Start test
./scripts/dashboard.sh --non-interactive --start-test

# 4. Send notification when complete (future)
# wait_for_test_completion && send_notification
```

### Future Enhancements

**Planned Features:**
1. Email/Slack notifications
2. Historical trending graphs
3. Operator-specific deep dive
4. Automated failure analysis
5. Jenkins/CI integration
6. Multi-cluster support
7. Result export (CSV, JSON)
8. Comparison reports

---

## 📝 Change Log

### Version 1.0 (Feb 3, 2026)
- Initial dashboard release
- CLI interface
- Web dashboard (basic)
- All core scripts integrated
- Webhook cleanup support
- Comprehensive documentation

---

## 🤝 Contributing

To add new features or scripts:

1. Add script to `~/operator-test-dashboard/scripts/`
2. Update `dashboard.sh` menu if needed
3. Update this README
4. Test thoroughly
5. Document changes

---

## 📞 Support

**Documentation Location:** `~/operator-test-dashboard/docs/`

**Key Documents:**
- `test-failure-webhook-issue-resolved.md` - Webhook issue fix
- `registry-credentials-and-operator-history.md` - Operator analysis
- `script-modification-skip-duplicate-subscription.md` - Script fixes

**Command Reference:**
```bash
# View all documentation
ls ~/operator-test-dashboard/docs/

# Search documentation
grep -r "keyword" ~/operator-test-dashboard/docs/
```

---

## 📄 License

Internal use only - Red Hat CNF Certification Team

---

**Last Updated:** February 3, 2026
**Maintainer:** CNF Cert Team
**Version:** 1.0
