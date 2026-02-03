# CURRENTLY INSTALLED OPERATORS FROM TEST LIST

**Cluster:** rdu2
**Checked:** February 3, 2026 10:46 AM EST
**Total Test Operators:** 52 operators

---

## SUMMARY

**Total CSVs Installed:** 14 (excluding packageserver)
**Total Subscriptions:** 16
**From Test List:**
- ✅ **Installed with CSV:** 5 operators (all + suffix operators)
- ⚠️ **Subscription Only (No CSV):** 2 operators
- ❌ **Not Installed:** 45 operators

---

## ✅ INSTALLED OPERATORS (5 total)

These operators have both subscriptions and CSVs installed. All are + suffix operators that persist between test runs.

### 1. lvms-operator+
- **Namespace:** openshift-storage
- **CSV:** lvms-operator.v4.20.0
- **Subscription:** lvms-operator
- **Status:** ✅ Healthy

### 2. odf-operator+
- **Namespace:** openshift-storage
- **CSV:** odf-operator.v4.20.4-rhodf
- **Subscription:** odf-operator
- **Status:** ✅ Healthy

### 3. ocs-operator+
- **Namespace:** openshift-storage
- **CSV:** ocs-operator.v4.20.4-rhodf
- **Subscriptions:** 2 subscriptions (DUPLICATE!)
  - ocs-operator
  - ocs-operator-stable-4.20-operator-catalog-openshift-marketplace
- **Status:** ⚠️ Has duplicate subscription (ResolutionFailed)

### 4. advanced-cluster-management+
- **Namespace:** open-cluster-management
- **CSV:** advanced-cluster-management.v2.14.1
- **Subscription:** advanced-cluster-management
- **Status:** ✅ Healthy

### 5. multicluster-engine+
- **Namespace:** multicluster-engine (also test-multicluster-engine)
- **CSV:** multicluster-engine.v2.9.1
- **Subscriptions:** 2 locations
  - multicluster-engine namespace
  - test-multicluster-engine namespace
- **Status:** ⚠️ Installed in multiple namespaces

---

## ⚠️ SUBSCRIPTION ONLY - NO CSV (2 operators)

These operators have subscriptions but no CSV installed. They are in ResolutionFailed state.

### 1. odf-csi-addons-operator
- **Namespace:** openshift-storage
- **Subscription:** odf-csi-addons-operator
- **CSV:** None
- **Reason:** OLM ResolutionFailed - shared namespace conflicts

### 2. mcg-operator
- **Namespace:** openshift-storage
- **Subscription:** mcg-operator
- **CSV:** None
- **Reason:** OLM ResolutionFailed - shared namespace conflicts

---

## ❌ NOT INSTALLED (45 operators)

These operators have no subscriptions or CSVs installed. They will be installed fresh during test runs.

**Red Hat Operators (43):**
- topology-aware-lifecycle-manager
- sriov-network-operator
- local-storage-operator
- cluster-logging
- compliance-operator
- cincinnati-operator
- nfd
- ptp-operator
- rhsso-operator
- file-integrity-operator
- openshift-cert-manager-operator
- openshift-gitops-operator
- quay-operator
- servicemeshoperator3
- metallb-operator
- kubevirt-hyperconverged
- gatekeeper-operator-product
- ansible-automation-platform-operator
- mtc-operator
- redhat-oadp-operator
- openshift-pipelines-operator-rh
- kiali-ossm
- kubernetes-nmstate-operator
- rhacs-operator
- kernel-module-management-hub
- kernel-module-management
- mta-operator
- loki-operator
- amq-broker-rhel8
- amq-streams
- amq7-interconnect-operator
- lifecycle-agent
- numaresources-operator
- volsync-product
- rhbk-operator
- cluster-observability-operator
- openshift-custom-metrics-autoscaler-operator
- node-healthcheck-operator
- self-node-remediation
- tempo-product
- jaeger (deprecated - doesn't exist in catalog)

**Certified Operators (4):**
- sriov-fec
- cloud-native-postgresql
- mongodb-enterprise
- vault-secrets-operator

---

## DETAILED INVENTORY BY NAMESPACE

### openshift-storage (13 CSVs, 15 subscriptions)

**CSVs:**
1. lvms-operator.v4.20.0
2. odf-operator.v4.20.4-rhodf
3. ocs-operator.v4.20.4-rhodf
4. cephcsi-operator.v4.20.4-rhodf
5. ocs-client-operator.v4.20.4-rhodf
6. odf-dependencies.v4.20.4-rhodf
7. odf-external-snapshotter-operator.v4.20.4-rhodf
8. odf-prometheus-operator.v4.20.4-rhodf
9. recipe.v4.20.4-rhodf
10. rook-ceph-operator.v4.20.4-rhodf

**Subscriptions (15):**
1. lvms-operator
2. odf-operator
3. ocs-operator ← duplicate
4. ocs-operator-stable-4.20-operator-catalog-openshift-marketplace ← duplicate
5. mcg-operator (no CSV)
6. odf-csi-addons-operator (no CSV)
7. cephcsi-operator-stable-4.20-operator-catalog-openshift-marketplace
8. ocs-client-operator-stable-4.20-operator-catalog-openshift-marketplace
9. odf-dependencies
10. odf-external-snapshotter-operator-stable-4.20-operator-catalog-openshift-marketplace
11. odf-prometheus-operator-stable-4.20-operator-catalog-openshift-marketplace
12. recipe-stable-4.20-operator-catalog-openshift-marketplace
13. rook-ceph-operator-stable-4.20-operator-catalog-openshift-marketplace

**Issues:**
- ⚠️ 2 duplicate subscriptions for ocs-operator
- ⚠️ 2 subscriptions with no CSV (mcg-operator, odf-csi-addons-operator)

### open-cluster-management (1 CSV, 1 subscription)

**CSVs:**
1. advanced-cluster-management.v2.14.1

**Subscriptions:**
1. advanced-cluster-management

### multicluster-engine (1 CSV, 1 subscription)

**CSVs:**
1. multicluster-engine.v2.9.1

**Subscriptions:**
1. multicluster-engine

### test-multicluster-engine (1 CSV, 1 subscription)

**CSVs:**
1. multicluster-engine.v2.9.1

**Subscriptions:**
1. multicluster-engine

---

## ISSUES IDENTIFIED

### 1. Duplicate ocs-operator Subscription ⚠️
**Impact:** High
**Problem:** Two subscriptions for ocs-operator causing ResolutionFailed
**Solution:** Delete the duplicate auto-generated subscription
```bash
oc delete subscription ocs-operator-stable-4.20-operator-catalog-openshift-marketplace \
  -n openshift-storage
```

### 2. Failed Subscriptions in openshift-storage ⚠️
**Impact:** Medium
**Problem:** mcg-operator and odf-csi-addons-operator have subscriptions but no CSV
**Reason:** OLM ResolutionFailed due to shared namespace conflicts
**Solution:** These will continue to fail until namespace conflicts resolved

### 3. No Active Catalog Source ⚠️
**Impact:** High
**Problem:** All subscriptions reference "operator-catalog" which doesn't exist
**Current State:**
```bash
$ oc get catalogsource -n openshift-marketplace
No resources found in openshift-marketplace namespace.
```
**Why It Matters:** Test script creates "operator-catalog" at test start, deletes at test end
**Result:** Between tests, all subscriptions are in CatalogSourcesUnhealthy state

---

## CLEANUP RECOMMENDATIONS

### Option 1: Clean Cluster (Full Reset)
Remove all test operators and start fresh:
```bash
# Delete all subscriptions
oc delete subscription --all -n openshift-storage
oc delete subscription --all -n open-cluster-management
oc delete subscription --all -n multicluster-engine
oc delete subscription --all -n test-multicluster-engine

# Delete all CSVs
oc delete csv --all -n openshift-storage
oc delete csv --all -n open-cluster-management
oc delete csv --all -n multicluster-engine
oc delete csv --all -n test-multicluster-engine

# Delete namespaces
oc delete namespace test-multicluster-engine
```

### Option 2: Fix Duplicates Only (Minimal)
Keep + operators, remove duplicates:
```bash
# Remove duplicate ocs-operator subscription
oc delete subscription ocs-operator-stable-4.20-operator-catalog-openshift-marketplace \
  -n openshift-storage

# Remove failed subscriptions
oc delete subscription mcg-operator -n openshift-storage
oc delete subscription odf-csi-addons-operator -n openshift-storage
```

### Option 3: Keep As-Is
Continue with current state:
- + operators will be skipped (with new script fix)
- Duplicate subscription will be avoided (with new script fix)
- Tests should run cleanly

---

## EXPECTED BEHAVIOR IN NEXT TEST RUN

With the new script modifications:

**For + Suffix Operators (5):**
- lvms-operator+: ✅ Skip install, find CSV, test passes
- odf-operator+: ✅ Skip install, find CSV, test passes
- ocs-operator+: ✅ Skip install, find CSV (despite duplicate subscription)
- advanced-cluster-management+: ✅ Skip install, find CSV, test passes
- multicluster-engine+: ✅ Skip install, find CSV, test passes

**For Failed Subscriptions (2):**
- odf-csi-addons-operator: ❌ Will fail (namespace conflict)
- mcg-operator: ❌ Will fail (namespace conflict)

**For All Other Operators (45):**
- ✅ Fresh install, should pass

**Expected Success Rate:** 50/52 (96.2%)
- 5 + operators reused
- 45 fresh installs
- 2 expected failures (namespace conflicts)

---

**Report Date:** February 3, 2026
**Report Location:** `/tmp/currently-installed-operators-summary.md`
