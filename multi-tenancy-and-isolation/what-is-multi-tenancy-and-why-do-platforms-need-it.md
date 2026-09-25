---
title: "What is multi-tenancy and why do platforms need it?"
id: 40
category: "Multi-Tenancy and Isolation"
difficulty: "Beginner"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - interview-questions
---

# What is multi-tenancy and why do platforms need it?

**Short answer:** Multi-tenancy means several independent groups - tenants - share the same underlying infrastructure while each behaves as if it had its own. Platforms need it because giving every team its own clusters, accounts, and tooling is expensive and slow to operate, while sharing without isolation means one team's mistake becomes everyone's outage. Multi-tenancy is the discipline of sharing the cost without sharing the blast radius.

## Detail

**The problem it solves.** An internal platform typically serves dozens or hundreds of product teams. If each team got a dedicated cluster, the platform team would be upgrading, patching, and monitoring hundreds of clusters, most of them mostly idle. If everyone simply deployed into one big shared space with no rules, a single runaway job could starve the rest, a single misconfigured role could expose another team's secrets, and nobody could tell who was paying for what. Multi-tenancy sits between those extremes.

**Four things a tenant expects from the boundary.** Whatever the implementation, isolation is judged on the same questions:

| Property          | What it means for the tenant                             | Typical mechanism                         |
| ----------------- | -------------------------------------------------------- | ----------------------------------------- |
| Access isolation  | Other tenants cannot read or change my things            | RBAC, cloud IAM, scoped workload identity |
| Resource fairness | Another tenant's spike does not slow me down             | Quotas, limit ranges, priority classes    |
| Network isolation | Other tenants cannot reach my services unless I allow it | Default-deny network policy               |
| Accountability    | My usage and cost are attributed to me, and only me      | Labels, tags, per-tenant cost reporting   |

**It is a spectrum, not a switch.** The cheapest form is sharing a single application process, separated only by code. Next comes a namespace per team in a shared Kubernetes cluster, then dedicated node pools, then a cluster per tenant, and finally a separate cloud account or project per tenant. Each step up gives stronger isolation and costs more money and operational effort. The deeper comparison lives in [What tenancy models can a platform offer?](./what-tenancy-models-can-a-platform-offer.md).

**Soft versus hard multi-tenancy.** Soft multi-tenancy assumes tenants are cooperative but fallible - internal teams who might ship a memory leak, not an exploit. Hard multi-tenancy assumes a tenant could be hostile, for example when running customer-supplied code. The same cluster setup that is perfectly adequate for the first is inadequate for the second, because tenants in one cluster still share a kernel and a control plane. Knowing which case you are in is the single most important decision.

**Who the user is.** The tenant is an engineering team using the platform. What multi-tenancy saves them is waiting: a new team gets a working, isolated space in minutes rather than a ticket queue for a new cluster, and they do not have to become Kubernetes or cloud networking experts to be safe. What it saves the platform team is running one fleet well instead of many fleets badly.

**The trade-off to state out loud.** Shared infrastructure gives better utilisation and one upgrade path, but it concentrates risk: a bad cluster-wide change affects every tenant at once, and isolation is only as good as its weakest control. Platforms accept that risk for most teams and give a harder boundary to the few that have a stated reason, such as regulatory scope or untrusted code.

## Example

```text
A platform serving 40 product teams - what multi-tenancy looks like in practice.

Without multi-tenancy                      With multi-tenancy
-----------------------------------------  -----------------------------------------
40 clusters, 1 per team                    3 shared clusters (dev, staging, prod)
40 upgrade cycles per Kubernetes release   3 upgrade cycles
Most clusters under 20% utilised           Shared capacity, far higher utilisation
New team waits days for a cluster          New team gets a namespace set in minutes

What each team gets in each shared cluster:
  namespace         team-checkout           (name scope, RBAC and quota target)
  RBAC              team-checkout group -> edit in its own namespace only
  ResourceQuota     40 CPU / 80Gi requested, 200 pods
  NetworkPolicy     default deny, DNS and telemetry allowed
  labels            tenant=team-checkout    (drives cost reports and offboarding)

Exceptions, each with a recorded reason:
  payments          dedicated cluster       (keeps PCI audit scope contained)
  ml-inference      dedicated GPU node pool (bursty, expensive hardware)
```

## Interview tips

- Define it in one sentence - shared infrastructure, isolated experience - then say why platforms need it: cost and operational load on one side, blast radius on the other.
- Name the four properties (access, fairness, network, accountability). It shows you think about isolation as more than "put them in different namespaces".
- Distinguish soft from hard multi-tenancy early. Interviewers often follow up with "what if the tenants were customers running their own code?"
- Mention that the right answer is usually mixed: most teams share, a few get stronger boundaries for a written reason.
- Expect a follow-up on the limits of namespaces; see [What does a Kubernetes namespace isolate, and what does it not?](./what-does-a-kubernetes-namespace-isolate-and-what-does-it-not.md).

---

[⬅ Back to Multi-Tenancy and Isolation](./README.md) · [All topics](../README.md)
