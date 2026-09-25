---
title: "What is a canary deployment?"
id: 94
category: "Progressive Delivery and Feature Flags"
difficulty: "Beginner"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# What is a canary deployment?

**Short answer:** A canary deployment runs a new version of a service alongside the current stable version and sends a small share of real traffic to it - say 5% - while comparing its error rate and latency against the stable version. If the canary is healthy, traffic shifts to it in steps until it serves everything; if it is not, traffic returns to the stable version and the canary is removed. The name comes from the canary in a coal mine: a small, early warning before everyone is exposed.

## Detail

**How the traffic split works.** There are two ways to send a fraction of requests to the canary, and the difference matters:

- **Replica ratio.** Run 9 stable Pods and 1 canary Pod behind the same Kubernetes Service. Roughly 10% of requests land on the canary because it is 10% of the endpoints. Simple, but coarse: you cannot get 1% without 100 Pods, and the split is only approximate.
- **Traffic routing.** A service mesh, a Gateway API implementation, or an ingress controller holds a weighted route - 95 to stable, 5 to canary - independent of Pod counts. This gives precise weights and lets you route by header, for example sending internal staff to the canary first.

A rollout controller such as Argo Rollouts or Flagger automates the steps: set the weight, wait, run an analysis, then promote or abort.

**The analysis is the part that makes it safe.** A canary without automated analysis is just a slower deploy that someone has to watch. The controller queries your metrics system (Prometheus, Datadog, CloudWatch and others) at each step and compares the canary with the stable version running at the same time. Comparing against the concurrent stable version rather than yesterday's numbers is important: a traffic spike or an upstream incident then affects both sides equally and is not blamed on your change.

**What a canary is good at catching.** Because the whole binary is new, a canary exercises everything that changed: a dependency upgrade, a new base image, a runtime version bump, a configuration change, a memory leak. These are regressions a feature flag cannot catch, because a flag only protects the code path it wraps.

**The limitations.**

- **Per-user inconsistency.** A user's successive requests can hit either version, so they might see new behaviour on one page and old behaviour on the next. Sticky sessions help but reduce the randomness of the sample. For user-visible behaviour changes, a feature flag is usually better - see [When do you use a feature flag instead of a canary deployment?](./when-do-you-use-a-feature-flag-instead-of-a-canary-deployment.md).
- **Both versions must coexist.** They share the same database and message queues, so schema changes need an expand-and-contract approach where the old version still works against the new schema.
- **Traffic volume.** 5% of a low-traffic service may be a handful of requests an hour, too few to judge. Such services need longer pauses, a higher starting weight, or synthetic traffic.
- **It does not reverse state.** Aborting stops new requests reaching the canary; anything the canary already wrote or sent stays done.

**Who uses it, and the platform's part.** Service teams use canaries on every deploy, often without thinking about it, when the platform makes it the default. The platform installs the rollout controller, provides shared analysis templates tied to each service's service-level objectives, and bakes a canary strategy into the service template. Teams then tune the steps rather than build the machinery. A good platform also exposes the rollout state - current weight, analysis results, abort reason - in the developer portal, so a team does not need cluster access to see why its release stopped.

## Example

```yaml
# The analysis the platform ships once and every team reuses.
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
  namespace: team-payments
spec:
  args:
    - name: service
  metrics:
    - name: success-rate
      interval: 1m
      failureLimit: 2 # two bad readings abort the rollout
      successCondition: result[0] >= 0.99
      provider:
        prometheus:
          address: http://prometheus.monitoring.svc:9090
          query: |
            sum(rate(http_requests_total{service="{{args.service}}",code!~"5.."}[2m]))
            /
            sum(rate(http_requests_total{service="{{args.service}}"}[2m]))
```

```text
A canary catching a regression no flag could have caught:

  checkout 1.5.0 = new JSON library + runtime upgrade, no feature change

  (a second metric in the same template compares canary p99 with stable p99)

  step  weight  p99 canary  p99 stable  success  decision
  1     5%      212ms       141ms       99.7%    latency ratio 1.5 > 1.2 -> ABORT
  -     0%      -           141ms       -        stable serving 100%

  5% of requests saw slower responses for 10 minutes. The team found the
  library regression in the profile, fixed it, and 1.5.1 promoted cleanly.
```

## Interview tips

- Describe the mechanism precisely: two versions running at once, a weighted split of requests, and a comparison between them.
- Distinguish replica-ratio canaries from routed canaries; knowing that 1% needs traffic routing rather than Pods is a good signal.
- Stress automated analysis against the concurrent stable version - that is what turns a gradual deploy into a safe one.
- Say what canaries are uniquely good at (whole-binary regressions) and their weakness (a user may see both versions), and you have answered the likely follow-up about flags.
- Name the platform's role: a controller in every cluster, shared analysis templates, and a canary strategy in the service template by default.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
