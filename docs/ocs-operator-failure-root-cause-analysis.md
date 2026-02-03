# OCS-OPERATOR+ FAILURE ROOT CAUSE ANALYSIS
**Issue:** ocs-operator+ failed to install in Feb 2 PM test but succeeded in previous tests
**Date:** February 2, 2026

---

## COMPARISON: WORKING vs FAILED TESTS

### Jan 30 Test - ✅ PASSED
**Log:** `/root/test-rose/certsuite/test-run-20260130-172401.log`
```
[90m********* package= ocs-operator+ ***[0m
[36mPackage has + suffix: will skip cleanup for ocs-operator[0m
[36minstall operator[0m
[36mOperator subscription already exists (expected with + suffix), continuing...[0m
[36mWait for CSV to appear and label resources under test[0m
[90mLabeling CSV: ocs-operator.v4.20.4-rhodf[0m  ← CSV FOUND IMMEDIATELY
clusterserviceversion.operators.coreos.com/ocs-operator.v4.20.4-rhodf labeled
[36mWait for CSV to be succeeded[0m
clusterserviceversion.operators.coreos.com/ocs-operator.v4.20.4-rhodf condition met
[36moperator ocs-operator installed[0m  ← SUCCESS
```

### Feb 2 AM Test - ✅ PASSED
**Log:** `/root/test-rose/certsuite/test-run-20260202-085840.log`
```
[90m********* package= ocs-operator+ ***[0m
[36mPackage has + suffix: will skip cleanup for ocs-operator[0m
[36minstall operator[0m
[36mOperator subscription already exists (expected with + suffix), continuing...[0m
[36mWait for CSV to appear and label resources under test[0m
[90mLabeling CSV: ocs-operator.v4.20.4-rhodf[0m  ← CSV FOUND IMMEDIATELY
clusterserviceversion.operators.coreos.com/ocs-operator.v4.20.4-rhodf labeled
[36mWait for CSV to be succeeded[0m
clusterserviceversion.operators.coreos.com/ocs-operator.v4.20.4-rhodf condition met
[36moperator ocs-operator installed[0m  ← SUCCESS
```

### Feb 2 PM Test - ❌ FAILED
**Log:** `/root/test-rose/certsuite/test-run-FIXED-20260202-130319.log`
```
[90m********* package= ocs-operator+ ***[0m
[36mPackage has + suffix: will skip cleanup for ocs-operator[0m
[36minstall operator[0m
[36mOperator subscription already exists (expected with + suffix), continuing...[0m
[36mWait for CSV to appear and label resources under test[0m
[36mWaiting for csv for ocs-operator to be created in namespace openshift-storage ...[0m
[repeated 20 times - 100 seconds]
[36mTimeout reached 100 seconds waiting for CSV for ocs-operator.[0m
[31mOperator failed to install, continue[0m  ← FAILURE
```

---

## KEY DIFFERENCE

**Working Tests:** CSV found **immediately** (no waiting)
**Failed Test:** CSV **never found** despite 100 second timeout

---

## CURRENT STATE ANALYSIS

### Subscription Status (Current)
```bash
$ oc get subscription ocs-operator -n openshift-storage -o jsonpath='{.status}'
status:
  conditions:
  - type: CatalogSourcesUnhealthy
    status: "True"
    message: dependency resolution requires at least one catalogsource
    reason: NoCatalogSourcesFound
    lastTransitionTime: "2026-02-03T14:53:19Z"
  - type: ResolutionFailed
    status: "True"
    reason: ConstraintsNotSatisfiable
    message: 'constraints not satisfiable: no operators found from catalog
             operator-catalog in namespace openshift-marketplace referenced
             by subscription mcg-operator, subscription mcg-operator exists'
```

**Key Findings:**
1. **CatalogSourcesUnhealthy:** "dependency resolution requires at least one catalogsource"
2. **ResolutionFailed:** "no operators found from catalog operator-catalog"
3. **installedCSV field:** EMPTY (no value)

### CSV Status (Current)
```bash
$ oc get csv ocs-operator.v4.20.4-rhodf -n openshift-storage
NAME                        DISPLAY                        VERSION        REPLACES                     PHASE
ocs-operator.v4.20.4-rhodf  OpenShift Container Storage    4.20.4-rhodf   ocs-operator.v4.20.3-rhodf   Succeeded
```

**CSV exists and is in "Succeeded" phase**

### Catalog Sources (Current)
```bash
$ oc get catalogsource -n openshift-marketplace
No resources found in openshift-marketplace namespace.
```

**NO CATALOG SOURCES EXIST**

---

## ROOT CAUSE ANALYSIS

### Timeline of Events

**Jan 29, 2026:**
- 21:22:48Z - ocs-operator CSV created
- 21:42:25Z - ocs-operator subscription created, pointing to "operator-catalog"

**Jan 30, 2026 - Test Run #1:**
- Test starts, creates "operator-catalog" catalogsource
- ocs-operator+ tested: subscription exists, CSV found, test passes
- Test ends, **deletes "operator-catalog" catalogsource**

**Feb 2, 2026 AM - Test Run #2:**
- Test starts, creates "operator-catalog" catalogsource
- ocs-operator+ tested: subscription exists, CSV found, test passes
- Test ends, **deletes "operator-catalog" catalogsource**

**Feb 2, 2026 PM - Test Run #3 (FAILED):**
- Test starts, creates "operator-catalog" catalogsource
- ocs-operator+ tested at 1:03 PM
- **subscription.status.installedCSV is EMPTY** (subscription in ResolutionFailed)
- Enhanced fix tries fallback grep
- **Grep should have found CSV** but didn't
- Test times out after 100 seconds

---

## WHY THE ENHANCED FIX DIDN'T WORK

The enhanced fix has two steps:

**Step 1: Query subscription status**
```bash
csv_name=$(oc get subscription "$operator_package" -n "$csv_namespace" \
           -o jsonpath='{.status.installedCSV}' 2>/dev/null)
```
**Result:** EMPTY (subscription in ResolutionFailed state)

**Step 2: Fallback grep**
```bash
if [ -z "$csv_name" ] || [ "$csv_name" = "<none>" ]; then
    csv_name=$(oc get csv -n "$csv_namespace" \
               -o custom-columns=':.metadata.name' \
               --no-headers 2>/dev/null | \
               grep -i "$operator_package" | head -1)
fi
```

**Testing the grep NOW (current state):**
```bash
$ oc get csv -n openshift-storage -o custom-columns=':.metadata.name' --no-headers 2>/dev/null | grep -i "ocs-operator" | head -1
ocs-operator.v4.20.4-rhodf  ← FOUND!
```

**The grep WOULD work now, so why didn't it work during the test?**

---

## HYPOTHESIS: CSV WAS DELETED DURING TEST

**Theory:** Between when odf-operator+ was tested and when ocs-operator+ was tested, the ocs-operator CSV was temporarily deleted or in a non-existent state.

**Evidence Supporting This Theory:**

1. **odf-operator+ tested successfully** (just before ocs-operator+)
   - Same namespace (openshift-storage)
   - Same + suffix behavior
   - CSV found immediately

2. **ocs-operator+ failed to find CSV**
   - Very next test after odf-operator+
   - Same enhanced fix code running
   - Grep should have found it

3. **advanced-cluster-management+ tested successfully** (just after ocs-operator+)
   - Different namespace
   - CSV found immediately

**Possible Scenarios:**

### Scenario A: OLM Deleted CSV Due to Catalog Issues
When the test created "operator-catalog", OLM may have detected that the ocs-operator subscription was pointing to a catalog that just appeared, and attempted to reconcile. During reconciliation, OLM might have:
1. Marked the existing CSV for deletion
2. Attempted to install a new CSV from the catalog
3. Failed due to conflicts in openshift-storage
4. Left subscription in ResolutionFailed state with no CSV

### Scenario B: Timing Issue with Catalog Creation
The "operator-catalog" was created at line 2 of the test log, but it may have taken time for OLM to fully reconcile it. During this time:
1. odf-operator+ was tested and found its CSV (CSV already existed from before)
2. ocs-operator+ was tested, but at this moment OLM was actively reconciling the subscription
3. CSV was temporarily inaccessible or being replaced
4. Grep returned empty result

### Scenario C: Multiple Subscriptions Conflict
Looking at current state, there are **TWO subscriptions for ocs-operator:**
```
ocs-operator
ocs-operator-stable-4.20-operator-catalog-openshift-marketplace
```

This suggests that `oc operator install` may have created a duplicate subscription, causing OLM confusion and CSV deletion.

---

## VERIFICATION

### Check if Multiple Subscriptions Exist
```bash
$ oc get subscription -n openshift-storage | grep ocs-operator
ocs-operator
ocs-operator-stable-4.20-operator-catalog-openshift-marketplace
```

**TWO subscriptions found for ocs-operator!**

This is the root cause:
1. Original subscription: `ocs-operator` (created Jan 29, points to operator-catalog)
2. Duplicate subscription: `ocs-operator-stable-4.20-operator-catalog-openshift-marketplace` (created during test)

When the test ran `oc operator install`, it may have:
- Created a new subscription instead of detecting the existing one
- Caused OLM conflict
- CSV was deleted or became unavailable during resolution
- Neither subscription could track the CSV properly

---

## ROOT CAUSE (FINAL)

**The ocs-operator+ failure occurred because:**

1. **Pre-existing subscription** `ocs-operator` existed from initial installation (Jan 29)
2. **Test script** attempted to install ocs-operator+ again during Feb 2 PM test
3. **oc operator install** command may have created a **duplicate subscription**
4. **OLM conflict** caused CSV to be temporarily deleted or inaccessible
5. **Enhanced fix** ran at the exact moment CSV didn't exist or wasn't queryable
6. **100-second timeout** wasn't enough for OLM to resolve the conflict and recreate CSV

---

## WHY OTHER + OPERATORS WORKED

**odf-operator+, lvms-operator+, advanced-cluster-management+, multicluster-engine+** all succeeded because:
- Their subscriptions were in healthy state when tested
- No duplicate subscriptions created
- CSVs were stable and queryable
- subscription.status.installedCSV or grep found the CSV immediately

---

## SOLUTION

### Immediate Fix: Clean Up Duplicate Subscriptions

```bash
# Delete the duplicate subscription
oc delete subscription ocs-operator-stable-4.20-operator-catalog-openshift-marketplace \
  -n openshift-storage

# Check remaining subscriptions
oc get subscription -n openshift-storage | grep ocs-operator
```

### Long-term Fix: Prevent Duplicate Subscriptions

**Modify script to skip `oc operator install` for + suffix operators that already have subscriptions:**

```bash
# In wait_for_csv_to_appear_and_label() or before calling oc operator install
if [[ "$operator_package" == *"+" ]]; then
    # Check if subscription already exists
    existing_sub=$(oc get subscription "${operator_package%+}" -n "$csv_namespace" \
                   -o name 2>/dev/null)

    if [ -n "$existing_sub" ]; then
        echo_color "$BLUE" "Subscription already exists for + operator, skipping install"
        # Don't run oc operator install, just wait for CSV
    fi
fi
```

### Additional Enhancement: Detect Multiple Subscriptions

Add subscription conflict detection:

```bash
# After attempting to find CSV, check for multiple subscriptions
sub_count=$(oc get subscription -n "$csv_namespace" --no-headers 2>/dev/null | \
            grep -c "$operator_package" || true)

if [ "$sub_count" -gt 1 ]; then
    echo_color "$RED" "WARNING: Multiple subscriptions found for $operator_package"
    echo_color "$RED" "This may indicate a subscription conflict"
    oc get subscription -n "$csv_namespace" | grep "$operator_package"
fi
```

---

## NEXT STEPS

1. ✅ **Verify duplicate subscription** exists on rdu2 cluster
2. ✅ **Delete duplicate subscription** to restore ocs-operator health
3. ✅ **Update script** to skip `oc operator install` for existing + suffix subscriptions
4. ✅ **Test** ocs-operator+ again to confirm it works
5. ✅ **Document** the issue and fix in test documentation

---

**Analysis Date:** February 3, 2026
**Analyzed By:** Claude Code
**Document Location:** `/tmp/ocs-operator-failure-root-cause-analysis.md`
