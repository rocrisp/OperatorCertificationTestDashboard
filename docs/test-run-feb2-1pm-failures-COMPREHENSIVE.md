# OPERATOR INSTALLATION FAILURE ANALYSIS
**Test Run:** test-run-FIXED-20260202-130319.log
**Date:** February 2, 2026 - 1:03 PM EST
**Script Version:** ENHANCED FIX (subscription status query + fallback grep)
**Log Location:** `/root/test-rose/certsuite/test-run-FIXED-20260202-130319.log`

---

## EXECUTIVE SUMMARY

**Total Operators Tested:** 52
**Successful Installations:** 47 (90.4%)
**Failed Installations:** 5 (9.6%)

**Test Improvement vs Previous Runs:**
- Previous success rate (Feb 2 AM): 38/52 (73.1%)
- Current success rate (Feb 2 PM): 47/52 (90.4%)
- **Improvement: +17.3 percentage points** ✅

**CSV Name Fix Status:** ✅ **WORKING**
- All 9 operators with CSV name mismatches now pass
- Enhanced fix (subscription + fallback grep) functioning correctly

---

## FAILED OPERATORS BREAKDOWN

### Failure Categories:
1. **+ Suffix Operator Conflicts**: 1 operator (ocs-operator+)
2. **Shared Namespace Subscription Failures**: 2 operators (odf-csi-addons-operator, mcg-operator)
3. **Package Not Found**: 1 operator (jaeger)
4. **CSV Status Never Succeeded**: 1 operator (cloud-native-postgresql)

---

## DETAILED FAILURE ANALYSIS

### 1. ocs-operator+ ❌
**Status:** Failed to install
**Namespace:** openshift-storage (shared)
**Category:** + Suffix Operator - Subscription Already Exists

**Timeline:**
- Package has + suffix: will skip cleanup for ocs-operator
- Using openshift-storage namespace (existing)
- Skipping namespace creation (using existing namespace)
- **Issue:** "Operator subscription already exists (expected with + suffix), continuing..."
- Waited 100 seconds for CSV to appear
- **Timeout:** CSV never appeared
- **Result:** Operator failed to install

**Root Cause:**
The + suffix indicates this operator should remain installed after testing. The subscription already exists from a previous installation, but when attempting to re-test, the CSV never appears. This suggests:
- The subscription exists but has no installedCSV populated
- OLM conflict in the shared openshift-storage namespace
- The operator may be in ResolutionFailed state

**Why Enhanced Fix Didn't Help:**
- subscription.status.installedCSV is likely empty (`<none>`)
- Fallback grep also found no CSV (CSV doesn't exist in cluster)
- Root issue is OLM can't create the CSV, not detection

**Fix Needed:**
Check subscription status for ResolutionFailed and report specific OLM error

---

### 2. odf-csi-addons-operator ❌
**Status:** Failed to install
**Namespace:** openshift-storage (shared)
**Category:** Shared Namespace Subscription Conflict

**Timeline:**
- Using openshift-storage namespace
- **Issue:** "Operator installation failed but will still waiting for CSV"
- Waited 100 seconds for CSV to appear
- **Timeout:** CSV never appeared
- **Result:** Operator failed to install

**Root Cause:**
The operator installation command (`oc operator install`) failed, but the script continued waiting for CSV anyway. Looking at previous analysis:
- Subscription creation failed
- OLM conflict due to multiple operators in openshift-storage
- ResolutionFailed status preventing CSV installation

**Error Pattern:**
```
install operator
[31mOperator installation failed but will still waiting for CSV[0m
Waiting for csv for odf-csi-addons-operator...
[repeated 20 times]
Timeout reached 100 seconds
```

**Why It Failed:**
- openshift-storage already hosts: lvms-operator+, odf-operator+, ocs-operator+
- OperatorGroup conflicts prevent new subscriptions
- OLM dependency resolution fails

**Fix Needed:**
Either exclude operators that require openshift-storage, or check subscription.status.conditions for ResolutionFailed

---

### 3. mcg-operator ❌
**Status:** Failed to install
**Namespace:** openshift-storage (shared)
**Category:** Shared Namespace Subscription Conflict

**Timeline:**
- Using openshift-storage namespace
- **Issue:** "Operator installation failed but will still waiting for CSV"
- Waited 100 seconds for CSV to appear
- **Timeout:** CSV never appeared
- **Result:** Operator failed to install

**Root Cause:**
Same issue as odf-csi-addons-operator:
- Subscription creation failed
- OLM ResolutionFailed due to conflicts in shared namespace
- No CSV ever created

**Error Pattern:**
```
install operator
[31mOperator installation failed but will still waiting for CSV[0m
Waiting for csv for mcg-operator...
[repeated 20 times]
Timeout reached 100 seconds
```

**Why It Failed:**
- MCG (Multicloud Object Gateway) is part of ODF (OpenShift Data Foundation)
- openshift-storage already has conflicting operators
- OLM can't resolve dependencies

**Fix Needed:**
Same as odf-csi-addons-operator - check for ResolutionFailed

---

### 4. jaeger ❌
**Status:** Failed to install
**Namespace:** test-operator
**Category:** Package Not Found in Catalog

**Timeline:**
- Wait for package jaeger to be reachable
- **Issue:** Package manifest never found
- Waited 600 seconds (10 minutes)
- **Timeout:** Package not found
- **Result:** Operator installation failed

**Error Pattern:**
```
Wait for package jaeger to be reachable
Waiting for package jaeger to be reachable...
[repeated 120 times - 5 second intervals]
Timeout reached 600 seconds
Operator installation failed but will still waiting for CSV
```

**Root Cause:**
The jaeger package does NOT exist in the OpenShift 4.20 catalog:
```bash
oc get packagemanifest jaeger -n openshift-marketplace
Error from server (NotFound): packagemanifests.packages.operators.coreos.com "jaeger" not found
```

**Replacement:**
- Jaeger has been deprecated in OCP 4.20
- Replaced by **tempo-product** (Tempo Operator)
- Test list includes both jaeger (old) and tempo-product (new)

**Fix Needed:**
Remove "jaeger" from test operator list for OCP 4.20+

---

### 5. cloud-native-postgresql ❌
**Status:** CSV installed but never reached Succeeded
**Namespace:** test-operator
**Category:** CSV Status Timeout

**Timeline:**
- Operator subscription created successfully
- CSV appeared: `cloud-native-postgresql.v1.25.1`
- CSV labeled successfully
- **Issue:** Waiting for CSV to reach "Succeeded" status
- **Timeout:** After 60 retries (600 seconds), CSV still not Succeeded
- **Result:** Operator failed (CSV status timeout)

**Error Pattern:**
```
Wait for CSV to be succeeded
[retrying 60 times with 10-second intervals]
CSV never reached Succeeded status
```

**Root Cause (from previous analysis):**
ImagePullBackOff for EnterpriseDB registry:
```
Error: ImagePullBackOff
Image: docker.enterprisedb.com/postgresql/postgresql:16
Error: invalid username/password: unauthorized
```

**Why It Failed:**
- Requires credentials for `docker.enterprisedb.com`
- No pull secret configured for EnterpriseDB registry
- Pods can't pull images, so CSV can't succeed

**Fix Needed:**
- Requires EnterpriseDB registry credentials (out of scope for script fix)
- OR exclude from test list (known external dependency)

---

## PATTERNS AND INSIGHTS

### ✅ What's Working (CSV Name Fix)

The enhanced fix successfully resolved **ALL 9 operators** with CSV name mismatches:

| Operator | Previous Result | Current Result |
|----------|----------------|----------------|
| cincinnati-operator | ❌ CSV timeout | ✅ Passed |
| openshift-cert-manager-operator | ❌ CSV timeout | ✅ Passed |
| kubevirt-hyperconverged | ❌ CSV timeout | ✅ Passed |
| redhat-oadp-operator | ❌ CSV timeout | ✅ Passed |
| kiali-ossm | ❌ CSV timeout | ✅ Passed |
| amq-broker-rhel8 | ❌ CSV timeout | ✅ Passed |
| amq-streams | ❌ CSV timeout | ✅ Passed |
| openshift-custom-metrics-autoscaler-operator | ❌ CSV timeout | ✅ Passed |
| tempo-product | ❌ CSV timeout | ✅ Passed |

**Enhanced Fix Code (working correctly):**
```bash
# Try to get CSV name from subscription status first
csv_name=$(oc get subscription "$operator_package" \
           -n "$csv_namespace" \
           -o jsonpath='{.status.installedCSV}' 2>/dev/null)

# If subscription.status.installedCSV is empty, fall back to grep
if [ -z "$csv_name" ] || [ "$csv_name" = "<none>" ]; then
    csv_name=$(oc get csv -n "$csv_namespace" \
               -o custom-columns=':.metadata.name' \
               --no-headers 2>/dev/null | \
               grep -i "$operator_package" | head -1)
fi
```

### ❌ What's Still Failing

**60% of failures (3/5) are in openshift-storage namespace:**
- ocs-operator+ (subscription already exists, no CSV)
- odf-csi-addons-operator (subscription creation failed)
- mcg-operator (subscription creation failed)

**Common Pattern:**
All three operators attempt to use the shared `openshift-storage` namespace, which already hosts multiple `+` suffix operators (lvms-operator+, odf-operator+). This creates OperatorGroup and subscription conflicts.

---

## RECOMMENDATIONS

### 1. Improve openshift-storage Conflict Detection ⚠️

**Problem:** 3 operators fail due to shared namespace conflicts
**Solution:** Check subscription.status.conditions for ResolutionFailed

**Proposed Enhancement:**
```bash
# After operator install, check subscription status
sub_status=$(oc get subscription "$operator_package" -n "$csv_namespace" \
             -o jsonpath='{.status.conditions[?(@.type=="ResolutionFailed")].message}' 2>/dev/null)

if [ -n "$sub_status" ]; then
    echo_color "$RED" "Subscription ResolutionFailed: $sub_status"
    echo_color "$RED" "OLM cannot resolve dependencies - likely namespace conflict"
    return 1
fi
```

### 2. Remove Deprecated Operators ✅

**Problem:** jaeger package doesn't exist in OCP 4.20
**Solution:** Remove from test list

**Action:**
```bash
# Remove jaeger from operator list (deprecated in OCP 4.20)
# tempo-product is the replacement
```

### 3. Handle External Dependencies 📋

**Problem:** cloud-native-postgresql requires external registry credentials
**Solution:** Document as known limitation OR exclude from automated tests

**Options:**
- Add to exclusion list for tests without EnterpriseDB credentials
- Document in test prerequisites

### 4. Increase Timeout for + Operators (Optional) 🕐

**Problem:** ocs-operator+ times out at 100 seconds
**Consideration:** + suffix operators may need longer to reconcile

**Proposed:**
```bash
# Increase timeout for + suffix operators
if [[ "$operator_package" == *"+" ]]; then
    timeout_seconds=300  # 5 minutes for + operators
else
    timeout_seconds=100  # Standard timeout
fi
```

---

## SUCCESS METRICS

**Before CSV Name Fix (Feb 2 AM):**
- Success: 38/52 (73.1%)
- CSV name mismatch failures: 9
- OLM timeout failures: 4
- Other failures: 1

**After CSV Name Fix (Feb 2 PM - THIS TEST):**
- Success: 47/52 (90.4%)
- CSV name mismatch failures: 0 ✅
- Shared namespace conflicts: 3
- Package not found: 1
- External dependency: 1

**Impact:**
- **+9 operators fixed** (CSV name mismatch)
- **+17.3 percentage point improvement**
- Script enhancement working as designed ✅

---

## NEXT STEPS

1. ✅ **CSV Name Fix:** COMPLETE - All 9 operators now passing
2. ⚠️ **Shared Namespace Conflicts:** Add ResolutionFailed detection
3. ✅ **Remove jaeger:** Update test list for OCP 4.20
4. 📋 **Document cloud-native-postgresql:** Mark as requiring external credentials
5. 🔄 **Re-run Test:** Validate ResolutionFailed detection with updated script

---

## VERIFICATION COMMANDS

Check subscription status for failed operators:
```bash
# Check ocs-operator+ subscription
oc get subscription ocs-operator -n openshift-storage -o yaml

# Check for ResolutionFailed
oc get subscription ocs-operator -n openshift-storage \
   -o jsonpath='{.status.conditions[?(@.type=="ResolutionFailed")]}'

# Check odf-csi-addons-operator
oc get subscription odf-csi-addons-operator -n openshift-storage -o yaml

# Verify jaeger doesn't exist
oc get packagemanifest jaeger -n openshift-marketplace
```

---

**Report Generated:** February 2, 2026
**Test Log:** `/root/test-rose/certsuite/test-run-FIXED-20260202-130319.log`
**Report Location:** `/tmp/test-run-feb2-1pm-failures-COMPREHENSIVE.md`
