# Test Run Failure Analysis - February 2, 2026 1:03 PM

## Executive Summary

- **Test Log**: `/root/test-rose/certsuite/test-run-FIXED-20260202-130319.log` on rdu2
- **Test Configuration**: ENHANCED FIX (subscription status query + fallback to grep)
- **Total Operators Tested**: 52 unique operators
- **Total Successful Installations**: 47 operators (90.4% success rate)
- **Total Failed Installations**: 5 operators (9.6% failure rate)
- **Test Duration**: 159m 13.868s (2 hours 39 minutes)

## Failed Operators Summary

| # | Operator Name | Namespace | Catalog Index | Failure Type |
|---|---------------|-----------|---------------|--------------|
| 1 | ocs-operator+ | openshift-storage | redhat-operator-index:v4.20 | CSV Timeout (+ suffix) |
| 2 | odf-csi-addons-operator | openshift-storage | redhat-operator-index:v4.20 | Subscription Creation + CSV Timeout |
| 3 | mcg-operator | openshift-storage | redhat-operator-index:v4.20 | Subscription Creation + CSV Timeout |
| 4 | jaeger | test-operator | redhat-operator-index:v4.20 | Package Not Found + CSV Timeout |
| 5 | cloud-native-postgresql | test-operator | certified-operator-index:v4.20 | CSV Status Timeout (Max Retries) |

---

## Detailed Failure Analysis

### 1. ocs-operator+ (OpenShift Container Storage)

**Package**: `ocs-operator+`  
**Namespace**: `openshift-storage`  
**Catalog**: `registry.redhat.io/redhat/redhat-operator-index:v4.20`  
**Has + Suffix**: Yes (indicates persistent operator, cleanup skipped)

#### Failure Timeline
1. Operator has `+` suffix, so cleanup is skipped
2. Subscription already exists (expected with `+` suffix)
3. Script attempts to wait for CSV to appear
4. Waited 100 seconds for CSV `ocs-operator` to be created
5. **Timeout reached** - CSV never appeared

#### Error Messages
```
[36mOperator subscription already exists (expected with + suffix), continuing...[0m
[36mWait for CSV to appear and label resources under test[0m
[36mWaiting for csv for ocs-operator to be created in namespace openshift-storage ...[0m
(repeated 19 times, 5 seconds each = 100 seconds)
[36mTimeout reached 100 seconds waiting for CSV for ocs-operator.[0m
[31mOperator failed to install, continue[0m
```

#### Root Cause
**Shared Namespace Conflict with + Suffix Operator**

The `ocs-operator+` uses the shared `openshift-storage` namespace which already has multiple operators installed:
- `lvms-operator+` (installed earlier)
- `odf-operator+` (installed earlier)
- Other storage-related CSVs

When the subscription already exists (from previous `+` suffix installation), the CSV may not be created/updated as expected, or it may have a different name than what the script is looking for.

#### Additional Context
- Previous uninstall showed rate limiter error: `delete rule "ocp4-file-groupowner-multus-conf": client rate limiter Wait returned an error: rate: Wait(n=1) would exceed context deadline`
- Multiple CSVs exist in the namespace but weren't labeled for this test run

---

### 2. odf-csi-addons-operator (OpenShift Data Foundation CSI Addons)

**Package**: `odf-csi-addons-operator`  
**Namespace**: `openshift-storage`  
**Catalog**: `registry.redhat.io/redhat/redhat-operator-index:v4.20`  
**Has + Suffix**: No

#### Failure Timeline
1. Uses suggested namespace `openshift-storage` (shared namespace)
2. Skips namespace creation (already exists)
3. Attempts to install operator
4. **Operator installation failed** (subscription creation issue)
5. Script continues to wait for CSV anyway
6. Waited 100 seconds for CSV to appear
7. **Timeout reached** - CSV never appeared

#### Error Messages
```
[36musing openshift-storage namespace for odf-csi-addons-operator[0m
[90mnamespace= openshift-storage[0m
[36mCluster cleanup[0m
[36mSkipping namespace creation for openshift-storage (using existing namespace)[0m
[36minstall operator[0m
[31mOperator installation failed but will still waiting for CSV[0m
[36mWait for CSV to appear and label resources under test[0m
[36mWaiting for csv for odf-csi-addons-operator to be created in namespace openshift-storage ...[0m
(repeated 19 times)
[36mTimeout reached 100 seconds waiting for CSV for odf-csi-addons-operator.[0m
[31mOperator failed to install, continue[0m
```

#### Root Cause
**Subscription Creation Failure in Shared Namespace**

The operator installation step failed (likely during subscription or operatorgroup creation) in the shared `openshift-storage` namespace. Possible causes:
- Operatorgroup conflict (namespace may already have an operatorgroup from `+` suffix operators)
- Subscription conflict or OLM resource contention
- The script reports "Operator installation failed" which indicates the `install_operator` function returned an error

The ENHANCED FIX's subscription status query may have detected an issue, but the script continued to wait for CSV as designed.

---

### 3. mcg-operator (Multi-Cloud Gateway Operator)

**Package**: `mcg-operator`  
**Namespace**: `openshift-storage`  
**Catalog**: `registry.redhat.io/redhat/redhat-operator-index:v4.20`  
**Has + Suffix**: No

#### Failure Timeline
1. Uses `openshift-storage` namespace (shared namespace)
2. Skips namespace creation (already exists)
3. Attempts to install operator
4. **Operator installation failed** (subscription creation issue)
5. Script continues to wait for CSV anyway
6. Waited 100 seconds for CSV to appear
7. **Timeout reached** - CSV never appeared

#### Error Messages
```
[36musing openshift-storage namespace for mcg-operator[0m
[90mnamespace= openshift-storage[0m
[36mCluster cleanup[0m
[36mSkipping namespace creation for openshift-storage (using existing namespace)[0m
[36minstall operator[0m
[31mOperator installation failed but will still waiting for CSV[0m
[36mWait for CSV to appear and label resources under test[0m
[36mWaiting for csv for mcg-operator to be created in namespace openshift-storage ...[0m
(repeated 19 times)
[36mTimeout reached 100 seconds waiting for CSV for mcg-operator.[0m
[31mOperator failed to install, continue[0m
```

#### Root Cause
**Subscription Creation Failure in Shared Namespace**

Same root cause as `odf-csi-addons-operator` - the operator installation failed in the shared `openshift-storage` namespace. The namespace already contains multiple storage operators with `+` suffix, likely causing operatorgroup or subscription conflicts.

---

### 4. jaeger (Jaeger Tracing Operator)

**Package**: `jaeger`  
**Namespace**: `test-operator`  
**Catalog**: `registry.redhat.io/redhat/redhat-operator-index:v4.20`  
**Has + Suffix**: No

#### Failure Timeline
1. Waits for package manifest to be reachable
2. Waited 600 seconds (60 retries × 10 seconds) for packagemanifest
3. **Package not found** - packagemanifest `jaeger` does not exist in catalog
4. Continues with installation attempt anyway
5. Creates new namespace `test-operator`
6. **Operator installation failed** (no package to install)
7. Waited 100 seconds for CSV to appear
8. **Timeout reached** - CSV never appeared (package doesn't exist)

#### Error Messages
```
[36mWait for package jaeger to be reachable[0m
[36mWaiting for package jaeger to be reachable...[0m
(repeated 60 times, 10 seconds each = 600 seconds)
[36mTimeout reached 600 seconds waiting for packagemanifest jaeger to be reachable.[0m
Error from server (NotFound): packagemanifests.packages.operators.coreos.com "jaeger" not found
[36mno suggested namespace for jaeger, using: test-operator[0m
[90mnamespace= test-operator[0m
[36mCluster cleanup[0m
[36mRemove namespace if present[0m
namespace/test-operator created
[36minstall operator[0m
[31mOperator installation failed but will still waiting for CSV[0m
[36mWait for CSV to appear and label resources under test[0m
[36mWaiting for csv for jaeger to be created in namespace test-operator ...[0m
(repeated 19 times)
[36mTimeout reached 100 seconds waiting for CSV for jaeger.[0m
[31mOperator failed to install, continue[0m
```

#### Root Cause
**Package Not Available in Catalog**

The `jaeger` package does not exist in the `redhat-operator-index:v4.20` catalog. This is a legitimate package availability issue - the operator may have been:
- Deprecated or removed from OCP 4.20
- Renamed (e.g., to `jaeger-product` or integrated into service mesh)
- Moved to a different catalog

The script correctly detected the package is not found but continued with the installation attempt (as designed to be resilient).

---

### 5. cloud-native-postgresql (CloudNative PostgreSQL Operator)

**Package**: `cloud-native-postgresql`  
**Namespace**: `test-operator`  
**Catalog**: `registry.redhat.io/redhat/certified-operator-index:v4.20`  
**Has + Suffix**: No

#### Failure Timeline
1. Package manifest found successfully
2. Creates new namespace `test-operator`
3. Creates operatorgroup successfully
4. Creates subscription successfully
5. **Subscription shows CSV installed**: `cloud-native-postgresql.v1.28.0`
6. CSV is labeled successfully
7. Waits for CSV to reach "Succeeded" status
8. Retried 60 times waiting for CSV status (10 seconds each = 600 seconds)
9. **Maximum retries reached** - CSV never reached "Succeeded" status
10. Operator marked as failed

#### Error Messages
```
[36minstall operator[0m
operatorgroup "test-operator" created
subscription "cloud-native-postgresql" created
operator "cloud-native-postgresql" installed; installed csv is "cloud-native-postgresql.v1.28.0"
[36mWait for CSV to appear and label resources under test[0m
[90mLabeling CSV: cloud-native-postgresql.v1.28.0[0m
clusterserviceversion.operators.coreos.com/cloud-native-postgresql.v1.28.0 labeled
[36mWait for CSV to be succeeded[0m
[90mRetry 1/60: Waiting for a few seconds before the next attempt...[0m
[90mRetry 2/60: Waiting for a few seconds before the next attempt...[0m
...
[90mRetry 60/60: Waiting for a few seconds before the next attempt...[0m
[90mMaximum retries reached.[0m
[31mOperator failed to install, continue[0m
```

#### Root Cause
**CSV Status Never Reached "Succeeded"**

This is a different type of failure - the operator subscription and CSV were created successfully, but the CSV never transitioned to the "Succeeded" phase. Possible causes:
- Pod scheduling issues (resource constraints, node selectors)
- Image pull failures
- CRD installation issues
- Webhook configuration problems
- Missing RBAC permissions
- Dependent resources not available

The ENHANCED FIX's subscription status monitoring would have detected this, but the CSV itself is stuck in a non-succeeded state (likely "Installing" or "Pending").

---

## Failure Type Categorization

### CSV Timeout Failures (3 operators)
Operators where the CSV never appeared after subscription creation:
1. **ocs-operator+** - Shared namespace with existing subscription
2. **odf-csi-addons-operator** - Subscription creation failed in shared namespace
3. **mcg-operator** - Subscription creation failed in shared namespace

### Package Not Found Failures (1 operator)
Operators not available in the specified catalog:
1. **jaeger** - Package does not exist in redhat-operator-index:v4.20

### CSV Status Timeout Failures (1 operator)
Operators where CSV was created but never reached "Succeeded" status:
1. **cloud-native-postgresql** - CSV stuck in non-succeeded phase

---

## Patterns and Insights

### Shared Namespace Issues (openshift-storage)
**3 out of 5 failures** occurred in the `openshift-storage` namespace:
- This namespace is used by multiple storage operators with `+` suffix
- `+` suffix operators (lvms-operator, odf-operator, ocs-operator) persist across test runs
- Non-`+` suffix operators attempting to use the same namespace fail
- Likely due to operatorgroup conflicts or existing subscriptions

**Operators that succeeded in openshift-storage:**
- lvms-operator+ (has `+` suffix)
- odf-operator+ (has `+` suffix)

**Operators that failed in openshift-storage:**
- ocs-operator+ (subscription already exists, CSV timeout)
- odf-csi-addons-operator (subscription creation failed)
- mcg-operator (subscription creation failed)

### ENHANCED FIX Behavior
The ENHANCED FIX (subscription status query + fallback to grep) appears to be working:
- It detected installation failures for odf-csi-addons-operator, mcg-operator, and jaeger
- Script correctly reported "Operator installation failed but will still waiting for CSV"
- Script continued to wait for CSV as designed (resilient behavior)
- cloud-native-postgresql shows the subscription status was successfully queried (operator installed, CSV created)

### Package Availability
- **jaeger** is not available in redhat-operator-index:v4.20
- May need to update the operator list or catalog source for this operator

---

## Recommendations

### 1. Shared Namespace Handling
**Problem**: Multiple operators using `openshift-storage` namespace causing conflicts

**Solutions**:
- Add special handling for `openshift-storage` namespace
- Check for existing operatorgroups before creating new ones
- Consider using AllNamespaces install mode for shared namespace operators
- Document which operators share namespaces and test them in order

### 2. Subscription Already Exists (+ Suffix Operators)
**Problem**: ocs-operator+ has existing subscription but CSV doesn't appear

**Solutions**:
- For `+` suffix operators with existing subscriptions, query the existing CSV name first
- Don't create new subscription if one already exists
- Use `oc get subscription <name> -o jsonpath='{.status.currentCSV}'` to find CSV
- Consider patching subscription instead of creating new one

### 3. Package Not Found Handling
**Problem**: jaeger package doesn't exist in catalog

**Solutions**:
- Update operator list to remove deprecated operators
- Check package availability before adding to test suite
- Add validation step to verify package exists in catalog before testing
- Document operator catalog mappings

### 4. CSV Status Debugging
**Problem**: cloud-native-postgresql CSV never reaches Succeeded

**Solutions**:
- Add CSV status condition details to logs (`.status.conditions`)
- Check pod status for operator deployments
- Log reasons for CSV failures (`.status.reason`, `.status.message`)
- Add timeout threshold configuration (600s may not be enough for some operators)

### 5. Enhanced Error Logging
**Current issue**: "Operator installation failed" doesn't show root cause

**Solutions**:
- Capture and log stderr from install_operator function
- Add subscription status details to failure messages
- Log operatorgroup conflicts
- Show OLM error messages from subscription status

---

## Test Run Statistics

### Overall Success Rate
- **Total Operators**: 52
- **Successful**: 47 (90.4%)
- **Failed**: 5 (9.6%)

### Failure Breakdown by Type
- **CSV Timeout**: 3 operators (60% of failures)
- **Package Not Found**: 1 operator (20% of failures)
- **CSV Status Timeout**: 1 operator (20% of failures)

### Namespace Distribution of Failures
- **openshift-storage**: 3 failures (shared namespace issues)
- **test-operator**: 2 failures (1 package not found, 1 CSV status timeout)

### Catalog Distribution
- **redhat-operator-index:v4.20**: 4 failures
- **certified-operator-index:v4.20**: 1 failure

---

## Appendix: Failed Operators Quick Reference

### Quick Command to Check Operator Status on Cluster

```bash
# Check ocs-operator subscription and CSV
oc get subscription -n openshift-storage ocs-operator -o yaml
oc get csv -n openshift-storage | grep ocs-operator

# Check odf-csi-addons-operator
oc get subscription -n openshift-storage odf-csi-addons-operator -o yaml
oc get csv -n openshift-storage | grep odf-csi-addons

# Check mcg-operator
oc get subscription -n openshift-storage mcg-operator -o yaml
oc get csv -n openshift-storage | grep mcg

# Check if jaeger package exists
oc get packagemanifest jaeger

# Check cloud-native-postgresql CSV status
oc get csv -n test-operator cloud-native-postgresql.v1.28.0 -o yaml
```

---

**Report Generated**: February 2, 2026  
**Analysis By**: Automated Test Log Analysis  
**Log File**: `/root/test-rose/certsuite/test-run-FIXED-20260202-130319.log` on rdu2 host  
**Test Configuration**: ENHANCED FIX (subscription status query + fallback to grep)
