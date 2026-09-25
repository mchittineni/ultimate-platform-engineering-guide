---
title: "How do you design node pools and scheduling for mixed workloads?"
id: 58
category: "Kubernetes Platform"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - kubernetes-platform
  - interview-questions
---

# How do you design node pools and scheduling for mixed workloads?

**Short answer:** Create a node pool only when workloads genuinely need different hardware, different interruption tolerance, or a node-level boundary - and use taints with tolerations so nothing lands there accidentally. Then let requests, priority classes, and topology spread do the rest inside the pool. The failure mode at both extremes is real: one pool for everything means batch jobs evict APIs, and a pool per team means stranded capacity everywhere.

## Detail

**Legitimate reasons for a separate pool:**

- **Different hardware** - GPUs, ARM versus x86, high-memory instances, local NVMe.
- **Different interruption tolerance** - spot or preemptible capacity for workloads that can be killed, on-demand for those that cannot.
- **A node-level boundary** - a tenant whose bursts were evicting neighbours, or a workload that must not share a kernel.
- **Platform components** - a small on-demand pool for gateway and ingress controllers, CoreDNS, and telemetry agents, so they are never displaced by tenant workloads or preempted with spot capacity.
- **Compliance** - nodes in a specific zone, or with a specific image.

**Taint the pool, tolerate in the workload.** A taint means nothing schedules there unless it explicitly tolerates it. A common mistake is using only node selectors or affinity: that directs your workload to the pool but does nothing to stop other workloads landing on it, so your expensive GPU nodes fill with unrelated pods. Taints plus tolerations for exclusion, node affinity or selectors for attraction - both, not either.

**Spot capacity needs to be designed for, not just selected.** Interruption handling means a termination handler that drains the node, pod disruption budgets so replicas are not all removed at once, spread across instance types and zones so one capacity shortage does not take everything, and a fallback to on-demand. A platform should express this as a tier property - "this workload tolerates interruption" - rather than making each team learn it.

**Autoscaling has two layers, and they solve different problems.** The horizontal pod autoscaler adds Pods; the cluster autoscaler or a just-in-time provisioner such as Karpenter adds nodes. Both are needed, and the interesting failure is when Pods are pending because no node can host them - too large to fit any instance type, or blocked by a topology constraint that cannot be satisfied. Just-in-time provisioners reduce this by choosing an instance type to fit the pending Pods rather than scaling a fixed pool, which also improves bin-packing. Karpenter (1.x, GA) also consolidates under-used nodes and, on AWS with its interruption queue configured, handles spot interruption notices itself, which removes the separate termination handler from the list above.

**Bin-packing versus resilience is a genuine trade-off.** Tight packing saves money and increases the impact of losing one node. Topology spread constraints across nodes and zones cost some efficiency and are almost always worth it for anything user-facing - and should be a platform default derived from the service tier rather than an option teams remember.

**Reserve headroom deliberately.** If a pool is at 95% utilisation, a node failure has nowhere to reschedule, and scaling up takes minutes you may not have. Explicit headroom - often implemented as low-priority placeholder Pods that real workloads preempt - buys instant capacity at a known cost.

**The platform's job is to hide most of this.** Developers should say `size: large` and `interruptible: true`, and the platform should translate that into the right pool, tolerations, priority class, spread constraints, and disruption budget. Teams learning taint syntax is a sign the abstraction is missing.

## Example

```text
Four pools for one production cluster - each justified by a distinct need.

POOL: system            on-demand, 3 nodes, taint platform=true:NoSchedule
  runs: gateway controllers, CoreDNS, telemetry agents, policy webhooks
  why:  platform components must never be preempted or displaced by tenants.
        This is the pool that keeps the cluster diagnosable during an incident.

POOL: general           on-demand, autoscaled 6-40, no taint
  runs: tier 1-2 stateless services (the default landing place)
  why:  the common case; no taint so the default needs no toleration

POOL: burst             spot, autoscaled 0-60, taint interruptible=true:NoSchedule
  runs: batch jobs, CI runners, async consumers, preview environments
  why:  large cost saving for workloads that tolerate being killed.
        Requires: termination handler, PDBs, spread across 6 instance types.

POOL: gpu               on-demand, autoscaled 0-8, taint nvidia.com/gpu=true:NoSchedule
  runs: inference and training
  why:  specialised expensive hardware; the taint is what stops ordinary pods
        occupying nodes that cost many times a general node.
        Allocation within the pool: device plugin counts, or DRA claims
        (GA in 1.34) when workloads must select GPUs by attribute.

Deliberately absent: a pool per team. Node pools are a hardware and interruption
boundary, not a tenancy boundary - tenancy is namespaces, quotas, and priority.
```

```yaml
# What the platform generates from `size: large` + `interruptible: true`.
# The developer wrote two fields; none of this is their concern.
apiVersion: apps/v1
kind: Deployment
metadata: { name: reindex-worker, namespace: team-search }
spec:
  replicas: 6
  template:
    spec:
      priorityClassName: tier-3-batch # loses first under contention
      terminationGracePeriodSeconds: 120 # Pod-level field; spot reclaim: finish in-flight work
      tolerations:
        - key: interruptible # exclusion handled by the taint
          operator: Equal
          value: "true"
          effect: NoSchedule
      affinity:
        nodeAffinity: # attraction handled separately
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - { key: platform.example.com/pool, operator: In, values: [burst] }
      topologySpreadConstraints: # one zone or node cannot take it all out
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway # batch: prefer, do not block
          labelSelector: { matchLabels: { app: reindex-worker } }
      containers:
        - name: worker
          resources:
            requests: { cpu: "2", memory: 8Gi }
            limits: { memory: 10Gi } # memory limit set; CPU limit deliberately not
```

## Interview tips

- Give the four legitimate reasons for a pool, and state clearly that a pool is a hardware and interruption boundary, not a tenancy boundary. That distinction is frequently confused.
- "Taints for exclusion, affinity for attraction - you need both" is the concrete technical point, along with why node selectors alone leave your GPU pool open to anything.
- For spot, list what it actually requires - termination handling, disruption budgets, instance-type diversity, on-demand fallback. Candidates who just say "use spot to save money" have not run it.
- Naming the pending-Pod failure mode, and just-in-time provisioning as the mitigation, shows real autoscaling experience. For the GPU pool specifically, see [running GPU and AI workloads](./how-do-you-run-gpu-and-ai-workloads-on-a-kubernetes-platform.md).
- Close on the platform hiding all of it: `size` and `interruptible` in, tolerations and spread constraints out. If developers are learning taint syntax, the abstraction is missing.

---

[⬅ Back to Kubernetes Platform](./README.md) · [All topics](../README.md)
