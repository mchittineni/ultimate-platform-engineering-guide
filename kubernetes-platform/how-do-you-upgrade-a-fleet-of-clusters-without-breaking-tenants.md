---
title: "How do you upgrade a fleet of clusters without breaking tenants?"
id: 33
category: "Kubernetes Platform"
difficulty: "Advanced"
tags:
  - platform-engineering
  - kubernetes-platform
  - interview-questions
---

# How do you upgrade a fleet of clusters without breaking tenants?

**Short answer:** Make upgrades a routine, frequent, staged process rather than an annual event: detect removed APIs and incompatible components before you start, upgrade the control plane first and nodes second, roll through clusters in waves from lowest to highest risk, and rely on pod disruption budgets and topology spread - which the platform should have set by default - to keep tenant workloads available during node replacement. The most common cause of tenant breakage is a removed API version nobody scanned for.

## Detail

**Frequency reduces risk.** Upgrading often means small version jumps, familiar procedures, and skills that stay current. Organisations that upgrade rarely accumulate several versions of deprecations at once, and each upgrade becomes a project with high stakes - which encourages further delay. Kubernetes minor releases are frequent and support windows are finite, so the treadmill is not optional; the only choice is whether it is routine or traumatic.

**Pre-flight checks are where the real work is:**

- **Removed and deprecated APIs.** Scan the manifests in Git and, importantly, what is actually stored in the cluster. Tools such as `kubent` or `pluto` do this. This single check prevents most tenant breakage.
- **Component compatibility.** Every controller, CSI and CNI driver, admission webhook, and agent has a supported version range. A webhook that fails against a new API version can block all Pod creation.
- **Deprecated feature gates and flags** that will be removed.
- **Version skew rules.** Control plane and node versions may differ only within a supported window, which is why the order matters.
- **Tenant readiness.** Do tier-1 workloads have disruption budgets and spread constraints? If they do not, node drains will hurt them.

**Order: control plane, then nodes.** The control plane may run ahead of nodes but not behind. Upgrade it first, verify, then replace nodes.

**Replace nodes rather than upgrading in place.** Create new nodes at the new version, cordon and drain the old ones, delete them. This is a surge upgrade: you need spare capacity and quota headroom, and you get a clean rollback path because the old nodes can be kept until you are confident. In-place node upgrades leave residue and are harder to reverse.

**Pod disruption budgets are what protect tenants during the drain**, and they cut both ways: a budget that can never be satisfied - a single-replica deployment with `minAvailable: 1` - blocks the drain indefinitely. A platform should generate correct budgets from the tier and detect unsatisfiable ones before an upgrade rather than discovering them mid-drain at 2am.

**Wave the fleet by risk.** Management cluster last or on its own carefully controlled path, then dev, staging, low-tier production, high-tier production, with a soak period between waves long enough for slow-burn problems to appear. Automation should execute the waves; a human should approve each promotion.

**Communicate specifically.** Tenants need to know when their cluster is being upgraded, what could affect them, and what they must do. "We are upgrading Kubernetes next month" produces nothing; "your service `reporting-api` uses `policy/v1beta1 PodDisruptionBudget`, removed in this version - here is the pull request" produces action.

**Have a rollback position and be honest about it.** Control-plane downgrades are generally not supported, so the realistic recovery for a bad control-plane upgrade is failing traffic to another cluster - which is another argument for the cluster-replacement model and for everything being reproducible from Git.

## Example

```text
Fleet upgrade 1.31 -> 1.32, nine clusters, waved over three weeks.

PRE-FLIGHT (before any cluster is touched)
  $ platform fleet preflight --target 1.32

  removed APIs in use
    ✗ team-reporting/reporting-api    policy/v1beta1 PodDisruptionBudget
    ✗ team-data/etl-cron              batch/v1beta1 CronJob
    -> 2 migration PRs auto-raised, with the exact diff. Blocking.

  component compatibility
    ✓ cilium 1.16.x        supports 1.32
    ✗ csi-driver 2.4.1     max 1.31  -> upgrade driver first. Blocking.
    ✓ kyverno 1.13.x       supports 1.32
    ⚠ custom-webhook 0.9   untested  -> test in dev wave, non-blocking

  tenant readiness
    ✗ 7 tier-1 deployments have no PodDisruptionBudget
    ✗ 2 PDBs are unsatisfiable (1 replica, minAvailable: 1) -> would block drain
    -> platform generates PDBs from tier; 2 unsatisfiable ones fixed first

  capacity
    ✓ quota headroom sufficient for surge in all 9 clusters

WAVES (control plane first in each cluster, then node replacement)
  Wave 0  dev-eu-1                        soak 48h   -> found the webhook issue
  Wave 1  staging-eu-1, preview-eu-1      soak 72h
  Wave 2  prod-us-1 (lowest traffic)      soak 96h
  Wave 3  prod-eu-2                       soak 96h   (partner drains traffic-free)
  Wave 4  prod-eu-1                       soak 96h
  Wave 5  prod-pci-eu-1                   change window, separate approval
  Wave 6  mgmt-eu-1, mgmt-eu-2            last, one at a time, standby first

  Each promotion: automated execution, human approval, and abort criteria -
  any tier-1 SLO burn or any pod evicted below its PDB stops the wave.
```

```yaml
# Generated from tier, not left to teams. Correct budgets are the difference
# between a routine drain and a tenant incident.
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: checkout
  namespace: team-payments
  annotations:
    platform.example.com/generated-from: "service/checkout:tier=1"
spec:
  # tier 1 -> minAvailable 2 (with replicas >= 3). Never minAvailable == replicas,
  # which produces an unsatisfiable budget that blocks every node drain.
  minAvailable: 2
  selector: { matchLabels: { app: checkout } }
```

## Interview tips

- Say upgrade frequently as the first risk-reduction measure. Interviewers who have lived through a two-version-behind cluster will recognise it immediately.
- Removed API scanning is the highest-value pre-flight check and the most common cause of tenant breakage - name `kubent` or `pluto` and say you scan both Git and live cluster state.
- The unsatisfiable pod disruption budget blocking a drain is a specific, painful, real failure. Mentioning it is strong evidence of experience.
- Control plane before nodes, and node replacement rather than in-place upgrade, with the capacity headroom that implies. These are the mechanics interviewers check.
- Be honest that control-plane rollback is effectively not available, and that the real recovery is failing over. Candidates who claim a clean rollback have not done it.

---

[⬅ Back to Kubernetes Platform](./README.md) · [All topics](../README.md)
