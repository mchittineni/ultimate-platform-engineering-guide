---
title: "How do you design a hybrid platform spanning on-premises and cloud?"
id: 195
category: "Multi-Cloud and Hybrid Platforms"
difficulty: "Advanced"
tags:
  - platform-engineering
  - multi-cloud-and-hybrid-platforms
  - interview-questions
---

# How do you design a hybrid platform spanning on-premises and cloud?

**Short answer:** Give both environments the same declarative interface and the same delivery mechanism, and accept that the capabilities behind that interface will differ - on-premises has no managed database service and no elastic capacity. Then design carefully around the link between them: it has latency, finite bandwidth, and a failure mode, so any synchronous dependency crossing it is a reliability decision. The common mistake is treating on-premises as a cloud region with a slow network.

## Detail

**Why hybrid exists.** Usually a regulatory or contractual requirement to keep specific data or workloads on owned infrastructure; sometimes hardware that cannot be replicated in a cloud; sometimes a large existing investment being amortised. It is rarely chosen for its own sake, and the platform's job is to make the on-premises estate feel like a first-class target rather than an exception everyone works around.

**Unify the interface, not the capabilities.** A team should declare a service the same way and deploy it the same way regardless of target. What differs is what is available: on-premises, a database is something you operate, capacity is fixed, and load balancing is likely appliance-based. Expressing the target as a placement property in the service specification - and letting the platform resolve it - is what keeps this manageable.

**Kubernetes is the practical unifying layer**, because it runs in both places with the same API. That gives you one deployment mechanism, one policy engine, one observability integration, and one set of team-facing concepts. It does not unify storage, load balancing, identity, or capacity - and being clear about that boundary is the difference between a working hybrid platform and a disappointing one.

**The link is the defining constraint.** A dedicated interconnect gives you predictable latency and bandwidth; a VPN gives you neither. Either way it is finite and it can fail. The design rules that follow:

- Keep synchronous request paths on one side of the link where possible.
- Prefer asynchronous, replayable communication across it.
- Assume it will be unavailable and decide what each side does then - which usually means each side must be able to serve its own traffic degraded rather than failing.
- Watch bandwidth for data-heavy patterns; a backup or a replication stream can saturate the link and degrade everything else sharing it.

**Address planning must be done once, globally.** On-premises ranges, cloud ranges, and anything from an acquisition must not overlap. Overlaps are extremely painful to remediate after workloads exist, and hybrid is where they most often surface.

**Identity should be one system.** Federate cloud access from the same identity provider that governs on-premises, so a person has one identity and one lifecycle. Two identity systems means two joiner-mover-leaver processes, and the accounts that get missed are the ones that matter.

**Be honest about capability gaps rather than papering over them.** On-premises typically has no managed database, no elastic scaling, no serverless option, and slower provisioning. The platform should present those gaps clearly - "a database here is operated by the platform team with these characteristics" - rather than offering an interface that looks identical and behaves differently. False equivalence is worse than a documented difference.

**Consider the vendor extensions.** All three major providers offer ways to run their control plane or services on your hardware - AWS Outposts and EKS Hybrid Nodes (on-premises machines joined as nodes to an EKS control plane in the cloud), Azure Local (formerly Azure Stack HCI) and Azure Arc, and Google Distributed Cloud in connected and air-gapped forms. These can genuinely narrow the capability gap at the cost of dependency on that provider in your own data centre, which is a trade to make deliberately - and it does not remove the link constraint.

**Check the licence and maintenance status of anything you self-host.** On-premises is where open-source substitutes for managed services cluster, and they change underneath you: the MinIO community edition, once the default S3-compatible store for on-premises estates, went into maintenance mode in December 2025 and its repository was archived in 2026. Treat each self-hosted substitute as a dependency with an owner and an exit plan.

## Example

```text
One interface, two sets of capabilities, one link between them.

  UNIFIED (identical for a team)
    service specification and its schema
    delivery: GitOps reconciliation into both estates
    policy: the same admission policy bundle
    observability: OpenTelemetry to the same backend
    identity: one provider, federated to cloud and governing on-premises
    catalogue, ownership, on-call routing

  DIFFERENT (behind the interface, and stated plainly)
                          ON-PREMISES                 CLOUD
    database              platform-operated Postgres  managed, with PITR
                          cluster; no PITR to a
                          point in seconds
    capacity              fixed; a quota request       elastic; autoscaled
                          means a hardware decision
    load balancing        appliance-based; VIP         managed LB, per-service
                          allocation is a request
    object storage        Ceph RGW or an S3 appliance  native, effectively unlimited
    serverless            none                         available
    provisioning time     hours to weeks for capacity  minutes

  The platform documents these as capability differences. It does NOT offer an
  identical-looking interface that behaves differently - false equivalence is
  worse than a documented gap.
```

```yaml
# Placement as a property. The platform resolves it; the team does not choose a
# deployment mechanism.
apiVersion: platform.example.com/v1
kind: Service
metadata: { name: claims-processor }
spec:
  owner: group:team-claims
  tier: 1
  placement:
    target: on-premises # on-premises | cloud | either
    reason: "policyholder medical data - regulatory requirement, see ADR-0021"
  runtime:
    image: registry.internal.example.com/claims-processor@sha256:9f2c8b1d...
    size: medium
  dependencies:
    - postgres: { size: medium, backups: daily }
      # Resolved to the platform-operated cluster on-premises. The capability
      # difference is surfaced at validation time, not discovered in production:
      #   WARNING: on-premises Postgres does not support point-in-time recovery
      #   to a second. RPO is 24h. Acknowledge in the PR to proceed.
  crossLinkDependencies:
    # Anything crossing the link is declared, so it can be reviewed as a
    # reliability decision rather than appearing by accident.
    - service: pricing
      location: cloud
      mode: asynchronous # synchronous would require explicit sign-off
      degradedBehaviour: "queue locally and replay; serve last-known pricing"
```

```text
Link failure design - decided in advance, per direction:

  LINK DOWN. What happens?

  on-premises workloads
    ✓ serve their own traffic from local databases
    ✓ queue outbound events locally; replay on recovery
    ✗ cannot reach cloud pricing service -> DEGRADED MODE: last-known pricing,
      with a staleness banner and an alert
    ✗ telemetry cannot reach the backend -> buffered locally, shipped on recovery
      (collector disk buffer sized for 4h; alert at 2h)

  cloud workloads
    ✓ serve their own traffic
    ✗ cannot reach on-premises claims data -> requests for those endpoints fail
      fast with a clear error rather than timing out
    ✗ GitOps cannot reconcile on-premises -> deploys to that side pause. Correct:
      a control-plane function should stop change, not stop serving.

  BANDWIDTH - the quieter failure
    the nightly on-premises backup replicating to cloud object storage saturated
    the link and degraded synchronous calls for 40 minutes
    -> rate-limit bulk transfers, schedule them off-peak, and give interactive
       traffic priority on the link. Capacity is finite in a way cloud
       networking usually is not.
```

## Interview tips

- The framing that lands: unify the interface, not the capabilities, and never present false equivalence. A documented capability gap is better than an identical-looking interface that behaves differently.
- Name Kubernetes as the practical unifying layer and be immediately precise about what it does not unify - storage, load balancing, identity, capacity.
- "The link is the defining constraint" with the four design rules is the core technical content. Preferring asynchronous communication across it and deciding degraded behaviour in advance is what interviewers want.
- Bandwidth as a quieter failure than an outage - a backup saturating the link and degrading interactive traffic - is a specific, credible detail.
- Global address planning done once, because overlaps surface in hybrid and are extremely painful to remediate.
- One identity system, because two means two joiner-mover-leaver processes and the missed accounts are the ones that matter.
- Mention the vendor on-premises extensions as a deliberate trade: they narrow the capability gap and add a provider dependency inside your data centre, and they do not remove the link constraint.

---

[⬅ Back to Multi-Cloud and Hybrid Platforms](./README.md) · [All topics](../README.md)
