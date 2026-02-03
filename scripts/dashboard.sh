#!/bin/bash

# Operator Test Dashboard - Main Interface
# Version: 1.0
# Date: February 3, 2026

set -e

# Configuration
REMOTE_HOST="${REMOTE_HOST:-rdu2}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_BASE_DIR="${REMOTE_BASE_DIR:-/root/test-rose/certsuite}"
LOCAL_BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Header
show_header() {
    clear
    echo -e "${BOLD}${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║        OPERATOR CERTIFICATION TEST DASHBOARD v1.0             ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${YELLOW}Remote Cluster:${NC} $REMOTE_HOST"
    echo -e "${YELLOW}Test Directory:${NC} $REMOTE_BASE_DIR"
    echo ""
}

# Check connection
check_connection() {
    if ssh -o ConnectTimeout=5 $REMOTE_HOST "echo 'connected' 2>/dev/null" | grep -q "connected"; then
        echo -e "${GREEN}✓${NC} Connected to $REMOTE_HOST"
        return 0
    else
        echo -e "${RED}✗${NC} Cannot connect to $REMOTE_HOST"
        return 1
    fi
}

# Get cluster info
get_cluster_info() {
    echo -e "\n${BOLD}Cluster Information:${NC}"
    ssh $REMOTE_HOST "oc version --short 2>/dev/null | head -2" || echo "Cannot get cluster info"
    echo ""
}

# Get test status
get_test_status() {
    if ssh $REMOTE_HOST "tmux has-session -t operator-test 2>/dev/null"; then
        echo -e "${GREEN}● Test is RUNNING${NC}"
        
        # Get current operator
        current_op=$(ssh $REMOTE_HOST "tmux capture-pane -t operator-test -p 2>/dev/null | grep '^\*\*\*\*\*\*\*\*\*' | tail -1 | awk -F'package= ' '{print \$2}' | awk '{print \$1}'")
        if [ -n "$current_op" ]; then
            echo -e "  ${YELLOW}Current operator:${NC} $current_op"
        fi
    else
        echo -e "${YELLOW}○ No test running${NC}"
    fi
}

# Get operator counts
get_operator_counts() {
    echo -e "\n${BOLD}Operator Status:${NC}"
    csvs=$(ssh $REMOTE_HOST "oc get csv -A --no-headers 2>/dev/null | grep -v packageserver | wc -l")
    subs=$(ssh $REMOTE_HOST "oc get subscription -A --no-headers 2>/dev/null | wc -l")
    webhooks=$(ssh $REMOTE_HOST "oc get mutatingwebhookconfigurations 2>/dev/null | grep -cE 'operator|odf|ocs|lvms' || echo 0")
    
    echo -e "  CSVs installed: ${GREEN}$csvs${NC}"
    echo -e "  Subscriptions: ${GREEN}$subs${NC}"
    echo -e "  Operator webhooks: ${GREEN}$webhooks${NC}"
}

# Main menu
show_menu() {
    show_header
    
    # Connection status
    if check_connection; then
        get_cluster_info
        get_test_status
        get_operator_counts
    fi
    
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}MAIN MENU${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}[1]${NC} Pre-Flight Checks - Validate cluster before testing"
    echo -e "${GREEN}[2]${NC} Clean Cluster - Remove all test operators"
    echo -e "${GREEN}[3]${NC} Start Test - Run full operator test suite"
    echo -e "${GREEN}[4]${NC} Monitor Test - Live progress monitoring"
    echo ""
    echo -e "${BLUE}[5]${NC} View Test Results - Analyze completed tests"
    echo -e "${BLUE}[6]${NC} Compare Results - Historical comparison"
    echo -e "${BLUE}[7]${NC} Operator Status - Check specific operators"
    echo ""
    echo -e "${YELLOW}[8]${NC} Quick Fixes - Manual interventions"
    echo -e "${YELLOW}[9]${NC} Sync Scripts - Update remote scripts"
    echo ""
    echo -e "${MAGENTA}[A]${NC} Advanced Options"
    echo -e "${MAGENTA}[C]${NC} Configuration"
    echo ""
    echo -e "${RED}[Q]${NC} Quit"
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Pre-flight checks
preflight_checks() {
    show_header
    echo -e "${BOLD}${BLUE}Running Pre-Flight Checks...${NC}\n"
    
    ssh $REMOTE_HOST "bash /tmp/pre-flight-checks.sh" || {
        echo -e "\n${RED}Pre-flight checks failed. Fix issues before testing.${NC}"
        read -p "Press Enter to continue..."
        return 1
    }
    
    echo -e "\n${GREEN}✓ All pre-flight checks passed!${NC}"
    read -p "Press Enter to continue..."
}

# Clean cluster
clean_cluster() {
    show_header
    echo -e "${BOLD}${YELLOW}⚠ WARNING: This will delete ALL test operators${NC}\n"
    echo "This includes:"
    echo "  - All subscriptions"
    echo "  - All CSVs"
    echo "  - All InstallPlans"
    echo "  - Webhook configurations"
    echo "  - Test namespaces"
    echo ""
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled."
        read -p "Press Enter to continue..."
        return
    fi
    
    echo -e "\n${BOLD}${BLUE}Cleaning cluster...${NC}\n"
    ssh $REMOTE_HOST "bash /tmp/cleanup-all-test-operators-v2.sh"
    
    echo -e "\n${GREEN}✓ Cluster cleanup complete!${NC}"
    read -p "Press Enter to continue..."
}

# Start test
start_test() {
    show_header
    echo -e "${BOLD}${BLUE}Starting Operator Test Suite${NC}\n"
    
    # Check if test already running
    if ssh $REMOTE_HOST "tmux has-session -t operator-test 2>/dev/null"; then
        echo -e "${RED}✗ Test is already running!${NC}"
        echo ""
        read -p "Kill existing test and restart? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            ssh $REMOTE_HOST "tmux kill-session -t operator-test"
            echo "Existing test killed."
        else
            read -p "Press Enter to continue..."
            return
        fi
    fi
    
    # Run pre-flight checks
    echo -e "${YELLOW}Running pre-flight checks...${NC}"
    if ! ssh $REMOTE_HOST "bash /tmp/pre-flight-checks.sh 2>&1 | tail -3"; then
        echo -e "\n${RED}Pre-flight checks failed!${NC}"
        read -p "Continue anyway? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            read -p "Press Enter to continue..."
            return
        fi
    fi
    
    # Start test
    echo -e "\n${GREEN}Starting test in tmux session 'operator-test'...${NC}"
    ssh $REMOTE_HOST "tmux new-session -d -s operator-test 'cd $REMOTE_BASE_DIR && ./run-ocp-4.20-test-v2.sh'"
    
    sleep 5
    
    echo -e "\n${GREEN}✓ Test started successfully!${NC}"
    echo ""
    echo "Start time: $(date)"
    echo "Estimated duration: ~3 hours"
    echo ""
    read -p "Open live monitor now? (yes/no): " monitor
    if [ "$monitor" = "yes" ]; then
        monitor_test
    else
        read -p "Press Enter to continue..."
    fi
}

# Monitor test
monitor_test() {
    show_header
    echo -e "${BOLD}${BLUE}Live Test Monitor${NC}\n"
    echo "Press Ctrl+C to exit monitor and return to menu"
    echo ""
    sleep 2
    
    ssh $REMOTE_HOST "bash /tmp/live-monitor.sh" || true
}

# View results
view_results() {
    show_header
    echo -e "${BOLD}${BLUE}Test Results${NC}\n"
    
    # Find latest test log
    latest_log=$(ssh $REMOTE_HOST "ls -t $REMOTE_BASE_DIR/test-run-*.log 2>/dev/null | head -1")
    
    if [ -z "$latest_log" ]; then
        echo -e "${RED}No test logs found${NC}"
        read -p "Press Enter to continue..."
        return
    fi
    
    echo -e "${YELLOW}Latest test log:${NC} $latest_log"
    echo ""
    
    # Count results
    total=$(ssh $REMOTE_HOST "grep -c '^\*\*\*\*\*\*\*\*\*' '$latest_log' 2>/dev/null || echo 0")
    success=$(ssh $REMOTE_HOST "grep -c 'operator .* installed' '$latest_log' 2>/dev/null || echo 0")
    failed=$(ssh $REMOTE_HOST "grep -c 'Operator failed to install' '$latest_log' 2>/dev/null || echo 0")
    
    echo -e "${BOLD}Summary:${NC}"
    echo -e "  Total operators tested: ${BLUE}$total${NC}"
    echo -e "  Successful: ${GREEN}$success${NC}"
    echo -e "  Failed: ${RED}$failed${NC}"
    
    if [ "$total" -gt 0 ]; then
        success_rate=$(awk "BEGIN {printf \"%.1f\", ($success/$total)*100}")
        echo -e "  Success rate: ${GREEN}${success_rate}%${NC}"
    fi
    
    echo ""
    echo -e "${BOLD}Options:${NC}"
    echo "[1] View failed operators"
    echo "[2] View full log (last 100 lines)"
    echo "[3] Download results locally"
    echo "[4] Back to main menu"
    echo ""
    read -p "Select option: " opt
    
    case $opt in
        1)
            echo -e "\n${BOLD}Failed Operators:${NC}"
            ssh $REMOTE_HOST "grep -B3 'Operator failed to install' '$latest_log' | grep 'package=' | awk -F'package= ' '{print \$2}' | awk '{print \$1}'" | nl
            read -p "Press Enter to continue..."
            ;;
        2)
            ssh $REMOTE_HOST "tail -100 '$latest_log'" | less
            ;;
        3)
            local_file="$LOCAL_BASE_DIR/results/$(basename $latest_log)"
            scp $REMOTE_HOST:$latest_log "$local_file"
            echo -e "${GREEN}✓ Downloaded to: $local_file${NC}"
            read -p "Press Enter to continue..."
            ;;
        *)
            ;;
    esac
}

# Quick fixes menu
quick_fixes() {
    show_header
    echo -e "${BOLD}${YELLOW}Quick Fixes${NC}\n"
    echo "[1] Delete stale webhooks"
    echo "[2] Approve pending InstallPlans"
    echo "[3] Delete failed InstallPlans"
    echo "[4] Restart catalog pod"
    echo "[5] Check operator logs"
    echo "[9] Back to main menu"
    echo ""
    read -p "Select option: " opt
    
    case $opt in
        1)
            echo "Deleting stale webhooks..."
            ssh $REMOTE_HOST "oc delete mutatingwebhookconfiguration csv.odf.openshift.io --ignore-not-found=true"
            echo -e "${GREEN}✓ Done${NC}"
            read -p "Press Enter to continue..."
            ;;
        2)
            echo "Approving pending InstallPlans..."
            ssh $REMOTE_HOST 'for plan in $(oc get installplan -n openshift-storage -o name 2>/dev/null); do oc patch $plan -n openshift-storage --type merge -p "{\"spec\":{\"approved\":true}}"; done'
            echo -e "${GREEN}✓ Done${NC}"
            read -p "Press Enter to continue..."
            ;;
        3)
            echo "Deleting failed InstallPlans..."
            ssh $REMOTE_HOST "oc delete installplan --all -n openshift-storage"
            echo -e "${GREEN}✓ Done${NC}"
            read -p "Press Enter to continue..."
            ;;
        4)
            echo "Restarting catalog pod..."
            ssh $REMOTE_HOST "oc delete pod -n openshift-marketplace -l olm.catalogSource=operator-catalog"
            echo -e "${GREEN}✓ Done${NC}"
            read -p "Press Enter to continue..."
            ;;
        5)
            read -p "Operator name: " op_name
            ssh $REMOTE_HOST "oc logs -n openshift-storage deployment/$op_name --tail=50" || echo "Operator not found or no logs"
            read -p "Press Enter to continue..."
            ;;
        *)
            ;;
    esac
}

# Sync scripts
sync_scripts() {
    show_header
    echo -e "${BOLD}${BLUE}Syncing Scripts to Remote Cluster${NC}\n"
    
    echo "Syncing cleanup script..."
    scp "$LOCAL_BASE_DIR/scripts/cleanup-all-test-operators-v2.sh" $REMOTE_HOST:/tmp/
    
    echo "Syncing pre-flight checks..."
    scp "$LOCAL_BASE_DIR/scripts/pre-flight-checks.sh" $REMOTE_HOST:/tmp/
    
    echo "Syncing monitoring scripts..."
    scp "$LOCAL_BASE_DIR/scripts/live-monitor.sh" $REMOTE_HOST:/tmp/
    
    echo "Syncing test runner (if modified)..."
    scp "$LOCAL_BASE_DIR/scripts/run-basic-batch-operators-test.sh" $REMOTE_HOST:$REMOTE_BASE_DIR/script/ 2>/dev/null || echo "Skipped"
    
    echo -e "\n${GREEN}✓ Scripts synced successfully!${NC}"
    read -p "Press Enter to continue..."
}

# Main loop
main() {
    while true; do
        show_menu
        read -p "Select option: " choice
        
        case $choice in
            1) preflight_checks ;;
            2) clean_cluster ;;
            3) start_test ;;
            4) monitor_test ;;
            5) view_results ;;
            6) echo "Feature coming soon..."; read -p "Press Enter..." ;;
            7) echo "Feature coming soon..."; read -p "Press Enter..." ;;
            8) quick_fixes ;;
            9) sync_scripts ;;
            [Qq]) echo "Goodbye!"; exit 0 ;;
            *) echo "Invalid option"; sleep 1 ;;
        esac
    done
}

# Run main
main
