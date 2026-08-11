---
title: "What is the difference between a control plane and a data plane in a platform?"
id: 16
category: "Platform Architecture"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-architecture
  - interview-questions
---

# What is the difference between a control plane and a data plane in a platform?

**Short answer:** The control plane decides what should exist and makes it so - it accepts declared intent, reconciles it, and manages lifecycle. The data plane is what actually serves traffic or does the work. The distinction matters because it tells you what your users can survive: a control plane outage should stop changes, not stop serving. Any design where the control plane sits in the request path has turned a management component into a production dependency.

## Detail

**The separation, using Kubernetes as the reference.** The API server, scheduler, and controllers form the control plane; the kubelet and the running containers form the data plane. Kill the API server and running Pods keep serving traffic - you simply cannot make changes. That property is deliberate and is the model to copy.

**Why it is the first question to ask about any platform component.** For every piece you build or adopt, ask: is this in the request path? If yes, it needs data-plane reliability - typically an order of magnitude better than your management tooling, plus its own capacity planning and failure isolation. If no, you can accept planned downtime and a simpler operational model.

**Components that catch people out.** Some things look like control plane and are not:

| Component                       | Plane       | Consequence of failure                           |
| ------------------------------- | ----------- | ------------------------------------------------ |
| GitOps reconciler (Argo, Flux)  | Control     | No new deploys; running workloads unaffected     |
| Ingress controller              | **Data**    | Traffic stops - this is a production dependency  |
| Service mesh control plane      | Control     | No config changes; existing proxies keep routing |
| Service mesh sidecar / proxy    | **Data**    | That workload's traffic stops                    |
| Secret store, read at pod start | Control-ish | New pods fail to start; running pods fine        |
| Secret store, read per request  | **Data**    | Requests fail - avoid this design                |
| Feature flag SDK, local eval    | Control     | Rules go stale; evaluation continues             |
| Feature flag SDK, remote eval   | **Data**    | Provider latency and outages hit every request   |
| Auth token issuance in-path     | **Data**    | Everything fails                                 |

The pattern in the rows that surprise people: a component becomes data plane the moment something in the request path synchronously depends on it. Reading a secret at startup and caching it is control plane; reading it per request is not.

**Design consequences for the platform team.** Data-plane components need capacity headroom, per-tenant isolation, and rollout care - you cannot restart them all at once. Control-plane components can be upgraded during the day, can be briefly unavailable, and should be built so that their unavailability is obvious and safe rather than silently degrading. Argo CD being down should stop deploys loudly, not partially apply.

**The failure mode to avoid: fail-closed data plane dependencies.** An admission webhook that rejects Pods when it cannot be reached will, during its own outage, prevent every Pod in the cluster from starting - including the ones that would fix it. That is a control-plane component with data-plane blast radius, and it is one of the most common self-inflicted platform outages.

**State is what makes control planes hard.** The control plane owns the desired state and usually a record of what it created. Losing that record is worse than losing the process: you can restart a controller, but if it no longer knows it created a database, it may create a second one or orphan the first. This is why control-plane state gets the backup and restore rigour normally reserved for production data.

## Example

```text
Where each component sits, and what an outage of it means for a developer
versus for a customer. The right-hand column is the one that sets your SLO.

                                       developer impact        customer impact
  CONTROL PLANE
    platform API / CRDs                 cannot declare intent   none
    reconciler (Argo CD)                cannot deploy           none
    provisioning controller             cannot get new infra    none
    CI system                           cannot build            none
    portal / catalogue                  cannot browse           none
    policy admission (fail-OPEN)        none                    none

  DATA PLANE
    ingress / load balancer             -                       OUTAGE
    service mesh sidecars               -                       OUTAGE
    DNS                                 -                       OUTAGE
    authentication in request path      -                       OUTAGE
    databases and queues                -                       OUTAGE
    policy admission (fail-CLOSED)      cannot start pods       OUTAGE during any
                                                                scaling or restart

The last row is the trap: identical component, opposite blast radius, decided
by one configuration field.

  failurePolicy: Ignore   # webhook down -> pods start, policy not enforced
  failurePolicy: Fail     # webhook down -> nothing starts, cluster-wide outage

Either can be correct. `Fail` is right for controls you must never bypass, but
only with the webhook made genuinely highly available, excluded from its own
namespace, and with a documented break-glass to remove it.
```

## Interview tips

- The sentence to land: a control plane outage should stop change, not stop serving. Then show you know which of your components violate that.
- Have two or three surprising classifications ready - ingress and mesh sidecars as data plane, remote flag evaluation as data plane. That is what demonstrates real design experience.
- The `failurePolicy` example is an excellent concrete answer to "give me an example of a platform component with the wrong blast radius".
- Mention control-plane state as the hard part - losing the record of what you created is worse than losing the process.
- Expect the follow-up "so what SLO does your control plane need?" - lower than the data plane, and the honest answer is that it should be measured on time-to-deploy rather than availability.

---

[⬅ Back to Platform Architecture](./README.md) · [All topics](../README.md)
