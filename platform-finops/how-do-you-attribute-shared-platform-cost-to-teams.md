---
title: "How do you attribute shared platform cost to teams?"
id: 233
category: "Platform FinOps"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-finops
  - interview-questions
---

# How do you attribute shared platform cost to teams?

**Short answer:** Pick an allocation rule per shared cost, publish it, and stick to it - proportional to a usage metric where one exists, even where none does, and absorbed by the platform where the platform's own decisions drive the cost. What matters more than precision is that the rule is understood, reproducible, and stable, because teams reject numbers they cannot reproduce and argue endlessly about numbers that change month to month.

## Detail

**Identify what is genuinely shared.** Control planes, the observability pipeline, shared cluster capacity including idle headroom, transit gateways and central egress, shared registries and artefact storage, and the platform team's own tooling. This is typically a modest share of total spend and generates a disproportionate amount of argument, which is why having a rule matters more than optimising the rule.

**The three allocation methods, and when each is right:**

| Method                | Use when                                     | Weakness                               |
| --------------------- | -------------------------------------------- | -------------------------------------- |
| Proportional to usage | A defensible usage metric exists             | Metric choice can be gamed or disputed |
| Even split            | No usage metric, or usage is roughly uniform | Crude; penalises small teams           |
| Absorbed by platform  | The platform's own decisions drive the cost  | Teams see no signal about their impact |

**Absorbing cost is underrated, and often correct.** Idle cluster headroom exists because the platform chose a capacity buffer; the observability pipeline's fixed cost exists because the platform chose that architecture. Charging teams for decisions they did not make produces disputes and no behaviour change, whereas the platform absorbing it creates the right incentive - the platform is now motivated to right-size the buffer. The test is whose decision drives the cost.

**Choose the proportional metric carefully, because it becomes an incentive.** Allocating the observability pipeline by bytes ingested encourages teams to reduce telemetry volume, which is probably what you want. Allocating shared cluster cost by resource requests encourages accurate requests, which is also good. Allocating by request count would encourage nothing useful. Pick the metric whose optimisation you actually want.

**Stability beats precision.** A rule that changes every month makes trends unreadable and every conversation a re-litigation. Set the rule, publish it, and review it at a fixed cadence - annually or when the estate changes materially - rather than adjusting it whenever someone complains.

**Publish the unallocated percentage.** Some cost genuinely resists attribution - inter-zone data transfer, load balancer capacity charges, support fees. Name them, choose a treatment, and publish the residual. If a third of spend is unattributed, no team's number means anything, so this figure is the credibility metric for the whole exercise.

**Show the workings.** A team should be able to see not just its number but how it was derived: this much directly attributed, this much from its share of the cluster, this much from the split rule, with the inputs visible. Numbers a team can reproduce get accepted; numbers they cannot get disputed regardless of accuracy. Build the pipeline on FOCUS-format billing exports where providers offer them - FOCUS 1.3 added allocation columns so a provider can state how it split a shared resource's cost - and on pod-level data for shared clusters, covered in [Why is Kubernetes cost allocation hard?](./why-is-kubernetes-cost-allocation-hard.md).

**Get agreement before you publish, once.** The allocation rule for shared cost is a political artefact as much as a technical one. Agreeing it with engineering leadership and the finance partner up front, and being able to point at that agreement, removes the monthly negotiation. Deriving it unilaterally guarantees the negotiation happens every month instead.

**Watch the second-order effect.** If a team is charged for shared cluster usage, it may move to its own cluster to escape the shared allocation - which is worse for everyone. Allocation rules that make the paved road more expensive than leaving it are actively harmful, and worth checking for.

## Example

```text
The allocation model, agreed once and published.

  SHARED COST                    METHOD          RULE / RATIONALE
  management cluster + control    ABSORBED        the platform chose this
    plane                                         architecture; teams have no
                                                  lever. Absorbing it motivates
                                                  US to keep it lean.
  shared cluster idle headroom    ABSORBED        the platform chose the buffer
                                                  size. Charging teams for our
                                                  capacity decision produces
                                                  argument and no behaviour change.
  shared cluster node cost        PROPORTIONAL    by resource REQUESTS. Chosen
                                                  because it incentivises accurate
                                                  requests, which is what we want.
  observability pipeline          PROPORTIONAL    by bytes ingested. Incentivises
                                                  reducing telemetry volume - the
                                                  behaviour we want.
  transit gateway + central       PROPORTIONAL    by data processed per account
    egress
  shared registry + artefacts     EVEN            no meaningful usage metric;
                                                  storage is small relative to
                                                  the argument it would cause
  platform team tooling           ABSORBED        the platform's own cost of doing
                                                  business
  inter-zone data transfer        UNALLOCATED     cannot be traced to a workload
                                                  from billing data. Named and
                                                  published.

  Agreed with: head of engineering, finance partner. Reviewed annually.
  This agreement is what removes the monthly negotiation.
```

```text
Showing the workings - a number a team can reproduce is a number they accept.

  $ platform cost explain --team team-payments --month 2026-07

  DIRECT (attributed by account and tag)                          $41,200
    checkout-prod account                              $28,400
    checkout-staging account                            $6,100
    tagged resources in shared accounts                 $6,700

  SHARED CLUSTER (proportional to resource requests)               $8,400
    your requests: 38.2 CPU-equivalent of 100 allocatable  = 38.2%
    allocatable node cost this month: $22,000
    38.2% x $22,000                                    $8,404
    idle headroom (9.8% unrequested): ABSORBED by platform, not charged

  OBSERVABILITY (proportional to bytes ingested)                   $6,700
    your ingest: 4.1 TB of 17.4 TB total = 23.6%
    pipeline + storage cost: $28,500
    23.6% x $28,500                                    $6,726
    -> 45% of your total spend. See the cardinality report.

  NETWORK SPLIT (proportional to data processed)                   $1,180

  EVEN SPLIT (registry, artefacts; 1/12 of $3,400)                   $283
  ------------------------------------------------------------------------
  TOTAL                                                           $57,763

  Every line shows its inputs and its arithmetic. A team can check it.
```

```text
The second-order effect to watch for - and the check that catches it:

  team-search asked for a dedicated cluster. Stated reason: isolation.
  Actual reason, on inspection: their shared-cluster allocation was $5,300/month
  and a small dedicated cluster looked cheaper on their line - because the
  dedicated cluster's idle capacity would be theirs alone and appear as "their"
  cost rather than as a share of a bigger pool they could not control.

  Outcome: the dedicated cluster would cost the ORGANISATION more (a full extra
  control plane and nine duplicated components) while costing the TEAM less.
  The allocation rule had made leaving the paved road rational.

  Fix: absorb idle headroom centrally (already the rule, but it was being applied
  inconsistently), and check annually whether any allocation makes the paved road
  more expensive than the alternative. An allocation rule that pushes teams off
  the platform is actively harmful, however fair it looks.
```

## Interview tips

- Lead with the principle that a published, reproducible, stable rule matters more than a precise one. Teams reject numbers they cannot reproduce.
- The three methods with the whose-decision-drives-the-cost test is the framework, and arguing for absorbing platform-chosen costs like idle headroom is the most defensible position.
- Choosing the proportional metric as an incentive - bytes ingested to discourage telemetry volume, resource requests to encourage accurate requests - is the sophisticated point.
- Publishing the unallocated percentage as the credibility metric shows you know the exercise fails if the numbers are not trusted.
- Showing the workings, with inputs and arithmetic visible, is the practical thing that gets allocation accepted.
- Agreeing the rule with engineering leadership and finance up front is what removes the monthly negotiation - a political insight that experienced candidates volunteer.
- The second-order effect is the strongest close: an allocation rule that makes leaving the platform cheaper for a team while costing the organisation more is actively harmful, and worth checking for annually.

---

[⬅ Back to Platform FinOps](./README.md) · [All topics](../README.md)
