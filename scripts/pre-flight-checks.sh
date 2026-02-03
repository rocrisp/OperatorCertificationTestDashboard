#!/bin/bash

echo "=========================================="
echo "PRE-FLIGHT CHECKS FOR OPERATOR TESTING"
echo "=========================================="
echo ""

# Set kubeconfig
export KUBECONFIG=/root/test-rose/certsuite/kubeconfig-new

ISSUES=0

# 1. Check cluster connectivity
echo "1. Checking cluster connectivity..."
if oc whoami &>/dev/null; then
    echo "   ✓ Cluster accessible"
else
    echo "   ✗ Cannot connect to cluster"
    ISSUES=$((ISSUES+1))
fi

# 2. Check for leftover catalog sources
echo ""
echo "2. Checking for leftover catalog sources..."
CATALOGS=$(oc get catalogsource -n openshift-marketplace --no-headers 2>/dev/null | grep -E "operator-catalog|test-catalog" | wc -l)
if [ "$CATALOGS" -gt 0 ]; then
    echo "   ⚠ Found $CATALOGS leftover catalog sources:"
    oc get catalogsource -n openshift-marketplace | grep -E "operator-catalog|test-catalog"
    ISSUES=$((ISSUES+1))
else
    echo "   ✓ No leftover catalog sources"
fi

# 3. Check for test namespaces
echo ""
echo "3. Checking for leftover test namespaces..."
TEST_NS=$(oc get namespaces --no-headers 2>/dev/null | grep -E "^test-operator|^test-keda|^test-tempo|^openshift-keda" | wc -l)
if [ "$TEST_NS" -gt 0 ]; then
    echo "   ⚠ Found $TEST_NS test namespaces still present:"
    oc get namespaces | grep -E "^test-operator|^test-keda|^test-tempo|^openshift-keda"
    ISSUES=$((ISSUES+1))
else
    echo "   ✓ No leftover test namespaces"
fi

# 4. Check for operators with + suffix that should remain
echo ""
echo "4. Checking required operators (should be present)..."
EXPECTED_OPS=("lvms-operator" "odf-operator" "ocs-operator" "advanced-cluster-management" "multicluster-engine")
for op in "${EXPECTED_OPS[@]}"; do
    if oc get csv -A --no-headers 2>/dev/null | grep -q "$op"; then
        echo "   ✓ $op present"
    else
        echo "   ⚠ $op missing (expected to remain installed)"
    fi
done

# 5. Check for unexpected operators in test-operator namespace
echo ""
echo "5. Checking for operators in non-persistent namespaces..."
for ns in test-operator openshift-keda openshift-tempo-operator; do
    if oc get namespace "$ns" &>/dev/null; then
        CSV_COUNT=$(oc get csv -n "$ns" --no-headers 2>/dev/null | wc -l)
        if [ "$CSV_COUNT" -gt 0 ]; then
            echo "   ⚠ Found $CSV_COUNT CSVs in $ns (should be empty):"
            oc get csv -n "$ns" --no-headers
            ISSUES=$((ISSUES+1))
        fi
    fi
done
if [ "$ISSUES" -eq "$ISSUES" ]; then
    echo "   ✓ No unexpected operators in test namespaces"
fi

# 6. Check cluster node health
echo ""
echo "6. Checking cluster node health..."
NOT_READY=$(oc get nodes --no-headers 2>/dev/null | grep -v " Ready" | wc -l)
if [ "$NOT_READY" -gt 0 ]; then
    echo "   ⚠ $NOT_READY nodes not ready:"
    oc get nodes | grep -v " Ready"
    ISSUES=$((ISSUES+1))
else
    TOTAL_NODES=$(oc get nodes --no-headers | wc -l)
    echo "   ✓ All $TOTAL_NODES nodes ready"
fi

# 7. Check for failed/pending pods in key namespaces
echo ""
echo "7. Checking for problematic pods..."
FAILED_PODS=$(oc get pods -A --no-headers 2>/dev/null | grep -E "Error|CrashLoopBackOff|ImagePullBackOff" | wc -l)
if [ "$FAILED_PODS" -gt 0 ]; then
    echo "   ⚠ Found $FAILED_PODS pods in failed state:"
    oc get pods -A | grep -E "Error|CrashLoopBackOff|ImagePullBackOff" | head -10
    ISSUES=$((ISSUES+1))
else
    echo "   ✓ No failed pods detected"
fi

# 8. Check OLM health
echo ""
echo "8. Checking OLM components..."
OLM_PODS=$(oc get pods -n openshift-operator-lifecycle-manager --no-headers 2>/dev/null | grep -v "Running" | wc -l)
if [ "$OLM_PODS" -gt 0 ]; then
    echo "   ⚠ OLM pods not all running:"
    oc get pods -n openshift-operator-lifecycle-manager | grep -v "Running"
    ISSUES=$((ISSUES+1))
else
    echo "   ✓ OLM components healthy"
fi

# 9. Check required files
echo ""
echo "9. Checking required test files..."
if [ -f "/root/test-rose/certsuite/config/dockerconfig" ]; then
    echo "   ✓ Docker config present"
else
    echo "   ✗ Docker config missing at /root/test-rose/certsuite/config/dockerconfig"
    ISSUES=$((ISSUES+1))
fi

if [ -f "/root/test-rose/certsuite/script/config.json" ]; then
    echo "   ✓ Script config.json present"
else
    echo "   ✗ Script config.json missing (may need to copy from config/dockerconfig)"
    ISSUES=$((ISSUES+1))
fi

if [ -f "/root/test-rose/certsuite/run-ocp-4.20-test-v2.sh" ]; then
    echo "   ✓ Test script present"
else
    echo "   ✗ Test script missing"
    ISSUES=$((ISSUES+1))
fi

# 10. Check disk space
echo ""
echo "10. Checking disk space..."
DISK_USAGE=$(df -h /var/www/html 2>/dev/null | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "   ⚠ Disk usage high: ${DISK_USAGE}%"
    ISSUES=$((ISSUES+1))
else
    echo "   ✓ Disk space adequate (${DISK_USAGE}% used)"
fi

# 11. Check for running test processes
echo ""
echo "11. Checking for running test processes..."
TEST_PROCS=$(ps aux | grep -E "run-basic-batch|run-ocp-4.20" | grep -v grep | wc -l)
if [ "$TEST_PROCS" -gt 0 ]; then
    echo "   ⚠ Found $TEST_PROCS running test processes:"
    ps aux | grep -E "run-basic-batch|run-ocp-4.20" | grep -v grep
    ISSUES=$((ISSUES+1))
else
    echo "   ✓ No running test processes"
fi

# Summary
echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
if [ "$ISSUES" -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED - Ready to run tests"
    exit 0
else
    echo "⚠️  FOUND $ISSUES ISSUES - Review and fix before running tests"
    exit 1
fi
