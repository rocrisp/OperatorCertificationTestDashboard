#\!/bin/bash

set -e

echo "=========================================="
echo "CLEANUP ALL TEST OPERATORS - v2"
echo "Includes webhook configuration cleanup"
echo "Date: $(date)"
echo "=========================================="
echo ""

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
BLUE='\\033[0;36m'
NC='\\033[0m' # No Color

echo_color() {
    color=$1
    shift
    echo -e "${color}$*${NC}"
}

echo_color "$BLUE" "Step 1: Delete all subscriptions in test namespaces"
echo ""

# Delete subscriptions in openshift-storage
echo "Deleting subscriptions in openshift-storage..."
oc get subscription -n openshift-storage --no-headers 2>/dev/null | awk '{print $1}' | while read sub; do
    echo "  - Deleting subscription: $sub"
    oc delete subscription "$sub" -n openshift-storage --ignore-not-found=true
done

# Delete subscriptions in open-cluster-management
echo "Deleting subscriptions in open-cluster-management..."
oc delete subscription --all -n open-cluster-management --ignore-not-found=true

# Delete subscriptions in multicluster-engine
echo "Deleting subscriptions in multicluster-engine..."
oc delete subscription --all -n multicluster-engine --ignore-not-found=true

# Delete subscriptions in test-multicluster-engine
echo "Deleting subscriptions in test-multicluster-engine..."
oc delete subscription --all -n test-multicluster-engine --ignore-not-found=true

echo ""
echo_color "$BLUE" "Step 2: Delete all CSVs in test namespaces"
echo ""

# Delete CSVs in openshift-storage
echo "Deleting CSVs in openshift-storage..."
oc get csv -n openshift-storage --no-headers 2>/dev/null | awk '{print $1}' | while read csv; do
    echo "  - Deleting CSV: $csv"
    oc delete csv "$csv" -n openshift-storage --ignore-not-found=true --wait=false
done

# Delete CSVs in open-cluster-management
echo "Deleting CSVs in open-cluster-management..."
oc delete csv --all -n open-cluster-management --ignore-not-found=true --wait=false

# Delete CSVs in multicluster-engine
echo "Deleting CSVs in multicluster-engine..."
oc delete csv --all -n multicluster-engine --ignore-not-found=true --wait=false

# Delete CSVs in test-multicluster-engine
echo "Deleting CSVs in test-multicluster-engine..."
oc delete csv --all -n test-multicluster-engine --ignore-not-found=true --wait=false

echo ""
echo_color "$BLUE" "Step 3: Delete test namespaces"
echo ""

# Delete test-multicluster-engine namespace
if oc get namespace test-multicluster-engine &>/dev/null; then
    echo "Deleting namespace: test-multicluster-engine"
    oc delete namespace test-multicluster-engine --wait=false --ignore-not-found=true
fi

# Delete test-operator namespace if it exists
if oc get namespace test-operator &>/dev/null; then
    echo "Deleting namespace: test-operator"
    oc delete namespace test-operator --wait=false --ignore-not-found=true
fi

# Delete any other test-* namespaces
oc get namespaces --no-headers | grep "^test-" | awk '{print $1}' | while read ns; do
    if [ "$ns" \!= "test-multicluster-engine" ] && [ "$ns" \!= "test-operator" ]; then
        echo "Deleting namespace: $ns"
        oc delete namespace "$ns" --wait=false --ignore-not-found=true
    fi
done

echo ""
echo_color "$BLUE" "Step 4: Wait for deletions to complete (max 2 minutes)"
echo ""

# Wait for CSVs to be deleted
timeout=120
elapsed=0
while [ $elapsed -lt $timeout ]; do
    csv_count=$(oc get csv -n openshift-storage --no-headers 2>/dev/null | wc -l || echo 0)
    csv_count2=$(oc get csv -n open-cluster-management --no-headers 2>/dev/null | wc -l || echo 0)
    csv_count3=$(oc get csv -n multicluster-engine --no-headers 2>/dev/null | wc -l || echo 0)
    
    total_csvs=$((csv_count + csv_count2 + csv_count3))
    
    if [ "$total_csvs" -eq 0 ]; then
        echo_color "$GREEN" "All CSVs deleted successfully"
        break
    fi
    
    echo "Waiting for CSVs to be deleted... ($total_csvs remaining)"
    sleep 5
    elapsed=$((elapsed + 5))
done

echo ""
echo_color "$BLUE" "Step 5: Force delete stuck CSVs (if any)"
echo ""

# Force delete any remaining CSVs with finalizers
for ns in openshift-storage open-cluster-management multicluster-engine; do
    oc get csv -n "$ns" --no-headers 2>/dev/null | awk '{print $1}' | while read csv; do
        echo "Force deleting CSV: $csv in namespace $ns"
        oc patch csv "$csv" -n "$ns" -p '{"metadata":{"finalizers":null}}' --type=merge 2>/dev/null || true
        oc delete csv "$csv" -n "$ns" --force --grace-period=0 --ignore-not-found=true 2>/dev/null || true
    done
done

echo ""
echo_color "$BLUE" "Step 6: Clean up webhook configurations"
echo ""

# Delete ODF webhook configurations
if oc get mutatingwebhookconfiguration csv.odf.openshift.io &>/dev/null; then
    echo "Deleting mutatingwebhookconfiguration: csv.odf.openshift.io"
    oc delete mutatingwebhookconfiguration csv.odf.openshift.io --ignore-not-found=true
else
    echo "No csv.odf.openshift.io webhook found (expected after clean cluster)"
fi

# Check for other operator-related webhooks
echo "Checking for other operator webhooks..."
webhook_count=$(oc get mutatingwebhookconfigurations 2>/dev/null | grep -cE "operator|odf|ocs|lvms" || echo 0)
if [ "$webhook_count" -gt 0 ]; then
    echo_color "$RED" "Found $webhook_count operator-related webhooks:"
    oc get mutatingwebhookconfigurations | grep -E "operator|odf|ocs|lvms"
else
    echo "No operator-related mutating webhooks found"
fi

echo ""
echo_color "$BLUE" "Step 7: Delete failed InstallPlans"
echo ""

# Delete all InstallPlans in openshift-storage
installplan_count=$(oc get installplan -n openshift-storage --no-headers 2>/dev/null | wc -l || echo 0)
if [ "$installplan_count" -gt 0 ]; then
    echo "Deleting $installplan_count InstallPlans in openshift-storage..."
    oc delete installplan --all -n openshift-storage --ignore-not-found=true
else
    echo "No InstallPlans found in openshift-storage"
fi

echo ""
echo_color "$BLUE" "Step 8: Clean up operator-catalog catalogsource (if exists)"
echo ""

if oc get catalogsource operator-catalog -n openshift-marketplace &>/dev/null; then
    echo "Deleting catalogsource: operator-catalog"
    oc delete catalogsource operator-catalog -n openshift-marketplace --ignore-not-found=true
else
    echo "No operator-catalog catalogsource found (expected)"
fi

echo ""
echo_color "$GREEN" "=========================================="
echo_color "$GREEN" "CLEANUP COMPLETE"
echo_color "$GREEN" "=========================================="
echo ""

echo "Final State:"
echo ""
echo "CSVs in openshift-storage: $(oc get csv -n openshift-storage --no-headers 2>/dev/null | wc -l || echo 0)"
echo "CSVs in open-cluster-management: $(oc get csv -n open-cluster-management --no-headers 2>/dev/null | wc -l || echo 0)"
echo "CSVs in multicluster-engine: $(oc get csv -n multicluster-engine --no-headers 2>/dev/null | wc -l || echo 0)"
echo ""
echo "Subscriptions in openshift-storage: $(oc get subscription -n openshift-storage --no-headers 2>/dev/null | wc -l || echo 0)"
echo "Subscriptions in open-cluster-management: $(oc get subscription -n open-cluster-management --no-headers 2>/dev/null | wc -l || echo 0)"
echo "Subscriptions in multicluster-engine: $(oc get subscription -n multicluster-engine --no-headers 2>/dev/null | wc -l || echo 0)"
echo ""
echo "InstallPlans in openshift-storage: $(oc get installplan -n openshift-storage --no-headers 2>/dev/null | wc -l || echo 0)"
echo ""
echo "Operator webhooks: $(oc get mutatingwebhookconfigurations 2>/dev/null | grep -cE "operator|odf|ocs|lvms" || echo 0)"
echo ""

echo_color "$BLUE" "Cluster is now ready for clean operator testing"

