# PRE-TEST CLEANUP COMPLETE

**Date:** February 3, 2026 10:56 AM EST
**Purpose:** Clean cluster state before running operator tests
**Script:** `/tmp/cleanup-all-test-operators.sh`

---

## CLEANUP SUMMARY

### ✅ Successfully Deleted

**Subscriptions Deleted:** 16 total
- openshift-storage: 13 subscriptions (including duplicate ocs-operator)
- open-cluster-management: 1 subscription
- multicluster-engine: 1 subscription
- test-multicluster-engine: 1 subscription

**CSVs Deleted:** 14 total
- openshift-storage: 10 CSVs (lvms, odf, ocs, ceph, etc.)
- open-cluster-management: 1 CSV (advanced-cluster-management)
- multicluster-engine: 1 CSV
- test-multicluster-engine: 1 CSV

**Namespaces Deleted:** 1
- test-multicluster-engine

---

## FINAL CLUSTER STATE

### CSVs Remaining
**Total:** 1 (system operator only)
- openshift-operator-lifecycle-manager: packageserver (system operator)

### Subscriptions Remaining
**Total:** 0
- All test operator subscriptions removed ✅

### Namespaces Preserved
The following namespaces still exist but are now empty of test operators:
- openshift-storage (contains vg-manager pods only)
- open-cluster-management (contains some cluster-curator/manager pods from previous install)
- multicluster-engine (empty)
- open-cluster-management-agent (system namespace)
- open-cluster-management-agent-addon (system namespace)
- open-cluster-management-global-set (system namespace)
- open-cluster-management-hub (system namespace)

---

## ISSUES RESOLVED

### 1. ✅ Duplicate ocs-operator Subscription
**Before:** 2 subscriptions
- ocs-operator
- ocs-operator-stable-4.20-operator-catalog-openshift-marketplace

**After:** 0 subscriptions
- Both deleted successfully

### 2. ✅ Failed Subscriptions Without CSV
**Before:**
- odf-csi-addons-operator (subscription, no CSV)
- mcg-operator (subscription, no CSV)

**After:**
- Both subscriptions deleted

### 3. ✅ All + Suffix Operators Removed
**Before:**
- lvms-operator+ (installed)
- odf-operator+ (installed)
- ocs-operator+ (installed)
- advanced-cluster-management+ (installed)
- multicluster-engine+ (installed)

**After:**
- All removed - will be installed fresh during test

---

## CLEANUP SCRIPT DETAILS

### What the Script Does

**Step 1:** Delete all subscriptions in test namespaces
- Iterates through each subscription and deletes individually
- Covers: openshift-storage, open-cluster-management, multicluster-engine, test-multicluster-engine

**Step 2:** Delete all CSVs in test namespaces
- Deletes with `--wait=false` to avoid blocking on finalizers
- Preserves system CSVs (packageserver)

**Step 3:** Delete test namespaces
- Removes test-multicluster-engine
- Removes test-operator (if exists)
- Removes any other test-* namespaces

**Step 4:** Wait for deletions (max 2 minutes)
- Polls every 5 seconds to verify CSVs are gone
- Exits early if all CSVs deleted successfully

**Step 5:** Force delete stuck CSVs
- Removes finalizers from any remaining CSVs
- Force deletes with --grace-period=0

**Step 6:** Clean up catalogsource
- Deletes operator-catalog if it exists
- (None found - expected between test runs)

---

## VERIFICATION COMMANDS

```bash
# Check CSVs
oc get csv -A

# Check subscriptions
oc get subscription -A

# Check catalogsources
oc get catalogsource -n openshift-marketplace

# Check pods in test namespaces
oc get pods -n openshift-storage
oc get pods -n open-cluster-management
oc get pods -n multicluster-engine
```

---

## NEXT STEPS

The cluster is now in a clean state for testing:

### Before Test Run
1. ✅ All test operator subscriptions removed
2. ✅ All test operator CSVs removed
3. ✅ Duplicate subscriptions cleaned up
4. ✅ Failed subscriptions removed

### During Test Run (Expected Behavior)
With the modified script:

**For + Suffix Operators (5):**
- lvms-operator+: Fresh install (no existing subscription detected)
- odf-operator+: Fresh install (no existing subscription detected)
- ocs-operator+: Fresh install (no existing subscription detected)
- advanced-cluster-management+: Fresh install (no existing subscription detected)
- multicluster-engine+: Fresh install (no existing subscription detected)

**For All Other Operators (47):**
- Fresh install for all

**Expected Failures:**
- jaeger: Package not found (deprecated in OCP 4.20)
- Possibly odf-csi-addons-operator and mcg-operator if namespace conflicts still occur

**Expected Success Rate:** 50-51/52 (96-98%)

---

## BENEFITS OF CLEAN START

✅ **No duplicate subscriptions** - fresh install for all operators
✅ **No OLM conflicts** - no pre-existing subscriptions to cause ResolutionFailed
✅ **CSV detection works reliably** - no stale CSVs or subscription state issues
✅ **Consistent test results** - same starting state for all tests
✅ **Tests all operators equally** - even + suffix operators get fresh install

---

## SCRIPT LOCATION

**RDU2:** `/tmp/cleanup-all-test-operators.sh`

### To Run Cleanup Again
```bash
ssh rdu2 'bash /tmp/cleanup-all-test-operators.sh'
```

---

## FILES CREATED

**Cleanup Script:**
- Location: `/tmp/cleanup-all-test-operators.sh`
- Purpose: Delete all test operators before test run
- Status: ✅ Tested and working

**Documentation:**
- This file: `/tmp/pre-test-cleanup-complete.md`
- Cleanup summary and verification

---

## READY FOR TESTING

The cluster is now clean and ready for a fresh test run:

```bash
# To run full test suite
ssh rdu2 'cd /root/test-rose/certsuite && ./run-ocp-4.20-test-v2.sh'
```

**Expected improvements with clean cluster + script fixes:**
1. CSV name fix → all 9 operators with mismatches will pass
2. Skip duplicate install fix → no duplicate subscriptions for + operators
3. Clean starting state → no pre-existing conflicts
4. Expected success rate: **96-98%** (50-51/52 operators)

---

**Cleanup Completed:** February 3, 2026 10:57 AM EST
**Verification:** ✅ PASSED
**Status:** Ready for testing
