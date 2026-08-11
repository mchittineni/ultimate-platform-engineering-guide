---
title: "When do you give a tenant its own cluster instead of a namespace?"
id: 25
category: "Multi-Tenancy and Isolation"
difficulty: "Advanced"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - interview-questions
---

# When do you give a tenant its own cluster instead of a namespace?

**Short answer:** Give a tenant its own cluster when a namespace cannot provide something they genuinely require - containing regulatory audit scope, data residency, untrusted code, an incompatible upgrade cadence, or blast-radius isolation for a top-tier workload. Do not do it because it feels safer, because every cluster carries a fixed cost in money and in operational attention, and the number of clusters you run is the strongest predictor of how much of your team's capacity goes to maintenance rather than capability.

## Detail

**What a dedicated cluster actually buys you.** A separate control plane, so API server and etcd contention is isolated. A separate upgrade cadence. A separate audit boundary. A cleanly separate network posture and egress policy. And a real blast radius boundary - a cluster-wide misconfiguration, a bad admission webhook, or a CNI failure affects one tenant.

**What it costs, and this is the part to be specific about.** The control plane fee, a minimum viable node footprint that is rarely well utilised, and a full copy of every platform component - ingress controller, cert-manager, CSI drivers, observability agents, policy engine, GitOps agent. That last item is the one people underestimate: each new cluster multiplies the number of component upgrades, certificate rotations, and version-skew combinations your team owns. Ten clusters is not ten times one cluster; it is ten times one cluster plus fleet management.

**The legitimate triggers:**

| Trigger                      | Why a namespace cannot do it                                       |
| ---------------------------- | ------------------------------------------------------------------ |
| Regulatory scope containment | Auditors scope to the cluster; sharing pulls 180 services into PCI |
| Data residency               | Nodes and volumes must be in a specific region                     |
| Untrusted code               | Shared kernel; namespace is not a security boundary                |
| Incompatible upgrade cadence | One control plane version per cluster                              |
| Tier-0 blast radius          | Cluster-wide failures do not respect namespaces                    |
| Control-plane resource abuse | Shared API server and etcd                                         |
| Legally separate entity      | Ownership and access must be provably separate                     |

**The bad reasons, which come up constantly:** "the team wants isolation" without a stated requirement; "we had a noisy neighbour once" - dedicated node pools solve that far more cheaply; "production must be separate" - true, but that is an environment boundary you already have; and "it is easier than getting RBAC right", which trades a solvable configuration problem for a permanent operational one.

**Consider the cheaper intermediate steps first.** Dedicated node pools with taints and tolerations handle resource contention and give a node-level boundary. Virtual control planes - vcluster and similar - give a tenant their own API server and CRD space on shared nodes, which covers the "they need cluster-scoped resources" case without a real cluster. Sandboxed runtimes cover untrusted code. Reaching for a full cluster before trying these is the common overcorrection.

**If you do run many clusters, the answer changes shape.** Beyond a handful, you need fleet management as a first-class capability: a cluster API or provider-managed lifecycle, one place that defines what every cluster must contain, per-cluster reconciliation from a shared definition, and a cluster inventory. Fleets built ad hoc become unupgradeable, which is how organisations end up with clusters three versions behind.

## Example

```text
Deciding for five requests in one quarter. Only one got a cluster.

REQUEST 1  Payments team, PCI scope
  ask: dedicated cluster
  test: can a namespace contain audit scope? No - the auditor scopes to the
        cluster, so 180 unrelated services enter PCI scope.
  -> GRANTED. Driver is audit cost, and it is a genuine namespace limitation.

REQUEST 2  ML team, "our GPU jobs get evicted"
  ask: dedicated cluster
  test: is this resource contention? Yes.
  -> DECLINED. Dedicated node pool with taints + tolerations, guaranteed QoS,
     and a PriorityClass. Solves it at ~5% of the cost.

REQUEST 3  Data team, "we need to install CRDs and a mutating webhook"
  ask: dedicated cluster
  test: do they need cluster-scoped resources, or a whole cluster?
  -> DECLINED. Virtual cluster (vcluster): their own API server and CRD space,
     scheduled onto shared nodes. Covers the actual need.

REQUEST 4  A team running customer-supplied plugins
  ask: namespace, with "we'll be careful"
  test: is the code trusted? No.
  -> ESCALATED THE OTHER WAY. A namespace is not a security boundary for
     untrusted code. Dedicated cluster with gVisor and restricted egress.
     The team asked for less isolation than they needed.

REQUEST 5  Reporting team, "production should be separate from staging"
  ask: dedicated cluster per environment
  test: is this an environment boundary?
  -> ALREADY SATISFIED. Separate cloud accounts per environment already exist.
     No new cluster.

Outcome: 1 new cluster from 5 requests. Cluster count went 4 -> 5, which added
one more copy of 9 platform components to the upgrade matrix. That is the cost
that justifies saying no four times.
```

```text
The fixed cost of one more cluster - the list to quote when pushing back:

  control plane fee                    per cluster, whether idle or not
  minimum node footprint               3 nodes for HA, poorly utilised
  ingress controller                   + upgrade, + certificate rotation
  cert-manager                         + upgrade
  CSI + CNI                            + upgrade, + version skew vs control plane
  observability agents                 + upgrade, + config drift risk
  policy engine + policy bundle        + upgrade, + policy sync
  GitOps agent + registration          + upgrade
  secrets driver                       + upgrade
  cluster registration in the fleet    inventory, access, break-glass, DR plan
  ------------------------------------------------------------------------------
  ~9 components x N clusters = the real number, and it grows superlinearly once
  version skew between clusters appears.
```

## Interview tips

- Give the triggers as things a namespace genuinely cannot do, and lead with regulatory scope containment - it is the most defensible and most common real driver.
- Be specific about cost. Listing the nine platform components that get duplicated per cluster is what makes the answer sound like it came from running a fleet.
- Naming the cheaper intermediate options - dedicated node pools, virtual clusters, sandboxed runtimes - is the strongest differentiator here. Most candidates jump straight from namespace to cluster.
- The reversed case, where a team asks for less isolation than their threat model requires, is a memorable example and shows you evaluate rather than just approve.
- Expect "how do you manage 30 clusters?" - fleet management as a capability, one definition reconciled per cluster, and an inventory. Ad hoc fleets become unupgradeable.

---

[⬅ Back to Multi-Tenancy and Isolation](./README.md) · [All topics](../README.md)
