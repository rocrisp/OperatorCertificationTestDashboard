#\!/bin/bash

echo "=========================================="
echo "LIVE TEST MONITOR"
echo "Started: $(date)"
echo "=========================================="
echo ""
echo "Monitoring tmux session: operator-test"
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
    clear
    echo "=========================================="
    echo "OPERATOR TEST PROGRESS"
    echo "Time: $(date)"
    echo "=========================================="
    echo ""
    
    # Check tmux session status
    if tmux has-session -t operator-test 2>/dev/null; then
        echo "Status: ✅ Test is RUNNING"
    else
        echo "Status: ⚠️  Test COMPLETED or session ended"
        echo ""
        echo "Check test results in /root/test-rose/certsuite/"
        break
    fi
    
    # Get latest output from tmux
    output=$(tmux capture-pane -t operator-test -p -S -50)
    
    # Extract current operator being tested
    current_op=$(echo "$output" | grep "^\*\*\*\*\*\*\*\*\*" | tail -1 | awk -F"package= " '{print $2}' | awk '{print $1}')
    
    if [ -n "$current_op" ]; then
        echo "Current Operator: $current_op"
    else
        echo "Current Operator: Starting up..."
    fi
    
    echo ""
    echo "=========================================="
    echo "Recent Output (last 25 lines):"
    echo "=========================================="
    echo "$output" | tail -25
    
    echo ""
    echo "=========================================="
    echo "Next update in 30 seconds..."
    echo "Press Ctrl+C to stop monitoring"
    echo "=========================================="
    
    sleep 30
done

