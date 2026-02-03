# FULL 52-OPERATOR TEST - MONITORING PLAN

## Test Details
**Started:** ~1:03 PM EST (Feb 2, 2026)
**Log File:** `test-run-FIXED-20260202-130319.log`
**Tmux Session:** `full-test`
**Expected Duration:** ~30 minutes
**Expected Completion:** ~1:33 PM EST

## What We're Testing
- **Total Operators:** 52
- **Previously Failed:** 14 operators
  - 9 CSV name mismatch (should now PASS ✅)
  - 4 OLM timeout (might pass with cleaner env)
  - 1 missing credentials (will still fail)

## Expected Results

### Conservative Estimate:
- **Success:** 47/52 (90.4%)
- **Failures:** 5
  - cloud-native-postgresql (credentials)
  - 4 OLM timeouts (if they persist)

### Optimistic Estimate:
- **Success:** 51/52 (98.1%)
- **Failures:** 1
  - cloud-native-postgresql only

## Progress Checkpoints

**5 min mark (~1:08 PM):** Should have ~8-10 operators done
**10 min mark (~1:13 PM):** Should have ~16-20 operators done
**15 min mark (~1:18 PM):** Should have ~24-28 operators done
**20 min mark (~1:23 PM):** Should have ~32-36 operators done
**25 min mark (~1:28 PM):** Should have ~40-44 operators done
**30 min mark (~1:33 PM):** Should be complete

## Key Operators to Watch

### CSV Name Mismatch (should all PASS now):
1. ✅ cincinnati-operator
2. ✅ openshift-cert-manager-operator
3. ✅ kubevirt-hyperconverged
4. ✅ redhat-oadp-operator
5. ✅ kiali-ossm
6. ✅ amq-broker-rhel8
7. ✅ amq-streams
8. ✅ openshift-custom-metrics-autoscaler-operator
9. ✅ tempo-product

### OLM Timeout (watch for improvement):
1. ⚠️ odf-csi-addons-operator
2. ⚠️ mcg-operator
3. ⚠️ ansible-automation-platform-operator
4. ⚠️ jaeger

### Known Failure:
1. ❌ cloud-native-postgresql (credentials issue)

## Monitoring Commands

Check progress:
```bash
ssh rdu2 'tail -30 /root/test-rose/certsuite/test-run-FIXED-*.log'
```

Count completed:
```bash
ssh rdu2 'grep -c "package=" /root/test-rose/certsuite/test-run-FIXED-*.log'
```

Check failures:
```bash
ssh rdu2 'grep -c "Operator failed to install" /root/test-rose/certsuite/test-run-FIXED-*.log'
```
