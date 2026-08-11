---
title: "What is the difference between showback and chargeback, and which works?"
id: 119
category: "Platform FinOps"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-finops
  - interview-questions
---

# What is the difference between showback and chargeback, and which works?

**Short answer:** Showback reports what a team spends without moving money; chargeback actually bills it to their budget. Showback changes behaviour at a fraction of the cost and complexity, and for most organisations it is the right answer. Chargeback becomes worth its overhead when teams have genuine budget authority and when cost genuinely needs to influence their prioritisation - and it only works if the numbers are already trusted, which means showback is a prerequisite either way.

## Detail

**The distinction is whether money moves.** Showback is visibility: here is your spend, its trend, and its composition. Chargeback is accounting: this amount is deducted from your budget, and you will be asked about it. Both require the same attribution work, which is why showback is never wasted effort even if you later move to chargeback.

**Showback works better than people expect.** Engineers are generally not indifferent to cost; they are unaware of it. A monthly report showing a team that its observability spend exceeds its compute spend, or that its idle preview environments cost more than its staging environment, produces action without any budget mechanism. Most of the behavioural benefit of cost accountability comes from visibility alone.

**Chargeback's overhead is real and often underestimated.** Once money moves, the numbers become a finance artefact: the allocation rule must survive audit, disputes need a resolution process, mid-year budget adjustments become necessary, and every shared-cost split becomes a negotiation with financial consequences. That machinery has an ongoing cost in platform and finance time, and it needs to be justified by a behavioural change that showback could not achieve.

**Chargeback's failure modes are worth naming:**

- **Optimising the bill rather than the outcome.** A team under budget pressure may cut monitoring, reduce replica counts, or skip a preview environment - saving money and creating risk.
- **Escaping the allocation rather than reducing usage.** If shared platform allocation is charged, a team may move to its own cluster to make its number smaller while making the organisation's number larger.
- **Disputes replacing engineering.** Time spent arguing about the split is time not spent reducing spend.
- **Gaming the metric.** Whatever the proportional metric is, it will be optimised - which is fine if you chose it well and harmful if you did not.

**Chargeback is genuinely right in some contexts:** when teams have real budgets they control, when a product's margin depends on its infrastructure cost, when internal customers should be able to choose between the platform and an alternative, and in organisations where cross-charging is already the norm.

**The middle ground is usually the answer.** Showback for everyone, plus budgets with alerts and quotas that bound the worst case, plus chargeback only where there is a genuine business reason - a product line with its own profit and loss, for instance. That gets most of the accountability without the accounting machinery.

**Either way, trust in the numbers is the prerequisite.** If a large share of spend is unallocated or the split rule is disputed, chargeback amplifies the argument rather than the accountability. Get attribution credible under showback first; the decision about chargeback can wait.

**Measure whether it worked, not whether it ran.** The point is behaviour change, so the evidence is spend per unit of value improving, waste declining, and teams acting on findings - not a report existing.

## Example

```text
The same information, two mechanisms, very different overhead.

  SHOWBACK
    monthly report to each team: spend, trend, composition, findings
    no money moves; no finance process; no dispute mechanism needed
    platform cost to run: a report and an allocation rule
    typical effect: teams act on the findings they can act on

  CHARGEBACK
    the same numbers, deducted from the team's budget
    requires: audit-grade allocation, a dispute process, mid-year budget
              adjustment, finance partner involvement, negotiated split rules
    platform cost to run: the above, ongoing, plus your time in the disputes
    typical effect: stronger prioritisation pressure, plus the failure modes below
```

```text
What showback alone achieved in one quarter - no budgets, no chargeback:

  team-search, on seeing its report
    finding: logs were 82% of its observability spend
    action:  set log level to info in production          -> large reduction
    motivation: not a budget. Just seeing the number.

  team-web
    finding: 1.84M metric series, dashboards timing out
    action:  normalised route labels in instrumentation   -> large reduction,
             and the dashboards got faster
    motivation: the performance problem and the cost had the same cause

  team-data
    finding: preview environments 91% idle at 63h average life
    action:  reduced TTL, adopted scale-to-zero            -> meaningful reduction

  Three teams, three actions, no money moved and no budget conversation. This is
  why showback is usually sufficient: the teams were not indifferent, they were
  uninformed.
```

```text
The chargeback failure modes, with a real shape for each:

  OPTIMISING THE BILL, NOT THE OUTCOME
    a team under budget pressure reduced tier-1 replicas from 6 to 3 and shortened
    log retention to 3 days. Saved a modest amount. Two months later an incident
    took longer to diagnose because the logs were gone, and a node failure caused
    a brief outage because there was no spare capacity.
    -> the saving was real and the trade was bad. Nobody reviewed it because the
       budget mechanism only measured cost.

  ESCAPING THE ALLOCATION
    a team asked for a dedicated cluster because its shared-cluster charge looked
    larger than a small dedicated cluster would. Organisationally more expensive;
    on their line, cheaper.
    -> allocation rules that make the paved road expensive push teams off it.

  DISPUTES REPLACING ENGINEERING
    two months of monthly meetings about whether the observability split should be
    by bytes or by series count. Engineering time spent: more than the disputed
    amount.

  Guardrails that prevent the first one:
    - tier-1 minimum replica counts and retention are platform-enforced floors,
      not team-adjustable levers
    - any reduction below a floor requires a recorded exception with a review
    - the report shows cost AND reliability together, so a trade is visible
```

## Interview tips

- Define the distinction crisply - visibility versus money moving - and note that both require the same attribution work, so showback is never wasted.
- "Teams are not indifferent to cost, they are unaware of it" is the sentence that justifies showback, and the quarter-of-findings example makes it concrete.
- Name chargeback's overhead specifically: audit-grade allocation, dispute processes, budget adjustments, finance involvement. Candidates who present chargeback as simply stricter showback have not implemented it.
- The failure modes are what interviewers want. Optimising the bill rather than the outcome - cutting monitoring and replicas - is the most important one, and naming platform-enforced floors as the guardrail shows you thought past the problem.
- The escaping-the-allocation failure connects cost design to platform adoption, which is a strong cross-topic link.
- Recommend the middle ground - showback everywhere, budgets and quotas as guardrails, chargeback only where there is a genuine business reason - and say trust in the numbers is a prerequisite either way.
- Close on measuring behaviour change rather than report existence.

---

[⬅ Back to Platform FinOps](./README.md) · [All topics](../README.md)
