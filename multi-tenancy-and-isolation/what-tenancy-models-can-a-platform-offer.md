---
title: "What tenancy models can a platform offer?"
id: 24
category: "Multi-Tenancy and Isolation"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - interview-questions
---

# What tenancy models can a platform offer?

**Short answer:** Tenancy models form a spectrum from shared process to fully separate infrastructure, and each step up buys stronger isolation at higher cost and lower utilisation. In a platform context the tenants are usually internal teams, and the decision is driven by threat model, regulatory obligation, and noisy-neighbour risk - not by a preference for isolation. The right answer is usually mixed: most teams share, and specific workloads get a harder boundary for a stated reason.

## Detail

**The spectrum, from weakest to strongest:**

| Model                         | Boundary               | Isolation strength | Cost and utilisation         |
| ----------------------------- | ---------------------- | ------------------ | ---------------------------- |
| Shared process                | Application logic      | Weakest            | Best utilisation             |
| Shared cluster, namespace     | Kubernetes RBAC, quota | Soft               | Very good                    |
| Shared cluster, node pool     | Node boundary          | Moderate           | Good, some stranded capacity |
| Cluster per tenant            | Control plane          | Strong             | Poor - fixed cost each       |
| Account or project per tenant | Cloud IAM boundary     | Strongest          | Poorest, highest overhead    |

**Namespaces are a soft boundary, and this is the point interviewers probe.** A namespace scopes names and gives you RBAC and quota targets. It does not, by itself, isolate the network, prevent resource contention, or protect against a container escape - because tenants still share a kernel and a control plane. Namespaces plus network policy, resource quotas, limit ranges, and admission control are a reasonable boundary between _trusted_ tenants. They are not a boundary against a hostile tenant.

**Trust level is the decisive variable.** Internal teams are semi-trusted: they might deploy a memory leak, not an exploit. Between semi-trusted tenants, soft multi-tenancy is appropriate and by far the most economical. If your tenants are genuinely untrusted - running customer-supplied code, for instance - then you need either a hard boundary or sandboxed runtimes such as gVisor or Kata Containers, and saying so distinguishes a real answer from a checklist.

**The control plane is a shared resource too.** Tenants in one cluster share the API server and etcd. A tenant generating enormous watch traffic, creating thousands of objects, or hammering the API can degrade everyone - a failure mode that namespaces do nothing about, and which API priority and fairness plus object-count quotas exist to mitigate.

**What actually forces a hard boundary:**

- Regulatory scope you want to contain - PCI, or a workload processing health data where auditing everything is prohibitive.
- Data residency requiring workloads and data in a specific region.
- Genuinely untrusted code.
- Wildly divergent lifecycle needs - a tenant who cannot accept your upgrade cadence.
- Blast radius requirements for the highest-tier workloads.

**Mixed tenancy is normal and should be stated as the answer.** A typical mature platform runs most teams in shared clusters by namespace, one hardened cluster for regulated workloads, dedicated node pools for GPU or memory-heavy tenants, and separate cloud accounts per environment. What matters is that each deviation has a recorded reason - because the count of hard-isolated tenants is a direct multiplier on your operational cost.

## Example

```text
One platform, four tenancy tiers - and the reason each exists.

TIER A - shared cluster, namespace per service        (34 teams, 180 services)
  boundary: namespace + RBAC + ResourceQuota + LimitRange + NetworkPolicy +
            admission policy; PriorityClass by tier
  rationale: semi-trusted internal teams, default for everything
  cost:      highest utilisation; one cluster upgrade serves everyone

TIER B - shared cluster, dedicated node pool          (3 teams)
  boundary: Tier A + taints/tolerations + node affinity
  rationale: GPU inference and a memory-heavy JVM tenant whose bursts were
             evicting neighbours. Node boundary, not control-plane boundary.
  cost:      some stranded capacity in the pool

TIER C - dedicated cluster                            (1 tenant: payments/PCI)
  boundary: separate control plane, separate node groups, restricted egress,
            separate log destination with longer retention
  rationale: keeps PCI audit scope off the other 180 services. The driver is
             audit cost, not a technical fear.
  cost:      full cluster fixed cost + a second upgrade cadence to run

TIER D - dedicated cloud account                      (per environment, plus 1 tenant)
  boundary: cloud IAM boundary, separate VPC, separate billing
  rationale: prod/staging/dev separation; one tenant with EU data residency
  cost:      account vending, network peering, cross-account access plumbing

Deviations from Tier A: 5 of 39 tenants. Each recorded with a reason and an
owner. That ratio is the number to watch - every promotion out of Tier A is a
permanent operational cost.
```

```yaml
# What makes a namespace an actual boundary rather than just a name scope.
# All four of these are required; a namespace with none of them isolates nothing.
apiVersion: v1
kind: ResourceQuota
metadata: { name: tenant-quota, namespace: team-payments }
spec:
  hard:
    requests.cpu: "40"
    requests.memory: 80Gi
    limits.cpu: "80"
    persistentvolumeclaims: "20"
    count/pods: "200" # object counts protect etcd, not just nodes
    count/services.loadbalancers: "2" # each one is a cloud bill
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-ingress, namespace: team-payments }
spec:
  podSelector: {} # every pod in the namespace
  policyTypes: [Ingress] # default deny; allow rules added per service
```

## Interview tips

- Present it as a spectrum with a cost gradient, then say the real answer is mixed tenancy with recorded reasons for each deviation.
- "A namespace is a soft boundary" is the phrase to land, followed by what actually hardens it - quota, limit range, network policy, admission control - and what it still cannot do.
- Shared kernel and shared control plane are the two things namespaces cannot isolate. Naming both, and mentioning API priority and fairness, is a strong signal.
- Distinguish semi-trusted internal teams from untrusted code, and name sandboxed runtimes for the latter. Many candidates miss that trust level is the deciding variable.
- The PCI example is worth having ready because the driver is audit scope rather than technical risk - that nuance reads as real experience.

---

[⬅ Back to Multi-Tenancy and Isolation](./README.md) · [All topics](../README.md)
