---
title: "How do you build unit economics for a platform?"
id: 120
category: "Platform FinOps"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-finops
  - interview-questions
---

# How do you build unit economics for a platform?

**Short answer:** Divide cost by a unit of business value - cost per order, per active user, per API call, per tenant - so that spend can be judged against growth instead of in absolute terms. A rising bill with a falling cost per unit is a business doing well; a flat bill with a rising cost per unit is a problem. For a platform team the additional and more interesting metric is cost per service and cost per deployment, because those are the numbers the platform's own efficiency moves.

## Detail

**Why absolute cost is the wrong number to manage.** A monthly bill that grew 20% tells you nothing on its own. If traffic grew 40%, efficiency improved. If traffic was flat, something regressed. Absolute cost cannot distinguish these, which is why cost conversations based on the total are frustrating and why unit economics is the reframe that makes them productive.

**Choose the unit from the business, not from the infrastructure.** Cost per order, per active user, per transaction, per tenant, per gigabyte processed - whatever the organisation already uses to describe its growth. A unit nobody outside engineering recognises will not be used in the conversations that matter. Cost per CPU hour is an infrastructure metric, not a unit economic.

**Layer the platform's own units on top.** These are the ones a platform team can actually move:

| Metric                                      | What it reveals                                        |
| ------------------------------------------- | ------------------------------------------------------ |
| Cost per service                            | Whether the platform's per-service overhead is growing |
| Cost per deployment                         | Whether the delivery path is getting cheaper           |
| Cost per environment                        | Whether ephemeral environments are affordable          |
| Platform overhead as a share of total spend | Whether the platform is proportionate                  |
| Observability cost per service              | Usually the fastest-growing line                       |

Cost per service is the most useful because it isolates the fixed and semi-fixed platform cost from workload growth. If cost per service is falling as service count rises, the platform is amortising well.

**Separate fixed, semi-variable, and variable cost.** Control planes and the platform team are largely fixed; shared cluster capacity and observability infrastructure are semi-variable; workload compute and data transfer are variable. That decomposition is what lets you forecast, and it explains the shape people find surprising - platform overhead per service should fall as adoption grows, which is the economic argument for the platform.

**Attach cost to the unit through the attribution you already have.** Cost per order requires knowing which spend serves the ordering path, which needs the service-level attribution and dependency graph the platform already maintains. This is a good argument for the attribution work: it is what makes unit economics possible at all.

**Track the trend, and set expectations rather than targets.** "Cost per order should decline as volume grows" is a useful expectation. A hard target invites gaming - deferring necessary spend, cutting reliability - and the metric is most valuable as a trend that prompts investigation when it moves the wrong way.

**Investigate the direction, not the level.** A rising cost per unit has a small number of causes: a new inefficiency, a change in traffic mix toward more expensive operations, growth in a fixed cost that is not amortising, or a step change from a migration. Each has a different response, and identifying which one it is matters more than the absolute figure.

**Use it to justify platform investment.** The strongest version of this is showing that platform overhead per service has fallen as adoption rose - which converts the platform from a cost centre into something with demonstrable leverage. That is a much better funding argument than describing capabilities.

## Example

```text
Absolute cost versus unit economics - the same twelve months, two conclusions.

  MONTH        TOTAL SPEND   ORDERS      COST/ORDER   SERVICES   COST/SERVICE
  2025-08       $142,000     1.90M        $0.0747        118       $1,203
  2025-11       $168,000     2.60M        $0.0646        149       $1,128
  2026-02       $191,000     3.40M        $0.0562        178       $1,073
  2026-05       $214,000     4.10M        $0.0522        201       $1,065
  2026-07       $238,000     4.20M        $0.0567        218       $1,092   <-- both
                                                                              turned

  ABSOLUTE READING       "spend up 68% in a year" - alarming, and useless
  UNIT READING           cost per order fell 30% while volume more than doubled;
                         the platform amortised well. Then in July BOTH unit
                         metrics reversed while volume was flat.
                         -> that reversal is the signal, and it is invisible in
                            the absolute number, which just kept rising.

  July investigation - three candidate causes, one confirmed:
    new inefficiency?          YES. Observability spend +$34k: one team's
                               cardinality change (1.84M series) plus debug
                               logging left on in another.
    traffic mix shift?         no material change
    fixed cost not amortising? no; service count still rising
  -> two one-line fixes, both surfaced by the unit metric turning.
```

```text
Cost decomposition - what makes forecasting possible and what explains the shape.

  FIXED (does not move with workload)                        $34,000/mo
    management clusters + control planes         $11,000
    platform team's own tooling and environments  $4,000
    observability pipeline baseline              $12,000
    shared registry, artefacts, CI baseline       $7,000

  SEMI-VARIABLE (steps with adoption, not with traffic)      $62,000/mo
    shared cluster capacity + idle headroom      $41,000
    observability storage growth                 $21,000

  VARIABLE (moves with traffic)                             $142,000/mo
    workload compute                             $96,000
    data transfer                                $18,000
    managed datastores                           $28,000

  Platform overhead (fixed + the shared portion of semi-variable):
    as a share of total spend .................. 21%   (was 34% a year ago)
    per service ................................ $232  (was $389 a year ago)

  That last pair of numbers IS the platform's economic argument. Overhead per
  service fell 40% as adoption grew - amortisation working as intended. It is a
  far better funding case than a list of capabilities shipped.
```

```yaml
# Unit definitions as a platform artefact, so everyone computes them the same way.
apiVersion: platform.example.com/v1
kind: UnitEconomic
metadata: { name: cost-per-order }
spec:
  unit:
    name: order
    source: warehouse
    query: "SELECT count(*) FROM orders WHERE created_at BETWEEN :from AND :to"
  cost:
    # Uses the service-level attribution and dependency graph the platform
    # already maintains - which is what makes this computable at all.
    include:
      - services: [checkout, pricing, payments, orders-worker, fulfilment]
        withDependencies: true # datastores, queues, and their share of shared cost
      - sharedAllocation: proportional
  expectation:
    direction: decreasing # an EXPECTATION, deliberately not a hard target -
    # a target invites deferring necessary spend
    investigateIfIncreasesBy: 5%
  publish: monthly
```

## Interview tips

- Lead with why absolute cost is unmanageable: a 20% increase is good news or bad news depending on growth, and the total cannot tell you which.
- Choose the unit from the business vocabulary. Cost per CPU hour is an infrastructure metric; cost per order is a unit economic that non-engineers will use.
- Cost per service is the platform-specific metric to name, because it isolates platform overhead from workload growth and is the number the platform's own efficiency moves.
- The fixed / semi-variable / variable decomposition is what enables forecasting and explains why overhead per service should fall as adoption rises.
- Frame the metric as an expectation with an investigation trigger rather than a hard target, and explain that a target invites deferring necessary spend.
- Investigating direction rather than level, with the small set of candidate causes, shows you have used this operationally.
- The closing argument is the strongest: platform overhead per service falling as adoption grows is a demonstrable leverage claim and a much better funding case than a capability list.

---

[⬅ Back to Platform FinOps](./README.md) · [All topics](../README.md)
