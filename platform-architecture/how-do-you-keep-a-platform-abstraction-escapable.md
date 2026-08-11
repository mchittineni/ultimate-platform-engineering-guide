---
title: "How do you keep a platform abstraction escapable?"
id: 18
category: "Platform Architecture"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-architecture
  - interview-questions
---

# How do you keep a platform abstraction escapable?

**Short answer:** Make the generated output visible, allow targeted overrides of individual pieces without abandoning the whole abstraction, and provide a documented full exit that keeps the service running. The principle is that the abstraction should be the easiest path but never the only path - because the alternative is that every unusual workload becomes a ticket to the platform team, which is the bottleneck the platform existed to remove.

## Detail

**Why leak-proof abstractions fail.** A platform that fully hides Kubernetes works until a workload needs a sidecar, a specific node affinity, a custom probe, or a scheduling constraint. If the interface has no answer, the team's only route is to ask you - and now your queue length determines their delivery speed. This is the single most common technical cause of platform teams becoming bottlenecks.

**The escape hatches, from cheapest to most drastic.** A good platform offers all four, and knowing the ladder is the substance of this answer:

| Level | Mechanism                    | What the developer keeps                    |
| ----- | ---------------------------- | ------------------------------------------- |
| 1     | Inspect the generated output | Everything - this is read-only              |
| 2     | Field-level override         | All platform features except the overridden |
| 3     | Strategic patch / overlay    | Reconciliation, dashboards, policy          |
| 4     | Full eject to raw manifests  | Nothing automatic; the team owns it         |

**Level 1 is non-negotiable and often forgotten.** `platform explain` or `platform render` showing exactly what the platform generated, and ideally why, converts a black box into a teaching tool. It also removes most escape requests outright, because a large fraction of them come from people who cannot tell whether the platform already did the thing they need.

**Level 2 and 3 are where the real design work is.** Allow a team to override the readiness probe or add a volume without abandoning the platform's dashboards, SLOs, and policy compliance. The key constraint is that overrides must be explicit, reviewable, and enumerable - you need to be able to answer "which services override scheduling, and why" because that list is your roadmap.

**Level 4 must exist and must be a clean exit.** Generate the equivalent raw manifests, hand them over, and record that the service left the path. What you must not do is make ejection a cliff where the team loses monitoring and ownership metadata too; that turns leaving into an incident and pressures people to stay on a path that does not fit.

**Escapes need lifecycle, not just permission.** Each override or exemption should record why, who owns it, what responsibility the team accepted, and when it will be reviewed. Otherwise you accumulate hundreds of silent deviations and lose the ability to change anything safely. Expiry dates on exemptions are the mechanism that keeps this from rotting - not to force teams back, but to force a conversation.

**Treat the escape register as product feedback.** If six teams override the same field, the default is wrong. If four eject for the same reason, that is a missing capability with proven demand. Platform teams that treat escapes as violations to be closed learn nothing; teams that read them as a backlog improve fast.

**The genuine limit.** Some things must not be escapable - image signing verification, audit logging, encryption, no public buckets. Those are guardrails, not abstractions, and the honest answer distinguishes them: you can escape the platform's opinions, not its controls.

## Example

```yaml
# Level 2 and 3 in one spec: still a platform Service, still gets SLOs,
# dashboards, and policy - with two explicit, reviewable deviations.
apiVersion: platform.example.com/v1
kind: Service
metadata:
  name: ml-inference
spec:
  owner: group:team-ml
  tier: 2
  runtime:
    image: ghcr.io/example/inference:2.1.0
    size: large

  # Level 2 - field override. Model load takes ~90s; the default probe
  # would restart the pod before it is ready.
  overrides:
    readinessProbe:
      httpGet: { path: /ready, port: 8080 }
      initialDelaySeconds: 120
      failureThreshold: 10
    reason: "Model warm-up is ~90s; default 30s probe causes a restart loop"

  # Level 3 - strategic patch for something the interface does not model.
  # Explicit, reviewed, and enumerable across the fleet.
  patches:
    - target: Deployment
      patch: |
        spec:
          template:
            spec:
              runtimeClassName: nvidia
              nodeSelector: { workload: gpu }
              tolerations:
                - key: nvidia.com/gpu
                  operator: Exists
                  effect: NoSchedule
      reason: "GPU scheduling; platform does not model accelerators yet"
      owner: group:team-ml
      review_by: 2026-09-30
```

```text
Level 1 and 4, as commands - and the register that makes escapes useful:

  $ platform explain ml-inference --show-defaults
      Deployment/ml-inference
        replicas: 3                      <- from tier: 2
        resources: 2000m / 4Gi           <- from size: large
        topologySpreadConstraints: [...]  <- platform default
        readinessProbe: OVERRIDDEN        <- yours, reason recorded
      ...

  $ platform eject ml-inference --out ./k8s
      Wrote 9 manifests. Service marked ejected in the catalogue.
      Retained: catalogue entry, ownership, alert routing, cost tags.
      Lost: automatic upgrades of platform defaults, generated SLO rules.

  $ platform escapes report
      overrides: readinessProbe .......... 11 services   <- DEFAULT IS WRONG. Fix it.
      overrides: resources ...............  4 services
      patches:   GPU scheduling ..........  6 services   <- MISSING CAPABILITY.
                                                            Proven demand; roadmap it.
      ejected: ...........................  2 services
      exemptions expiring in 30 days .....  3
```

## Interview tips

- "Escapable, not escape-proof" plus the bottleneck argument is the core. Interviewers are checking whether you understand why hiding everything backfires.
- The four-level ladder is the structure that makes this answer memorable. Most candidates offer only "we let them write raw YAML if needed".
- Level 1 - showing the generated output - is the cheapest and most overlooked. Volunteering it signals practical experience.
- The escape register as a roadmap input is the senior move: eleven services overriding the same probe means your default is wrong, not that eleven teams are wrong.
- Draw the line at guardrails: platform opinions are escapable, security and compliance controls are not. Without that caveat the answer sounds permissive.

---

[⬅ Back to Platform Architecture](./README.md) · [All topics](../README.md)
