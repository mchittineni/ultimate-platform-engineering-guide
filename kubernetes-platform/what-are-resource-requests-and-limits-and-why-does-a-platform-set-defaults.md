---
title: "What are resource requests and limits, and why does a platform set defaults?"
id: 55
category: "Kubernetes Platform"
difficulty: "Beginner"
tags:
  - platform-engineering
  - kubernetes-platform
  - interview-questions
---

# What are resource requests and limits, and why does a platform set defaults?

**Short answer:** A request is what the scheduler reserves for a container - the node must have that much unreserved capacity before the Pod can land there. A limit is the ceiling the kernel enforces at runtime: exceed the CPU limit and you are throttled, exceed the memory limit and you are killed. A platform sets defaults because a Pod with no requests is invisible to the scheduler, unaccountable for cost, and first to be evicted - and most developers do not know what numbers to write, so the platform should pick sensible ones and let teams override.

## Detail

**Requests drive scheduling, not usage.** The scheduler adds up the requests of every Pod on a node and only places a new Pod if its requests fit into what remains of the node's allocatable capacity. It does not look at actual usage. A node can be 10% busy and still "full" because every Pod requested far more than it uses - which is the most common form of Kubernetes waste. Requests also feed the kernel: CPU requests become cgroup weights, so under contention a container gets CPU in proportion to what it asked for.

**Limits are enforced by the kernel, and CPU and memory behave differently.** CPU is compressible: a container hitting its CPU limit is throttled by the CFS quota and runs slower, which shows up as latency rather than an error. Memory is not compressible: a container exceeding its memory limit is OOM-killed and restarted. That asymmetry is behind the common platform guidance - always set memory requests and limits, always set CPU requests, and think twice before setting CPU limits, because throttling a latency-sensitive service when the node has idle CPU buys nothing.

**QoS classes decide who dies first.** Kubernetes derives a quality-of-service class from what you set:

| QoS class  | How you get it                                         | Under node memory pressure    |
| ---------- | ------------------------------------------------------ | ----------------------------- |
| Guaranteed | Every container has requests equal to limits (CPU+mem) | Evicted last                  |
| Burstable  | At least one request or limit set, not all equal       | Evicted by usage over request |
| BestEffort | Nothing set at all                                     | Evicted first                 |

A BestEffort Pod is the one the kubelet sacrifices when a node runs short of memory. Teams who ship without requests are usually surprised to learn their service was the first thing killed during someone else's traffic spike.

**Why the platform sets defaults.** Left alone, you get three failure modes. Pods with no requests pack too densely, and a busy node starts evicting them. Pods with huge, guessed requests strand capacity and cost money. And without requests, cost attribution and quotas do not work, because both are calculated from requests. Most developers cannot tell you whether their service needs 200m or 2 cores - and they should not have to on day one. So the platform provides:

- **A LimitRange per tenant namespace** that injects default requests and limits into containers that set none, plus minimums and maximums so nobody requests a whole node by accident.
- **A ResourceQuota per namespace** that caps the total a team can request. Once a quota covers CPU or memory, every Pod in that namespace _must_ carry requests - the LimitRange defaults are what keep that from rejecting everything.
- **Size presets in the service specification** - `size: small | medium | large` mapped to tested request and limit values, so a developer picks a T-shirt size rather than a number.
- **Admission validation** that rejects anything that slipped through without requests - see [admission control as a platform lever](./what-is-admission-control-and-how-do-you-use-it-as-a-platform-lever.md).

**Defaults are a starting point, not an answer.** The default is right for nobody in particular. The platform should close the loop: show each team requested versus actual usage, recommend new values (the Vertical Pod Autoscaler in recommendation mode is the usual source), and make changing them a one-line edit. Since Kubernetes 1.35, in-place Pod resize is GA, so CPU and memory can be adjusted on a running Pod without recreating it - which makes automated right-sizing far less disruptive than it used to be.

**The trade-off.** Generous defaults are safe and wasteful; tight defaults are efficient and cause OOM kills and throttling that teams then blame on the platform. Most platforms start moderately generous, measure, and tighten through recommendations rather than by lowering the defaults globally.

## Example

```yaml
# Applied by the platform to every tenant namespace at creation.
apiVersion: v1
kind: LimitRange
metadata: { name: platform-defaults, namespace: team-search }
spec:
  limits:
    - type: Container
      defaultRequest: { cpu: 100m, memory: 256Mi } # injected when a container sets none
      default: { memory: 512Mi } # default memory limit; no default CPU limit, deliberately
      min: { cpu: 10m, memory: 32Mi }
      max: { cpu: "4", memory: 16Gi } # stops accidental whole-node requests
---
apiVersion: v1
kind: ResourceQuota
metadata: { name: team-quota, namespace: team-search }
spec:
  hard:
    requests.cpu: "40"
    requests.memory: 160Gi
    limits.memory: 240Gi
    pods: "200"
```

```text
What a developer sees, and what the platform does with it.

  service.yaml          size: medium
  platform generates    requests: cpu 500m, memory 1Gi
                        limits:   memory 1536Mi  (no CPU limit)
                        QoS class: Burstable

  30 days later, platform right-sizing report for team-search:

  SERVICE          REQ CPU   P95 CPU   REQ MEM   P95 MEM   SUGGESTION
  search-api       500m      410m      1Gi       780Mi     keep
  reindex-worker   2         300m      8Gi       2.1Gi     size: small-highmem
  suggest-api      500m      620m      1Gi       990Mi     raise memory limit (3 OOM kills)

  Requested but unused across the namespace: 9.4 cores, 31Gi.
```

## Interview tips

- State the core distinction crisply: requests are for the scheduler and reserve capacity; limits are enforced by the kernel at runtime. Many candidates blur them.
- Explain the CPU versus memory asymmetry - throttling versus OOM kill - and why many platforms set memory limits but deliberately leave CPU limits off for latency-sensitive services.
- Name the QoS classes and the eviction consequence of BestEffort. That shows you understand requests as a reliability control, not just a cost one.
- Mention that a CPU or memory ResourceQuota forces every Pod to carry requests, and that LimitRange defaults are what make that workable.
- Close on closing the loop: defaults to start, usage-based recommendations after, and in-place resize (GA in 1.35) to apply them without restarts. Cost and quotas both run on requests, which ties this to [cost attribution](../platform-finops/how-do-you-attribute-shared-platform-cost-to-teams.md).

---

[⬅ Back to Kubernetes Platform](./README.md) · [All topics](../README.md)
