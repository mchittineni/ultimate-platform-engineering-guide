---
title: "What is a blue-green deployment?"
id: 95
category: "Progressive Delivery and Feature Flags"
difficulty: "Beginner"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# What is a blue-green deployment?

**Short answer:** Blue-green keeps two complete copies of a service: "blue" serves all live traffic while "green", running the new version, is deployed and tested alongside it with no users on it. When green is verified, a router switches all traffic from blue to green in one step, and blue is kept running for a while so switching back is equally quick. It trades extra capacity for a near-instant, all-or-nothing cut-over and rollback.

## Detail

**The mechanism.** There are three moving parts:

1. **Two environments** that are identical except for the version - same size, same configuration, same dependencies.
2. **A router** in front of them: a load balancer target group, a DNS record, a Kubernetes Service selector, or a Gateway API route. It points at exactly one colour at a time.
3. **A switch** - changing that pointer. Rollback is the same operation in reverse.

Before the switch, green can be tested through a separate preview address using smoke tests, synthetic transactions, and sometimes internal users. Nothing about green is visible to customers until the pointer moves.

**How it differs from a canary.** A canary exposes a small share of real traffic and ramps gradually; blue-green exposes nothing and then everything. That makes blue-green simpler to reason about - there is never a mix of versions serving users - but it means the first real production traffic the new version sees is all of it. Many teams combine them: test green through the preview, then shift traffic to it in weighted steps rather than all at once, which is effectively a canary with a fully warmed environment.

**Where blue-green is the better fit.**

- Services where mixing versions is dangerous, such as a protocol change between client and server that cannot run side by side.
- Low-traffic services where a canary would take too long to gather a signal.
- Releases that need a hard cut-over at a scheduled time, with a rehearsed rollback.

**The trade-offs.**

- **Double capacity.** Two full environments run during the release. On Kubernetes this is usually temporary - green scales up, the switch happens, blue scales down after a grace period - but you need the headroom, including any cluster autoscaling time.
- **The database is shared.** Blue and green almost always point at the same database, so the schema must work for both versions at once. Use expand-and-contract migrations: add new columns before the switch, remove old ones only after blue is gone. A migration that breaks the old version makes rollback impossible, which defeats the point.
- **Long-lived connections and in-flight work.** WebSockets, streaming requests, and queue consumers on blue do not move just because the router did. Plan for draining, and make sure only one colour consumes from a queue at a time or both will process messages.
- **Caches and sessions.** If blue and green keep sessions in memory, users are logged out at the switch. Keep session state external.
- **Instant rollback only covers behaviour.** Switching back to blue stops the new version, but any data green already wrote in a new shape remains.

**Who uses it, and the platform's part.** Service teams use it for releases that need a clean cut-over. The platform provides the tooling so the switch is a routine, audited operation rather than a hand-edited load balancer: a rollout controller strategy, a preview endpoint pattern, pre-promotion checks, and a default grace period before the old colour is scaled down. The platform also owns the capacity headroom that makes double-sized releases possible without a ticket.

## Example

```yaml
# Blue-green with Argo Rollouts. `checkout` is the live Service, `checkout-preview`
# points at the new version for testing. Promotion flips the live Service selector.
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: checkout
  namespace: team-payments
spec:
  replicas: 6
  selector:
    matchLabels: { app: checkout }
  template:
    metadata:
      labels: { app: checkout }
    spec:
      containers:
        - name: checkout
          image: registry.example.com/checkout:2.0.0
  strategy:
    blueGreen:
      activeService: checkout
      previewService: checkout-preview
      autoPromotionEnabled: false # a human or pipeline promotes after checks
      prePromotionAnalysis:
        templates:
          - templateName: smoke-tests # must pass against the preview first
      scaleDownDelaySeconds: 1800 # keep the old colour for 30 min of fast rollback
```

```text
The release, as the team runs it:

  $ kubectl argo rollouts get rollout checkout -n team-payments
    Status:  Paused (BlueGreenPause)
    Active:  checkout-7c9f  (1.9.4)   <- blue, all live traffic
    Preview: checkout-5d2a  (2.0.0)   <- green, smoke tests passed

  $ kubectl argo rollouts promote checkout -n team-payments
    Active:  checkout-5d2a  (2.0.0)   <- traffic switched in one step
    Old ReplicaSet kept for 1800s

  # If the error rate rises after the switch:
  $ kubectl argo rollouts undo checkout -n team-payments
```

## Interview tips

- Describe the three parts - two environments, a router, a pointer switch - and that rollback is the same switch in reverse.
- Contrast it with a canary in one sentence: nothing and then everything, versus a small share ramped up.
- The shared database is the classic follow-up. Answer with expand-and-contract migrations and the point that a schema that breaks blue removes your rollback.
- Mention the less obvious traps - queue consumers on both colours, long-lived connections, in-memory sessions. They show operational experience.
- Name the user and the platform's role: teams get an audited, one-command cut-over; the platform supplies the controller, preview pattern, and capacity headroom.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
