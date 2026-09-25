---
title: "How do you stop ephemeral environments becoming a cost problem?"
id: 113
category: "Environments and Ephemeral Infrastructure"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - environments-and-ephemeral-infrastructure
  - interview-questions
---

# How do you stop ephemeral environments becoming a cost problem?

**Short answer:** Make destruction automatic and multi-triggered - pull request closed, TTL expired, idle timeout - scale to zero when nothing is using them, run them on spot capacity, share the expensive dependencies rather than duplicating them per environment, and attribute the cost per team so it is visible. The characteristic failure is not the running environments; it is the orphaned ones that were never destroyed and the shared baseline nobody notices is sized for peak.

## Detail

**Multiple reap triggers, because each one misses cases.** Pull request closed handles the common path. TTL handles abandoned pull requests, which are more numerous than people expect. Idle timeout handles the environment created on Monday and reviewed on Friday. A weekly sweep for anything with no owning pull request handles the failures of the other three. Any single trigger leaves a class of survivors.

**Scale to zero is the largest lever for the environments that do exist.** A preview is used for minutes and exists for days. Scaling workloads to zero when idle, and waking them on the first request through the ingress, removes the majority of compute cost while keeping the URL working. The visible cost is cold-start latency on the first request, which for a preview is entirely acceptable.

**Share the expensive dependencies.** A database instance per preview is usually the largest line. A shared instance with a schema or logical database per preview, or a copy-on-write clone from a template, costs a fraction. The same applies to caches, message brokers, and search clusters - one shared instance with per-environment namespacing.

**Run them on interruptible capacity.** Previews are the ideal spot workload: interruption is an inconvenience, not an incident. Combined with scale to zero this is usually the difference between an affordable capability and one that gets cut.

**Watch the shared baseline.** With request-level routing to a shared baseline of all services, the baseline runs continuously and is easy to over-provision. It should be sized for preview traffic - which is tiny - not shaped like production, and it should scale to zero out of hours too.

**Storage and data are the costs people forget.** Snapshots, orphaned volumes from deleted environments, and container images built per pull request all accumulate. Volume reaping needs to be part of teardown, and image retention needs a policy - preview images built for a closed pull request should expire quickly.

**Attribute cost per team and per environment, and publish it.** A team seeing that its abandoned previews cost more than its production staging changes behaviour without any policy being written. Attribution is also what lets you defend the capability: "previews cost this much and saved this much contention" is a sentence you can only say with the data.

**Quota rather than policing.** A per-team limit on concurrent previews, enforced at creation, is better than a monthly conversation about spend. It also makes the cost bounded and predictable, which is what a budget owner wants.

**Do the arithmetic before defending it.** Ephemeral environments are usually cheap compared to engineering time lost to shared environment contention. Being able to state that comparison, with numbers, is how the capability survives a cost review.

## Example

```text
Where the money actually goes, and what each control removes.

  BEFORE (naive: full stack per PR, always on, on-demand instances)
    14 concurrent previews x full stack ................. dominant cost
    1 database instance per preview ..................... second largest
    all workloads running 24/7 whether used or not
    orphaned: 23 environments with no open PR ........... pure waste
    orphaned volumes from deleted previews .............. pure waste
    preview images retained indefinitely ................ growing
    shared baseline sized like production ............... over-provisioned

  AFTER, control by control:
    reap on PR close + TTL + idle + weekly sweep    -> 23 orphans -> 0
    scale to zero when idle (wake on first request) -> compute cut by ~85%;
                                                       cold start ~8s, fine here
    shared database, schema per preview             -> DB cost cut by ~90%
    spot capacity for preview node pool             -> remaining compute ~-70%
    volume reaping in teardown                      -> orphaned storage -> 0
    preview image retention: 7 days                 -> registry growth flat
    baseline sized for preview traffic + off-hours
      scale to zero                                 -> baseline cost ~-60%
    per-team concurrent preview quota: 5            -> cost bounded, predictable
```

```yaml
# The controls expressed in the environment definition, so they apply by default
# rather than being remembered per team.
apiVersion: platform.example.com/v1
kind: EnvironmentClass
metadata: { name: preview }
spec:
  lifecycle:
    ttl: 72h
    idleTimeout: 8h
    reapOn: [pull-request-closed, pull-request-merged, ttl-expired, idle]
    orphanSweep: weekly # nothing with no owning PR survives a week
  scaling:
    scaleToZero: { enabled: true, afterIdle: 20m, wakeOn: ingress-request }
  placement:
    nodePool: burst # spot; interruption is acceptable here
    tolerations: [{ key: interruptible, value: "true", effect: NoSchedule }]
  dependencies:
    postgres: { mode: shared-instance, isolation: schema } # not one instance each
    redis: { mode: shared-instance, isolation: keyspace }
  storage:
    reapVolumesOnDelete: true # otherwise volumes outlive their environments
  images:
    retention: 7d # preview builds expire quickly
  quota:
    concurrentPerTeam: 5 # bounded cost, enforced at creation
```

```text
Attribution, published monthly - the report that changes behaviour without a policy:

  $ platform previews cost --by team --month 2026-07

  TEAM             PREVIEWS  AVG LIFE  IDLE %  COST     NOTE
  team-payments          84      11h     41%   $412
  team-search            61      19h     78%   $388     <- high idle: TTL too long
                                                           for how they work
  team-data              22      63h     91%   $604     <- HIGHEST COST, LOWEST
                                                           USE. 91% idle at 63h
                                                           average life.
  team-web              103       6h     22%   $291     <- best pattern: short
                                                           lived, actually used
  ------------------------------------------------------------------------------
  total                 270              ~     $1,695

  The comparison that justifies the spend:
    engineering time previously lost to staging contention, measured before
    previews existed: ~14 engineer-hours/week across 12 teams.
    That is the number to put next to $1,695 - not zero.
```

## Interview tips

- Lead with multiple reap triggers and explain why each single trigger leaves survivors. Abandoned pull requests are more common than people expect.
- Scale to zero is the biggest lever, and the trade-off - cold start on first request - is trivially acceptable for a preview. Say both halves.
- Sharing the expensive dependency, with a schema per preview instead of an instance per preview, is the most concrete cost reduction available.
- Naming the forgotten costs - orphaned volumes, retained preview images, an over-provisioned shared baseline - is what distinguishes this from a generic answer.
- Attribution per team is the behavioural mechanism; a team seeing its own idle spend fixes it without a policy.
- Close with the comparison against engineering time lost to contention. That framing is how the capability survives a cost review, and it shows you think about value rather than only spend.

---

[⬅ Back to Environments and Ephemeral Infrastructure](./README.md) · [All topics](../README.md)
