# TEST FAILURE ROOT CAUSE AND RESOLUTION

**Date:** February 3, 2026 11:30 AM EST
**Issue:** First 3 operators (lvms, odf, ocs) failed during test run
**Status:** ✅ RESOLVED

---

## PROBLEM DISCOVERED

The test started but the first 3 storage operators failed immediately:
- ❌ lvms-operator+ - Operator installation failed, skipping test
- ❌ odf-operator+ - Operator installation failed, skipping test
- ❌ ocs-operator+ - Operator installation failed, skipping test

But operators 4 and 5 succeeded:
- ✅ advanced-cluster-management+ - SUCCESS
- ✅ multicluster-engine+ - SUCCESS

---

## ROOT CAUSE IDENTIFIED

### The Stale Webhook Problem

When we cleaned up all operators before the test, we deleted:
- ✅ All subscriptions
- ✅ All CSVs
- ✅ All operator pods
- ❌ **BUT we did NOT delete the webhook configurations**

**Critical Finding:**
ODF (OpenShift Data Foundation) operators install a **mutating webhook** that intercepts all CSV creation requests in the `openshift-storage` namespace.

**Webhook Configuration:**
- Name: `csv.odf.openshift.io`
- Type: MutatingWebhookConfiguration
- Target Service: `odf-operator-webhook-server-service.openshift-storage.svc`

**What Happened:**
1. Test started, catalog created
2. Script ran `oc operator install lvms-operator`
3. Subscription created ✅
4. OLM created InstallPlan ✅
5. OLM tried to create CSV for lvms-operator
6. Kubernetes called the mutating webhook `csv.odf.openshift.io`
7. **Webhook tried to call service that doesn't exist** (we deleted it during cleanup)
8. Webhook call failed with timeout
9. CSV creation failed ❌
10. InstallPlan marked as Failed

**Error Message:**
```
error creating csv lvms-operator.v4.20.0: Internal error occurred:
failed calling webhook "csv.odf.openshift.io": failed to call webhook:
Post "https://odf-operator-webhook-server-service.openshift-storage.svc:443/mutate-operators-coreos-com-v1alpha1-csv?timeout=30s":
service "odf-operator-webhook-server-service" not found
```

**Why advanced-cluster-management+ and multicluster-engine+ Succeeded:**
They use different namespaces (open-cluster-management, multicluster-engine), so they weren't affected by the openshift-storage webhook.

---

## RESOLUTION

### Step 1: Delete the Stale Webhook
```bash
oc delete mutatingwebhookconfiguration csv.odf.openshift.io
```
Result: `mutatingwebhookconfiguration.admissionregistration.k8s.io "csv.odf.openshift.io" deleted`

### Step 2: Delete Failed InstallPlans
```bash
oc delete installplan --all -n openshift-storage
```
Result: Deleted 3 failed InstallPlans

### Step 3: Approve New InstallPlans
OLM automatically recreated InstallPlans. Approved them manually:
```bash
oc patch installplan <name> -n openshift-storage --type merge -p '{"spec":{"approved":true}}'
```

### Step 4: Verify CSVs Created
```bash
oc get csv -n openshift-storage
```

Result:
```
NAME                         DISPLAY                       VERSION        PHASE
lvms-operator.v4.20.0        LVM Storage                   4.20.0         Succeeded
ocs-operator.v4.20.4-rhodf   OpenShift Container Storage   4.20.4-rhodf   Installing
odf-operator.v4.20.4-rhodf   OpenShift Data Foundation     4.20.4-rhodf   Installing
```

✅ **CSVs are now being created successfully!**

---

## IMPACT ON RUNNING TEST

### Current Test Status

**Failed Operators (Already Tested):**
1. lvms-operator+ - ❌ Failed (but now fixed)
2. odf-operator+ - ❌ Failed (but now fixed)
3. ocs-operator+ - ❌ Failed (but now fixed)

**Succeeded Operators:**
4. advanced-cluster-management+ - ✅ Passed
5. multicluster-engine+ - ✅ Passed

**Remaining Operators:**
- 47 operators still to be tested
- They should work normally now

### Should We Restart the Test?

**Option 1: Let Current Test Continue** (Not Recommended)
- 3 operators already marked as failed
- Results will show 3 false failures
- Success rate will be artificially low

**Option 2: Stop and Restart Test** (Recommended)
- Stop current test
- Restart with clean state
- All operators will have fair chance
- Accurate success rate

---

## UPDATED CLEANUP SCRIPT NEEDED

The cleanup script needs to be updated to also remove webhook configurations.

**Add to cleanup script:**
```bash
echo_color "$BLUE" "Step 7: Clean up webhook configurations"
echo ""

# Delete ODF webhook configurations
if oc get mutatingwebhookconfiguration csv.odf.openshift.io &>/dev/null; then
    echo "Deleting mutatingwebhookconfiguration: csv.odf.openshift.io"
    oc delete mutatingwebhookconfiguration csv.odf.openshift.io --ignore-not-found=true
fi

# Check for other operator webhooks
oc get mutatingwebhookconfigurations | grep -E "operator|odf|ocs|lvms" || echo "No operator webhooks found"
oc get validatingwebhookconfigurations | grep -E "operator|odf|ocs|lvms" || echo "No operator webhooks found"
```

---

## LESSONS LEARNED

### What Caused This

1. **Incomplete Cleanup**: Webhook configurations are cluster-scoped resources, not namespace-scoped
2. **Missed Resource Type**: We deleted subscriptions, CSVs, namespaces but not webhooks
3. **Silent Failure**: The webhook existed but pointed to non-existent service
4. **Timing**: Only affected openshift-storage namespace operators

### Prevention for Future

**Enhanced Cleanup Checklist:**
- ✅ Delete subscriptions
- ✅ Delete CSVs
- ✅ Delete namespaces
- ✅ Delete catalogsources
- ✅ **Delete mutatingwebhookconfigurations** ← NEW
- ✅ **Delete validatingwebhookconfigurations** ← NEW
- ✅ Delete any custom resources
- ✅ Delete operator-created CRDs (if safe)

**Pre-Test Validation:**
```bash
# Check for stale webhooks before starting test
oc get mutatingwebhookconfigurations | grep -E "operator|odf|ocs|lvms"
oc get validatingwebhookconfigurations | grep -E "operator|odf|ocs|lvms"
```

---

## CURRENT TEST DECISION

**Recommendation:** STOP and RESTART the test

**Reasons:**
1. First 3 operators have false failures
2. Now that webhook is removed, they will succeed
3. Clean results are important for accurate metrics
4. Only lost ~30 minutes of test time

**Command to Stop Test:**
```bash
ssh rdu2 'tmux kill-session -t operator-test'
```

**Command to Restart Test:**
```bash
ssh rdu2 'tmux new-session -d -s operator-test "cd /root/test-rose/certsuite && ./run-ocp-4.20-test-v2.sh"'
```

---

## FILES TO UPDATE

### 1. Cleanup Script
**File:** `/tmp/cleanup-all-test-operators.sh`
**Action:** Add webhook cleanup section

### 2. Pre-Flight Check Script
**File:** `/tmp/pre-flight-checks.sh`
**Action:** Add webhook validation check

### 3. Test Documentation
**Update:** All test run documentation to include webhook cleanup step

---

## SUMMARY

**Problem:** Stale ODF webhook blocked CSV creation in openshift-storage namespace
**Root Cause:** Incomplete cleanup - webhooks not deleted
**Impact:** First 3 storage operators failed, 2 others succeeded
**Resolution:** Deleted stale webhook, approved InstallPlans
**Status:** ✅ FIXED - CSVs now creating successfully
**Recommendation:** Restart test for clean results

---

**Issue Discovered:** February 3, 2026 11:15 AM EST
**Resolution Applied:** February 3, 2026 11:30 AM EST
**Time to Diagnose:** 15 minutes
**Status:** ✅ RESOLVED
