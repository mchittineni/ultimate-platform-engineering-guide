---
title: "How do you use commitments and spot capacity on behalf of every team?"
id: 235
category: "Platform FinOps"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-finops
  - interview-questions
---

# How do you use commitments and spot capacity on behalf of every team?

**Short answer:** Buy commitments centrally against the estate's aggregate baseline usage - never per team, because no team can forecast for the whole - and expose interruptibility as a property in the platform interface so spot capacity is a declaration rather than an implementation each team assembles. This is one of the clearest cases where the platform saves money that no individual team could, because both mechanisms depend on aggregate scale.

## Detail

**Commitments work on aggregate, which is why they belong centrally.** Reserved instances and savings plans trade a usage commitment for a discount. Individual teams cannot forecast their own baseline reliably, will under-commit out of caution, and cannot see the estate's shape. The platform can see aggregate usage across every team, commit against the portion that is genuinely stable, and pass the discount through - which is both a larger discount and a lower risk than the sum of individual decisions.

**Commit to the floor, not the average.** The safe commitment level is the usage you are confident persists - typically the low point of the last several months, with headroom for a departing workload. Over-committing means paying for capacity you do not use; under-committing leaves obvious savings. Deliberately under-committing and reviewing quarterly is the right bias, because the downside of over-commitment is worse.

**Prefer flexible commitment types.** Commitments tied to a specific instance family constrain your architecture for their whole term, which is a poor trade when instance generations improve and your workload mix changes. Flexible commitments that apply across families and sizes give up a little discount for a lot of freedom, and that is usually the right choice for a platform.

**Ladder the terms.** Rather than committing everything at once for a long term, stagger commitments so a portion expires each quarter. That gives you regular opportunities to adjust to a changed estate without a cliff, and it avoids the situation where a large commitment expires at a moment when your usage happens to be atypical.

**Spot capacity needs the platform to make it a declaration.** The mechanics - interruption handling, node draining, disruption budgets, diversification across instance types and zones, on-demand fallback - are real work, and no team should implement them. Exposing `interruptible: true` in the service specification and having the platform place the workload on a spot node pool with all of that configured is the whole value. Node autoscalers now carry much of the mechanics: Karpenter 1.x handles spot interruption and rebalance notices natively and consolidates onto cheaper capacity, and managed modes such as EKS Auto Mode and GKE Autopilot run that layer for you - which leaves the platform's job as the interface, the eligibility rules, and the diversification policy.

**Which workloads are genuinely interruptible.** Batch jobs, CI runners, asynchronous consumers with durable queues, preview environments, and stateless services with enough replicas and correct disruption budgets. Not: stateful singletons, anything with a long unbreakable in-flight operation, or a service whose replica count is already at the minimum for its availability target.

**Diversification is what makes spot reliable.** A pool restricted to two instance types will experience simultaneous reclamation when that capacity tightens. Allowing many families and generations, across all zones, means a shortage in one type is not a shortage everywhere - and it is the difference between spot being an occasional inconvenience and a recurring incident.

**Watch the coverage and utilisation numbers rather than the discount rate.** Commitment coverage - the share of eligible usage covered - and commitment utilisation - the share of what you committed to that you actually consumed - are the two figures that tell you whether the strategy is working. High coverage with low utilisation means you over-committed.

**Pass the benefit through visibly.** If teams see their showback at undiscounted rates while the platform absorbs the savings, the platform's economic contribution is invisible and teams cannot make correct decisions. Showing the discounted rate, and the saving attributable to the platform's commitments, is both honest and good politics.

## Example

```text
Why commitments belong centrally - the same estate, two approaches.

  PER TEAM (what happens without a platform)
    each team forecasts its own baseline, cautiously
    team A commits to 60% of its floor, team B to 40%, team C not at all
    aggregate coverage: ~35% of eligible usage
    nobody can see the estate's shape, so nobody commits confidently

  CENTRALLY (platform, against aggregate)
    aggregate baseline across all teams is far more stable than any single team's -
    one team's decline offsets another's growth
    commit against the observed FLOOR of the last 6 months, with headroom
    aggregate coverage: ~80% of eligible usage, at a better discount tier
    -> the platform captured savings no team could have captured alone. This is
       the clearest single example of the platform earning its place economically.
```

```text
The commitment ladder - staggered so nothing expires as a cliff.

  QUARTER      NEW COMMITMENT      TERM     EXPIRES     COVERS
  2025-Q3      baseline slice A    1 year   2026-Q3     ~20% of eligible
  2025-Q4      baseline slice B    1 year   2026-Q4     ~20%
  2026-Q1      baseline slice C    3 year   2029-Q1     ~20% (the most stable
                                                              portion only)
  2026-Q2      baseline slice D    1 year   2027-Q2     ~20%
  ------------------------------------------------------------------
  coverage ~80%, and a slice comes up for review every quarter.

  Rules applied:
    - commit to the FLOOR of observed usage, not the average
    - flexible commitment types, not instance-family-specific: the small extra
      discount is not worth constraining the architecture for a whole term
    - only the demonstrably stable portion gets a 3-year term
    - deliberately leave ~20% uncommitted: the downside of over-committing is
      worse than the foregone discount

  THE NUMBERS TO WATCH  (not the headline discount rate)
    commitment coverage ..... 80%   share of eligible usage covered
    commitment utilisation .. 97%   share of what we committed to that we used
    -> high coverage with LOW utilisation would mean we over-committed.
       Both numbers together are the health check.
```

```yaml
# Spot as a DECLARATION, not an implementation. The team writes one field.
apiVersion: platform.example.com/v1
kind: Service
metadata: { name: reindex-worker }
spec:
  owner: group:team-search
  tier: 3
  runtime:
    size: large
    interruptible: true # <- the whole team-facing surface
```

```text
What the platform configures from that one field - none of it the team's concern:

  PLACEMENT
    spot node pool, tainted interruptible=true:NoSchedule
    tolerations + node affinity generated
    DIVERSIFIED across 6 instance families x 3 generations x 3 zones
      -> a shortage in one type is not a shortage everywhere. This is what makes
         spot an inconvenience rather than a recurring incident.
    on-demand fallback if spot capacity is genuinely unavailable

  INTERRUPTION HANDLING
    interruption notice handled by the node autoscaler (Karpenter) - node
      cordoned and drained, replacement launched before reclamation
    PodDisruptionBudget generated from tier
    terminationGracePeriodSeconds 120 so in-flight work finishes
    PriorityClass tier-3-batch, preemptionPolicy: Never

  ELIGIBILITY CHECK - the platform REFUSES the declaration where it is unsafe
    ✗ stateful singletons
    ✗ replicas == minimum required for the availability target
    ✗ workloads with unbreakable long-running in-flight operations
    -> `interruptible: true` on a tier-1 single-replica service is rejected at
       admission with an explanation, not silently accepted.

  Showback shows the DISCOUNTED rate, plus the saving attributable to platform
  commitments and spot placement - so teams can make correct decisions and the
  platform's contribution is visible rather than absorbed invisibly.
```

## Interview tips

- The central claim: both mechanisms depend on aggregate scale, so this is a saving no individual team can achieve. That makes it the clearest economic argument for a platform team.
- Aggregate baseline being more stable than any single team's, because declines and growth offset, is the reasoning that makes central commitment obviously correct.
- "Commit to the floor, not the average", flexible commitment types over family-specific ones, and a laddered term structure are three specific, defensible practices.
- Coverage and utilisation together as the health check, rather than the headline discount rate, is the detail that shows you have managed commitments rather than bought them once.
- For spot, the value is turning it into a declaration. Listing what the platform configures - diversification especially - demonstrates why no team should implement this.
- Diversification being what separates spot-as-inconvenience from spot-as-incident is the technical insight worth stating.
- The platform refusing an unsafe `interruptible: true` declaration is a good sign of a designed interface rather than a passthrough flag.
- Passing the discount through visibly is both honest and politically sensible, and it lets teams make correct decisions.

---

[⬅ Back to Platform FinOps](./README.md) · [All topics](../README.md)
