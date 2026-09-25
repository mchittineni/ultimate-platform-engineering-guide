---
title: "How do you find and remove idle platform cost?"
id: 230
category: "Platform FinOps"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-finops
  - interview-questions
---

# How do you find and remove idle platform cost?

**Short answer:** Look for resources that exist without a consumer - orphaned volumes and addresses, environments nobody destroyed, over-provisioned requests reserving capacity nobody uses, non-production running overnight, and retention paying to store data nobody queries. Then make removal automatic rather than a periodic clean-up, because a manual sweep finds the same waste again six months later. The largest single line is usually over-provisioned resource requests, and the easiest is non-production running out of hours.

## Detail

**Idle cost is structurally different from inefficient cost.** An over-large instance is inefficiency; a volume attached to nothing is pure waste with no offsetting benefit. Waste is easier to remove because there is no trade-off to negotiate - which makes it the right place to start, and the reason to be systematic about finding it.

**The categories, roughly by size in a typical estate:**

| Category                               | Why it accumulates                                        |
| -------------------------------------- | --------------------------------------------------------- |
| Over-provisioned resource requests     | Requests reserve capacity; nobody revisits the guess      |
| Non-production running out of hours    | Nothing turns it off                                      |
| Orphaned storage and addresses         | Deletion did not include dependent resources              |
| Ephemeral environments never destroyed | Reaping missing or single-triggered                       |
| Over-retained telemetry                | Retention set once, never reviewed against query patterns |
| Idle cluster headroom beyond need      | Buffer chosen once, never re-derived                      |
| Old snapshots and images               | No retention policy                                       |
| Unused commitments and licences        | Not released when the workload went away                  |
| Idle GPUs                              | Held for scarcity reasons, allocated but not active       |

**Over-provisioned requests are usually the largest and least visible.** In Kubernetes, a request reserves capacity whether or not it is used, so a service requesting 2 CPU and using 200 millicores is paying for 2 while consuming a tenth of that. Because the pod is healthy, nothing surfaces it. Comparing requests against observed usage at a high percentile across the estate is the highest-value analysis available, and it is often startling the first time.

**Recommend, do not silently right-size.** Automatically reducing requests can cause throttling or eviction for a workload with spiky behaviour. The good pattern is a recommendation with the evidence attached and a pull request the team can review - the platform does the work, the team retains the judgement. For low-tier workloads, automatic adjustment is more defensible - and less disruptive than it used to be, because in-place pod resize is GA in Kubernetes 1.35 and the Vertical Pod Autoscaler's `InPlaceOrRecreate` mode can change requests without recreating the pod in most cases. See [What is rightsizing?](./what-is-rightsizing.md).

**Non-production out of hours is the easiest large saving.** Development and staging environments running continuously for a workday's use is a large multiple of waste, and scale-to-zero or scheduled shutdown removes most of it. The cost is a cold start for the first person in each morning, which is trivially acceptable.

**Orphaned resources come from incomplete deletion.** A deleted workload leaves its volume; a deleted environment leaves its address; a deleted service leaves its load balancer. The durable fix is making teardown complete - owner references and reaping in the deletion path - rather than sweeping afterwards. A sweep is a symptom that the deletion path is incomplete.

**Retention is worth reviewing against actual query behaviour.** If nobody queries logs older than five days, paying for thirty days of hot storage is waste. Instrumenting query age distribution and setting retention from it, tiered by service tier, is more defensible than either a guess or a uniform policy.

**Automate the removal, with a grace period and a notification.** Anything unattached or unused for a defined period gets tagged, its owner notified, and then reclaimed unless someone objects. That converts waste from a recurring project into a property of the system. Without automation you will find the same categories again next year.

**Track waste as a metric and publish it.** Estimated waste as a share of spend, trending down, is the evidence that the automation is working. And when a category stops shrinking, that is where to look next.

## Example

```text
A waste audit - the categories, and the fix that makes each one not come back.

  $ platform waste report

  OVER-PROVISIONED REQUESTS                          est. 18% of compute spend
    requests vs p95 observed usage, across 218 services
      142 services request >2x their p95 usage
      31 services request >5x
      worst: team-data/etl-runner requests 8 CPU, p95 usage 0.4 CPU
    FIX: recommendation PRs with the evidence attached. Tier 3 auto-adjusted;
         tier 1-2 recommended only, because spiky workloads can be throttled or
         evicted by an automatic reduction.
    -> the largest line, and invisible because every pod is healthy.

  NON-PRODUCTION OUT OF HOURS                        est. 11% of total spend
    dev and staging running 168h/week for ~45h of use
    FIX: scale-to-zero after 20m idle, wake on first request. Cold start ~8s for
         the first person each morning - trivially acceptable.
    -> the easiest large saving in almost any estate.

  ORPHANED RESOURCES                                       $4,100/month
    unattached volumes ................ 61   (from deleted workloads)
    unassociated addresses ............ 18
    load balancers with no backends .... 7
    empty node groups .................. 3
    FIX: not a sweep - fix the DELETION PATH. Owner references and volume reaping
         in teardown. A sweep is a symptom that deletion is incomplete.

  EPHEMERAL ENVIRONMENTS NEVER DESTROYED                   $2,900/month
    23 preview environments with no open pull request
    FIX: multiple reap triggers (PR closed, TTL, idle, weekly orphan sweep).
         A single trigger always leaves a class of survivors.

  OVER-RETAINED TELEMETRY                                  $9,400/month
    logs retained 30d; 98% of queries are for data <5 days old
    FIX: retention derived from measured query-age distribution, tiered by
         service tier. Tier 3 -> 7d, tier 1 -> 30d.
    -> defensible because it is derived from behaviour, not guessed.

  IDLE CLUSTER HEADROOM BEYOND NEED                        $6,200/month
    buffer sized for 3 node failures; the SLO justifies 1 plus scale-up time
    FIX: re-derive the buffer from the actual requirement, then keep it under
         review. Absorbed by the platform, so it is OUR incentive to get right.

  STALE SNAPSHOTS AND IMAGES                               $3,300/month
    snapshots older than 1 year with no restore ever performed
    preview-build images retained indefinitely
    FIX: retention policies. 7d for preview images.

  UNRELEASED COMMITMENTS AND LICENCES                      $1,800/month
    3 licences for a departed workload; 1 commitment slice unused
    FIX: release in the offboarding path, not in an annual review.
```

```yaml
# Automate the reclamation - grace period, notification, then reclaim. This is
# what stops the same categories reappearing next year.
apiVersion: platform.example.com/v1
kind: WastePolicy
metadata: { name: orphaned-resources }
spec:
  rules:
    - name: unattached-volumes
      match: { kind: Volume, attached: false, ageDays: ">7" }
      actions:
        - { at: 7d, do: tag, value: "reclaim-candidate" }
        - { at: 7d, do: notify, target: owner-from-tags }
        - { at: 14d, do: snapshot } # cheap insurance before deletion
        - { at: 21d, do: delete }
      objectionWindow: 14d # an owner can keep it, with a reason and a review date

    - name: preview-environment-orphans
      match: { kind: Environment, type: ephemeral, owningPullRequest: closed }
      actions:
        - { at: 0h, do: delete } # no grace period needed; the PR is closed

    - name: idle-nonproduction
      match: { kind: Service, environment: "!production", idleMinutes: ">20" }
      actions:
        - { at: 0m, do: scale-to-zero } # wake on first request
```

```text
Waste as a published metric - the evidence that automation is working, and the
pointer to what to fix next.

  QUARTER    ESTIMATED WASTE   % OF SPEND   NOTE
  2025-Q4        $58,000          31%       first audit; nothing automated
  2026-Q1        $34,000          17%       scale-to-zero + env reaping shipped
  2026-Q2        $21,000          10%       retention derived from query behaviour
  2026-Q3        $19,000           8%       request recommendations landing slowly

  Category not shrinking: over-provisioned requests. 142 services still >2x.
  -> the recommendation PRs are correct but compete with product work. Next step:
     auto-adjust tier 3 (done), and make the recommendation appear in the PR that
     changes the service rather than as a separate notification.
     The category that stops shrinking is where to look next.
```

## Interview tips

- Distinguish waste from inefficiency: waste has no offsetting benefit, so there is no trade-off to negotiate, which is why it is the right place to start.
- Over-provisioned requests as the largest and least visible line is the answer interviewers most want, and the reason - requests reserve capacity while the pod looks healthy - is what makes it invisible.
- "Recommend, do not silently right-size" shows judgement: an automatic reduction can throttle or evict a spiky workload. Auto-adjusting only low tiers is the balanced position.
- Non-production out of hours as the easiest large saving, with the trivial cold-start cost, is a quick concrete win to name.
- For orphaned resources, say the fix is the deletion path rather than a sweep, and that a sweep is a symptom of incomplete teardown. That is the systemic answer.
- Deriving retention from measured query-age distribution rather than guessing is more defensible and is a detail few candidates offer.
- Close on automation with a grace period and on publishing waste as a trending metric, with the observation that the category which stops shrinking tells you where to look next.

---

[⬅ Back to Platform FinOps](./README.md) · [All topics](../README.md)
