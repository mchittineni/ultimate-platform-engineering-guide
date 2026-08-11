---
title: "How do you define SLOs for a platform rather than an application?"
id: 104
category: "Platform Reliability"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-reliability
  - interview-questions
---

# How do you define SLOs for a platform rather than an application?

**Short answer:** Write one SLO per capability, expressed as the outcome the consuming team experiences - time from merge to running in production, time from claim to a usable database, whether a deploy that was requested actually happened - rather than the availability of your components. A platform's users are engineers, so its SLIs measure whether their work completes, and the most important of them are latency and completion measures rather than uptime.

## Detail

**Component availability is the wrong unit.** "Argo CD was up 99.95%" tells a team nothing about whether their deploys worked. The consumer-facing question is whether a merged change reached production within the expected time. A platform can have every component green and still be failing its users - if reconciliation is backed up, or if provisioning is silently retrying, or if the pipeline is queueing.

**Capability-level SLOs are the right granularity.** One per thing a team asks the platform to do, each with an SLI defined from the consumer's side:

| Capability         | SLI                                                             | Shape             |
| ------------------ | --------------------------------------------------------------- | ----------------- |
| Deploy             | Merged change running in production within N minutes            | Latency           |
| Provision          | Claim to usable resource within N minutes                       | Latency           |
| Build              | Pipeline completes within N minutes, no infrastructure failures | Latency + success |
| Environment create | Preview environment ready within N minutes                      | Latency           |
| Secret delivery    | New pods receive credentials successfully                       | Success rate      |
| Telemetry          | Emitted spans queryable within N seconds                        | Freshness         |
| Policy evaluation  | Admission decisions within N ms                                 | Latency           |

**Latency and completion matter more than uptime for control-plane capabilities.** A reconciler being unavailable for two minutes is invisible; a reconciler taking forty minutes to notice a change is a serious platform failure that no availability metric captures. This is the distinctive thing about platform SLOs and the point most worth making.

**Distinguish control plane from data plane targets sharply.** Platform components in the request path - ingress, DNS, service mesh proxies, authentication - need availability targets at least as strong as the services depending on them. Control-plane capabilities need latency and completion targets and can tolerate brief unavailability. Applying one uniform target to both over-invests in the control plane and under-invests in the data plane.

**Measure from the consumer's side.** Instrument the whole path: commit timestamp to the moment the new version is serving traffic, including queueing and reconciliation delay. Measuring your own component's internal processing excludes exactly the delays consumers feel, which is how a platform ends up with green dashboards and unhappy users.

**Set targets from observed behaviour and consumer need,** not from ambition. Measure the current distribution for a few weeks, then choose a target that is achievable and meaningful. And be careful with tier-1 promises: if you commit to a strong deployment target, you are committing to the on-call and engineering investment to sustain it.

**Publish them, and report against them.** An unpublished SLO is a private aspiration. Publishing turns the relationship with teams into a stated expectation, gives you the basis for prioritisation arguments, and - importantly - gives you the standing to say no to work that would jeopardise a target you have committed to.

**Include the meta-SLO.** Whether teams can see the platform's own state during an incident. If your status page and dashboards depend on the platform they describe, they will be unavailable exactly when they are needed.

## Example

```yaml
# One SLO per capability, measured from the consumer's side.
apiVersion: platform.example.com/v1
kind: PlatformSLO
metadata: { name: deploy-latency }
spec:
  capability: deploy
  description: >
    Time from merge on a deployment repository's main branch to the new version
    serving production traffic. Includes CI queueing, image build, reconciliation
    delay, and rollout - i.e. everything the consuming team experiences.
  sli:
    # NOT "argocd_up". The whole path, from the consumer's first action.
    numerator: platform_deploy_completed_total{within="15m"}
    denominator: platform_deploy_requested_total
  objective: 95%
  window: 28d
  # A second objective on the tail: the p50 being fine hides the pain
  additionalObjectives:
    - { percentile: 99, threshold: 45m, objective: 99% }
  consumerVisible: true # published, not private
---
apiVersion: platform.example.com/v1
kind: PlatformSLO
metadata: { name: ingress-availability }
spec:
  capability: ingress
  plane: data # DATA PLANE - availability, and a strong one
  description: "Successful responses through platform ingress, excluding 5xx from the workload itself."
  sli:
    numerator: ingress_requests_total{platform_error="false"}
    denominator: ingress_requests_total
  objective: 99.99% # stronger than any single consumer's target, because
  window: 28d #        every consumer depends on it
```

```text
The SLO set, and what each plane gets:

  DATA PLANE - availability targets, stronger than any consumer's own
    ingress .......................... 99.99% successful responses
    DNS .............................. 99.99% resolution success
    service mesh data path ........... 99.99% successful proxied requests
    authentication in request path .... 99.99%
    -> these must be stronger than the services depending on them, or the
       platform is the ceiling on everyone's reliability

  CONTROL PLANE - latency and completion, brief unavailability tolerated
    deploy ........................... 95% within 15m, 99% within 45m
    provision (database) ............. 95% within 10m
    provision (bucket/queue) ......... 99% within 2m
    preview environment ready ........ 95% within 5m
    pipeline completion .............. 95% within 12m, infra-caused failures <1%
    secret delivery to new pods ...... 99.9% success
    telemetry queryable .............. 99% within 60s
    admission decision ............... 99.9% within 200ms
    -> a reconciler down for 2 minutes is invisible. A reconciler taking 40
       minutes to notice a change is a serious failure that no availability
       metric would catch. This is why these are latency SLOs.

  META
    platform status visible during a platform incident ... 99.9%
    -> hosted OUTSIDE the platform it describes, or it is unavailable exactly
       when it is needed
```

```text
The measurement trap, illustrated:

  WRONG    argocd_reconciliation_duration_seconds
           -> 1.2s p99. Dashboard green. Excludes queueing entirely.

  RIGHT    time from merge commit timestamp to the new version serving traffic
           -> p50 4m, p95 14m, p99 52m
              and during last Tuesday's backlog: p99 was 3h 40m

  Same system, same day. The first metric said nothing was wrong; the second
  matched what teams were reporting. Measure from the consumer's first action,
  not from your component's internal work.
```

## Interview tips

- Lead with the reframe: a platform's users are engineers, so the SLI measures whether their work completes, not whether your components are up.
- "Argo CD was up 99.95% tells a team nothing about whether their deploys worked" is the sentence that makes the point immediately.
- Latency and completion over availability for control-plane capabilities, with the concrete contrast - two minutes down is invisible, forty minutes of reconciliation delay is a serious failure - is the distinctive platform insight.
- Split control plane from data plane targets explicitly, and note that data-plane components must be more reliable than any consumer depending on them, because the platform is otherwise the ceiling on everyone's reliability.
- Measuring from the consumer's first action is the practical detail; measuring your component's internal processing excludes exactly the delays users feel.
- Publishing the SLOs, and using them as the basis for saying no to work that would jeopardise a commitment, shows you understand their organisational function.
- The meta-SLO - status visibility hosted outside the platform - is a memorable close.

---

[⬅ Back to Platform Reliability](./README.md) · [All topics](../README.md)
