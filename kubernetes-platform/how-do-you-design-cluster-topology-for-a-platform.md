---
title: "How do you design cluster topology for a platform?"
id: 61
category: "Kubernetes Platform"
difficulty: "Advanced"
tags:
  - platform-engineering
  - kubernetes-platform
  - interview-questions
---

# How do you design cluster topology for a platform?

**Short answer:** Decide what a cluster boundary is for - environment, region, compliance scope, or blast radius - and pick the smallest number of clusters that satisfies those requirements, because cluster count is the main driver of a platform team's maintenance load. The common good answer is one cluster per environment per region, with dedicated clusters only where a namespace genuinely cannot serve, plus a separate management cluster that must never host tenant workloads.

## Detail

**Start from what the boundary must give you.** Clusters are expensive boundaries, so each one should be justified by something a namespace cannot do: environment separation, regional placement for latency or residency, compliance scope containment, or blast-radius isolation for the highest tier. Every other reason should be pushed down to a cheaper boundary.

**The dimensions, and what each costs:**

| Dimension   | Typical count       | Justification                                       |
| ----------- | ------------------- | --------------------------------------------------- |
| Environment | 3 (dev/stage/prod)  | Mandatory - and it belongs at the account level too |
| Region      | 1 to 3              | Latency, residency, regional failure isolation      |
| Compliance  | 0 or 1              | Only to contain audit scope                         |
| Tenant      | 0 to few            | Only when a namespace genuinely cannot serve        |
| Management  | 1 (or 1 per region) | Hosts the control plane; never tenant workloads     |

Multiply these out carefully - three environments times three regions is already nine clusters, plus management. That number is the one to sanity-check against your team size.

**Management clusters should be separate, and this is the point worth making firmly.** The cluster running Argo CD, Crossplane, and the platform controllers should not host tenant workloads. Two reasons: a tenant cannot degrade the machinery that would fix them, and the management cluster's blast radius is enormous so it needs different change control. The corollary is a bootstrapping question - who reconciles the management cluster? - which needs an explicit answer, usually a minimal externally-managed pipeline or a small seed cluster.

**Fewer, larger clusters is usually the right default.** Utilisation is better, there are fewer things to upgrade, and cross-service networking is simpler. The counter-pressure is blast radius: one cluster-wide failure - a bad CNI upgrade, a broken admission webhook, control-plane exhaustion - affects everyone in it. The resolution is usually not more clusters but stronger in-cluster isolation plus a genuinely tested ability to fail over.

**Design for cluster failure rather than assuming clusters do not fail.** The valuable question is what happens when a whole cluster is lost. If the answer is "we rebuild and redeploy from Git", measure how long that takes and whether it meets the tier's requirement. If it does not, you need capacity in a second cluster and traffic management above it - which is a different design, not a bigger cluster.

**Avoid cross-cluster service dependencies where you can.** Services that call each other should generally live in the same cluster; a synchronous dependency crossing a cluster boundary adds latency, a failure domain, and considerable networking complexity. Cross-cluster communication is best kept to asynchronous or clearly regional patterns.

**Plan for cluster replacement, not perpetual upgrades.** Treating clusters as replaceable - build the new one, shift traffic, delete the old - avoids accumulating years of in-place upgrade residue and is the only way to change decisions baked in at creation, such as CIDR ranges or the CNI. This requires that everything in a cluster is reproducible from Git, which is a design constraint on the whole platform.

## Example

```text
A concrete topology for 40 teams, 220 services, two regions, one PCI scope.

MANAGEMENT (2 clusters, one per region, active/standby)
  hosts: Argo CD, Crossplane, cluster-api, policy distribution, platform CRDs
  tenants: none, ever
  change control: stricter than production - a bad change here blocks everything
  bootstrap: minimal external pipeline reconciles these two; documented and tested

PRODUCTION (4 clusters)
  prod-eu-1, prod-eu-2    tenants by namespace, ~110 services each
  prod-us-1               tenants by namespace, ~40 services
  prod-pci-eu-1           payments only - contains audit scope
  capacity: eu-1 and eu-2 each sized to absorb the other's traffic

NON-PRODUCTION (3 clusters)
  staging-eu-1            production-shaped, same platform versions
  dev-eu-1                shared, relaxed quotas, aggressive scale-to-zero
  preview-eu-1            ephemeral PR environments, TTL-reaped

  Total: 9 clusters. Each one is 9+ platform components to keep in step, which
  is what the fleet management capability exists to handle.

Why not fewer:
  - prod-eu-1/eu-2 split exists so a cluster-level failure is survivable, and
    the failover is exercised quarterly rather than assumed.
  - prod-pci-eu-1 exists to keep 210 services out of PCI audit scope.
Why not more:
  - no per-team clusters; namespaces plus node pools cover every request so far.
  - no separate cluster per service tier; priority classes handle that in-cluster.
```

```yaml
# Cluster identity carried as labels, so the fleet definition can target by
# property rather than by name - "every production cluster gets this policy".
apiVersion: cluster.x-k8s.io/v1beta2 # v1beta2 since Cluster API v1.11; v1beta1 is being retired
kind: Cluster
metadata:
  name: prod-eu-1
  labels:
    platform.example.com/environment: production
    platform.example.com/region: eu-west-1
    platform.example.com/tenancy: shared
    platform.example.com/compliance-scope: standard # vs "pci"
    platform.example.com/failover-partner: prod-eu-2
    platform.example.com/k8s-channel: stable # stable | fast, for upgrade waves
```

## Interview tips

- Start from what the boundary must provide, and be explicit that cluster count is the main driver of platform maintenance load. Multiplying the dimensions out loud shows you have felt this.
- "Management clusters host no tenant workloads" is a firm, defensible position - and volunteering the bootstrapping question that follows is a strong signal.
- Default to fewer, larger clusters and give the counter-pressure honestly. Resolving it with in-cluster isolation plus tested failover, rather than more clusters, is the senior answer.
- "Design for cluster replacement, not perpetual upgrades" is the idea that most distinguishes this answer, and it explains why everything must be reproducible from Git.
- Expect "how do you handle a service in one cluster calling one in another?" - prefer same-cluster for synchronous calls; cross-cluster should be asynchronous or regional by design.

---

[⬅ Back to Kubernetes Platform](./README.md) · [All topics](../README.md)
