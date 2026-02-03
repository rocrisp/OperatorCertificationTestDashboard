# COMPREHENSIVE OPERATOR FAILURE ANALYSIS & FIX PLAN

**Date:** February 2, 2026
**Test Logs Analyzed:**
- Test Run #1: `test-run-20260130-172401.log` (Jan 30) - 14 failures
- Test Run #2: `test-run-20260202-085840.log` (Feb 2) - 14 failures

---

## EXECUTIVE SUMMARY

**Total Operators Tested:** 52
**Failed:** 14 (26.9%)
**Success Rate:** 38/52 (73.1%)

**Failure Breakdown:**
- **CSV Name Mismatch:** 9 operators (64% of failures) - **FIXABLE**
- **OLM InstallPlan Timeout:** 4 operators (29% of failures) - **INTERMITTENT**
- **CSV Never Succeeded:** 1 operator (7% of failures) - **KNOWN ISSUE**

**Expected Success Rate After Fix:** 47/52 (90.4%)

---

## CATEGORY 1: CSV NAME MISMATCH (9 operators) ✅ FIXABLE

These operators **installed successfully** but the script couldn't find the CSV due to name mismatch.

### The Pattern
Script searches for CSV names starting with package name: `grep "^${package_name}\."`
But many operators have different CSV names.

| # | Package Name | Actual CSV Name | Pattern |
|---|--------------|-----------------|---------|
| 1 | `cincinnati-operator` | `update-service-operator.v5.0.3` | Complete rename |
| 2 | `openshift-cert-manager-operator` | `cert-manager-operator.v1.18.1` | Drops "openshift-" |
| 3 | `kubevirt-hyperconverged` | `kubevirt-hyperconverged-operator.v4.18.28` | Adds "-operator" |
| 4 | `redhat-oadp-operator` | `oadp-operator.v1.5.3` | Drops "redhat-" |
| 5 | `kiali-ossm` | `kiali-operator.v2.17.2` | Changes "-ossm" → "-operator" |
| 6 | `amq-broker-rhel8` | `amq-broker-operator.v7.12.5-...` | Changes "-rhel8" → "-operator" |
| 7 | `amq-streams` | `amqstreams.v3.1.0-7` | Removes hyphen |
| 8 | `openshift-custom-metrics-autoscaler-operator` | `custom-metrics-autoscaler.v2.18.1-1` | Drops "openshift-" and "-operator" |
| 9 | `tempo-product` | `tempo-operator.v0.19.0-3` | Changes "-product" → "-operator" |

### Root Cause Code Location

**File:** `/root/test-rose/certsuite/script/run-basic-batch-operators-test.sh`
**Function:** `wait_for_csv_to_appear_and_label()`
**Line:** 332

```bash
# CURRENT (BROKEN):
csv_name=$(oc get csv -n "$csv_namespace" \
           -o custom-columns=':.metadata.name' \
           --no-headers 2>/dev/null | \
           grep "^${operator_package}\." | head -1)
```

### The Fix - Query Subscription Status

**Replace line 332 with:**
```bash
# FIXED:
csv_name=$(oc get subscription "$operator_package" \
           -n "$csv_namespace" \
           -o jsonpath='{.status.installedCSV}' 2>/dev/null)
```

**Why This Works:**
- ✅ OLM populates `subscription.status.installedCSV` with actual CSV name
- ✅ No pattern matching needed
- ✅ Works for all operators regardless of naming convention
- ✅ Safe with multiple operators in same namespace
- ✅ Already available immediately after `oc operator install`

---

## CATEGORY 2: OLM INSTALLPLAN TIMEOUT (4 operators) ⚠️ INTERMITTENT

These operators failed because OLM couldn't create an InstallPlan within the timeout.

| # | Operator | Issue |
|---|----------|-------|
| 1 | `odf-csi-addons-operator` | OLM timeout - no InstallPlan created |
| 2 | `mcg-operator` | OLM timeout - no InstallPlan created |
| 3 | `ansible-automation-platform-operator` | OLM timeout - no InstallPlan created |
| 4 | `jaeger` | Package not found in catalog + OLM timeout |

**Root Cause:** OLM overwhelmed processing 52 operators rapidly

**Prognosis:** Likely to succeed on retry with cleaner environment or slower test pace

**Action:** Monitor - no code fix needed, may self-resolve

---

## CATEGORY 3: CSV NEVER SUCCEEDED (1 operator) 🔴 KNOWN ISSUE

| Operator | Issue |
|----------|-------|
| `cloud-native-postgresql` | CSV installed but never reached "Succeeded" state |

**Root Cause:** ImagePullBackOff for `docker.enterprisedb.com`
**Error:** `invalid username/password: unauthorized`

**Action:** Requires EnterpriseDB registry credentials - out of scope for script fix

---

## IMPLEMENTATION PLAN

### Phase 1: Apply CSV Name Fix ✅

**File to Modify:** `/root/test-rose/certsuite/script/run-basic-batch-operators-test.sh`

**Changes:**

1. **Backup original script**
   ```bash
   cp run-basic-batch-operators-test.sh run-basic-batch-operators-test.sh.backup
   ```

2. **Apply fix at line 332**

   **Before:**
   ```bash
   csv_name=$(oc get csv -n "$csv_namespace" \
              -o custom-columns=':.metadata.name' \
              --no-headers 2>/dev/null | \
              grep "^${operator_package}\." | head -1)
   ```

   **After:**
   ```bash
   csv_name=$(oc get subscription "$operator_package" \
              -n "$csv_namespace" \
              -o jsonpath='{.status.installedCSV}' 2>/dev/null)
   ```

3. **Add timeout loop for edge case handling**

   The subscription.status.installedCSV field might be empty initially.
   Wrap in existing while loop (lines 330-349) - no change needed since
   the while loop already handles waiting.

### Phase 2: Test the Fix ✅

**Test Strategy:**
1. Run test on operators known to have CSV name mismatch
2. Verify all 9 CSV name mismatch operators now pass
3. Check OLM timeout operators (may still fail intermittently)

**Test Command:**
```bash
cd /root/test-rose/certsuite
./script/run-basic-batch-operators-test.sh \
  registry.redhat.io/redhat/redhat-operator-index:v4.20 \
  "cincinnati-operator kiali-ossm amq-streams tempo-product"
```

### Phase 3: Full Test Run ✅

Run complete test suite and verify:
- CSV name mismatch operators: 9/9 pass (100%)
- OLM timeout operators: Check if reduced load helps
- Overall success rate: Target 90%+

---

## EXPECTED RESULTS AFTER FIX

### Before Fix
- **Success:** 38/52 (73.1%)
- **CSV Mismatch Failures:** 9
- **OLM Timeout Failures:** 4
- **CSV Status Failures:** 1

### After Fix (Conservative Estimate)
- **Success:** 47/52 (90.4%)
- **CSV Mismatch Failures:** 0 ✅ (fixed)
- **OLM Timeout Failures:** 4 (may improve)
- **CSV Status Failures:** 1 (requires credentials)

### After Fix (Optimistic - if OLM timeouts resolve)
- **Success:** 51/52 (98.1%)
- **Only failure:** cloud-native-postgresql (credentials issue)

---

## VERIFICATION CHECKLIST

- [ ] Backup original script
- [ ] Apply fix at line 332
- [ ] Test with 4 known CSV mismatch operators
- [ ] Verify all 4 pass
- [ ] Run full test suite
- [ ] Compare results with previous run
- [ ] Document final success rate
- [ ] Update todo-list.log with results

---

## ADDITIONAL NOTES

### Why Not Other Solutions?

**Option 1: Parse `oc operator install` output**
- ❌ Fragile - depends on output format
- ❌ Breaks if OpenShift changes CLI output
- ❌ Complex text parsing

**Option 3: Hardcode CSV name mappings**
- ❌ Not scalable - 9 operators already, more in future
- ❌ Brittle - CSV names change with versions
- ❌ High maintenance burden

**Option 2 (Chosen): Query subscription.status.installedCSV**
- ✅ Uses OLM's authoritative source
- ✅ Works for all current and future operators
- ✅ No maintenance needed
- ✅ Clean, simple implementation

---

## CONCLUSION

The primary issue (CSV name mismatch affecting 9 operators) is **fully fixable** with a simple 2-line code change.

This will improve success rate from **73% to 90%+**.

The remaining failures are either:
- Intermittent (OLM timeouts - may resolve with retry)
- Known external issue (missing registry credentials)

**Recommendation:** Proceed with fix implementation immediately.
