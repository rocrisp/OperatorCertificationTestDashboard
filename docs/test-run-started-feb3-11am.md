# FULL OPERATOR TEST RUN STARTED

**Start Time:** February 3, 2026 11:01 AM EST
**Tmux Session:** operator-test
**Test Script:** /root/test-rose/certsuite/run-ocp-4.20-test-v2.sh
**Total Operators:** 52 (50 Red Hat + 2 Certified)

---

## TEST CONFIGURATION

### Script Modifications Applied

1. **CSV Name Fix** ✅
   - Line 332-339: Query subscription.status.installedCSV
   - Fallback to grep if subscription status is empty
   - Fixes 9 operators with CSV name mismatches

2. **Skip Duplicate Install Fix** ✅
   - Line 713-744: Check for existing subscriptions before installing + operators
   - Prevents duplicate subscriptions
   - Avoids OLM ResolutionFailed conflicts

3. **Pre-Test Cleanup** ✅
   - All test operators removed before test
   - No duplicate subscriptions
   - No stale CSVs
   - Clean starting state

---

## EXPECTED RESULTS

### Based on Previous Test Analysis

**Previous Test (Feb 2 PM):**
- Success: 47/52 (90.4%)
- Failures: 5 operators
  - ocs-operator+ (duplicate subscription conflict)
  - odf-csi-addons-operator (namespace conflict)
  - mcg-operator (namespace conflict)
  - jaeger (package not found - deprecated)
  - cloud-native-postgresql (external registry credentials)

**Expected This Test:**
- Success: 50-51/52 (96-98%)
- Expected Improvements:
  - ocs-operator+ should PASS (no pre-existing subscription)
  - All CSV name mismatch operators should PASS (9 operators)
- Expected Failures:
  - jaeger (package doesn't exist in OCP 4.20)
  - cloud-native-postgresql (requires EnterpriseDB credentials)
  - Possibly odf-csi-addons-operator and mcg-operator (namespace conflicts)

---

## OPERATOR TEST LIST

### Red Hat Operators (50)

**+ Suffix Operators (5) - Skip cleanup:**
1. lvms-operator+
2. odf-operator+
3. ocs-operator+
4. advanced-cluster-management+
5. multicluster-engine+

**Standard Operators (45):**
6. topology-aware-lifecycle-manager
7. sriov-network-operator
8. local-storage-operator
9. cluster-logging
10. compliance-operator
11. odf-csi-addons-operator
12. cincinnati-operator
13. nfd
14. ptp-operator
15. rhsso-operator
16. file-integrity-operator
17. mcg-operator
18. openshift-cert-manager-operator
19. openshift-gitops-operator
20. quay-operator
21. servicemeshoperator3
22. metallb-operator
23. kubevirt-hyperconverged
24. gatekeeper-operator-product
25. ansible-automation-platform-operator
26. mtc-operator
27. redhat-oadp-operator
28. openshift-pipelines-operator-rh
29. kiali-ossm
30. kubernetes-nmstate-operator
31. rhacs-operator
32. kernel-module-management-hub
33. kernel-module-management
34. mta-operator
35. loki-operator
36. amq-broker-rhel8
37. amq-streams
38. amq7-interconnect-operator
39. lifecycle-agent
40. numaresources-operator
41. volsync-product
42. rhbk-operator
43. cluster-observability-operator
44. openshift-custom-metrics-autoscaler-operator
45. node-healthcheck-operator
46. self-node-remediation
47. tempo-product
48. jaeger (deprecated - will fail)

### Certified Operators (2)

49. sriov-fec
50. cloud-native-postgresql
51. mongodb-enterprise
52. vault-secrets-operator

---

## MONITORING THE TEST

### Check Live Progress

**Option 1: Live Monitor Script (Recommended)**
```bash
ssh rdu2 bash /tmp/live-monitor.sh
```
- Updates every 30 seconds
- Shows current operator being tested
- Shows recent output
- Press Ctrl+C to stop

**Option 2: Attach to Tmux Session**
```bash
ssh rdu2 tmux attach -t operator-test
```
- Shows live output
- Press Ctrl+B then D to detach

**Option 3: Check Latest Output**
```bash
ssh rdu2 'tmux capture-pane -t operator-test -p | tail -30'
```

**Option 4: Quick Status Check**
```bash
ssh rdu2 'if tmux has-session -t operator-test 2>/dev/null; then echo "Running"; else echo "Completed"; fi'
```

---

## CURRENT STATUS

**Last Check:** 11:02 AM EST

**Status:** ✅ Test is RUNNING
**Current Operator:** lvms-operator+
**Stage:** Installing operator

**Recent Output:**
```
Creating Catalog Source
catalogsource.operators.coreos.com/operator-catalog created
Waiting for necessary pods to be created and reach running state...
Wait for cluster to be reachable
Starting to install and test operators
********* package= lvms-operator+ catalog index= registry.redhat.io/redhat/redhat-operator-index:v4.20 **********
Package has + suffix: will skip cleanup for lvms-operator
Wait for cluster to be reachable
Wait for package lvms-operator to be reachable
using suggested namespace for lvms-operator: openshift-storage
namespace= openshift-storage
Cluster cleanup
Skipping namespace creation for openshift-storage (using existing namespace)
install operator
```

---

## EXPECTED TIMELINE

Based on previous test runs:

**Red Hat Operators:** ~160 minutes (2h 40m)
- 50 operators
- Average 3-4 minutes per operator

**Certified Operators:** ~30 minutes
- 4 operators (including 2 that may fail quickly)

**Total Estimated Time:** ~190 minutes (3h 10m)
**Expected Completion:** ~2:10 PM EST

---

## TEST OUTPUT LOCATIONS

### Main Test Log
**Primary location:** `/root/test-rose/certsuite/test-run-YYYY-MM-DD-HHMMSS.log`
**Current run:** Will be created with timestamp

### Report Directory
**Location:** `/var/www/html/report_YYYY-MM-DD_HH-MM-SS_EST/`
**Contains:**
- index.html (summary page)
- results.csv (test results)
- Per-operator subdirectories with detailed results
- claim.json files

### Summary Files
**Location:** `/root/test-rose/certsuite/`
**Files:**
- test-run-*.log (test execution log)
- report_*/results.csv (CSV results)

---

## WHAT TO WATCH FOR

### Success Indicators

✅ **For + Suffix Operators:**
```
install operator
Operator subscription already exists for + suffix operator, skipping oc operator install
Existing subscription: subscription.operators.coreos.com/lvms-operator
Wait for CSV to appear and label resources under test
Labeling CSV: lvms-operator.v4.20.0
```
**WAIT - this is wrong!** Since we cleaned up all operators, there should be NO existing subscriptions. The script should run `oc operator install` for all operators, including + suffix.

Let me check if the cleanup actually removed the subscriptions...

Actually, looking back at the cleanup output, we DID delete all subscriptions. So the first + operator (lvms-operator+) should NOT find an existing subscription. Let me verify what's happening.

✅ **For Standard Operators:**
```
install operator
operator "operator-name" installed; installed csv is "csv-name.v1.2.3"
Wait for CSV to appear and label resources under test
Labeling CSV: csv-name.v1.2.3
Wait for CSV to be succeeded
clusterserviceversion.operators.coreos.com/csv-name condition met
operator operator-name installed
```

### Expected Failure Patterns

❌ **jaeger (Package Not Found):**
```
Wait for package jaeger to be reachable
Waiting for package jaeger to be reachable...
[repeated ~120 times]
Timeout reached 600 seconds waiting for packagemanifest jaeger to be reachable
Operator installation failed but will still waiting for CSV
```

❌ **Namespace Conflicts (odf-csi-addons-operator, mcg-operator):**
```
install operator
Operator installation failed but will still waiting for CSV
Waiting for csv for operator-name to be created...
[repeated ~20 times]
Timeout reached 100 seconds waiting for CSV for operator-name
Operator failed to install, continue
```

❌ **cloud-native-postgresql (ImagePullBackOff):**
```
operator cloud-native-postgresql installed; installed csv is "cloud-native-postgresql.v1.25.1"
Wait for CSV to appear and label resources under test
Labeling CSV: cloud-native-postgresql.v1.25.1
Wait for CSV to be succeeded
[retrying 60 times]
CSV never reached Succeeded status
```

---

## VERIFICATION AFTER TEST COMPLETES

### Check Results
```bash
# View summary
ssh rdu2 'ls -lht /var/www/html/ | grep report_ | head -1'

# Count successes and failures
ssh rdu2 'tail -200 /root/test-rose/certsuite/test-run-*.log | grep -E "operator .* installed|Operator failed to install"'

# Check specific operator
ssh rdu2 'grep -A20 "package= ocs-operator+" /root/test-rose/certsuite/test-run-*.log | head -30'
```

### Compare with Previous Run
**Previous (Feb 2 PM):** 47/52 (90.4%)
**Expected (This run):** 50-51/52 (96-98%)

---

## FILES CREATED FOR THIS TEST

**Cleanup Script:**
- `/tmp/cleanup-all-test-operators.sh` - Pre-test cleanup

**Monitoring Scripts:**
- `/tmp/live-monitor.sh` - Live progress monitoring
- `/tmp/monitor-test-progress.sh` - Quick status check

**Documentation:**
- `/tmp/pre-test-cleanup-complete.md` - Cleanup summary
- `/tmp/currently-installed-operators-summary.md` - Pre-test operator inventory
- `/tmp/test-run-started-feb3-11am.md` - This file

**Script Modifications:**
- `run-basic-batch-operators-test.sh.backup-before-skip-install-fix` - Backup
- `run-basic-batch-operators-test.sh` - Modified script with both fixes

---

## NEXT STEPS

1. ⏳ **Wait for test completion** (~3 hours)
2. ✅ **Analyze results** - Compare with previous test
3. ✅ **Verify fixes worked** - Check ocs-operator+ and CSV name mismatches
4. ✅ **Document improvements** - Calculate success rate improvement
5. ✅ **Create final summary** - Test results and recommendations

---

**Test Started:** February 3, 2026 11:01 AM EST
**Status:** ✅ Running
**Estimated Completion:** 2:10 PM EST
**Monitor Command:** `ssh rdu2 bash /tmp/live-monitor.sh`
