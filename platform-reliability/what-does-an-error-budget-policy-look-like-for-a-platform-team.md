---
title: "What does an error budget policy look like for a platform team?"
id: 207
category: "Platform Reliability"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-reliability
  - interview-questions
---

# What does an error budget policy look like for a platform team?

**Short answer:** A written, pre-agreed set of consequences that trigger when a capability's error budget is being consumed too quickly or is exhausted - typically freezing non-essential change to that capability, redirecting the team to reliability work, and escalating at defined thresholds. Its purpose is to remove the negotiation from the moment when negotiating is hardest, and for a platform team it has a specific extra function: it is the strongest available argument for declining feature work.

## Detail

**What an error budget is.** The complement of the objective. A 99.9% target over 28 days permits roughly 40 minutes of failure; the budget is that allowance, and consuming it is the intended use of the reliability you did not promise. The point is that it converts reliability from an absolute into a resource you spend deliberately.

**The policy is the consequences, decided in advance.** Without written consequences, an exhausted budget produces a conversation in which the pressure is always to ship anyway. The policy's value is entirely in having agreed the response before you needed it.

**Per capability, not per team.** A platform team owns several capabilities with independent budgets. Exhausting the provisioning budget should not freeze deployment work. Tying the policy to the capability keeps the response proportionate and keeps unrelated work moving.

**Burn rate is what makes it actionable.** Consuming a month's budget over a month is normal; consuming it in an hour is an incident. Multi-window, multi-burn-rate alerting - a fast burn over a short window paging immediately, a slow burn over a longer window raising a ticket - is the standard approach and is far better than alerting on the raw error rate.

**The platform-specific consequence: this is how you decline work.** A platform team is under continuous pressure to add capabilities. An error budget policy signed off by the same leadership that requests those capabilities converts "we are too fragile to build that" from an opinion into a pre-agreed rule. That organisational function is at least as valuable as the engineering one, and it is the point most worth making in an interview.

**Freezing platform change is more complicated than freezing an application.** Your users depend on your change mechanism, so a freeze must exclude security patches, changes that improve the burning capability, and anything unblocking a consumer. Define those exclusions in the policy - an unqualified freeze on a platform is either ignored or harmful.

**Consumers need to see it.** Publishing budget status per capability lets teams understand why their request is queued, and it turns an opaque refusal into a visible, shared constraint. It also builds pressure in the right direction: teams start asking about reliability rather than only about features.

**Have an escalation ladder rather than a single cliff.** Fifty percent consumed is a signal, seventy-five percent changes prioritisation, exhausted freezes non-essential change, and repeated exhaustion triggers a decision about whether the target is wrong or the investment is insufficient. The last rung matters: a budget exhausted three quarters running is telling you something about staffing or about the promise, not about that quarter's incidents.

**Allow deliberate spending.** Budget can legitimately be spent on a migration or a risky improvement, agreed in advance and recorded. A policy that treats all consumption as failure discourages exactly the work that improves reliability over time.

## Example

```yaml
# The policy, per capability, agreed and signed off before it is needed.
apiVersion: platform.example.com/v1
kind: ErrorBudgetPolicy
metadata: { name: deploy-capability }
spec:
  capability: deploy
  slo: { objective: 95%, window: 28d } # ~34h of budget in the window
  approvedBy: [head-of-engineering, platform-lead]
  reviewedQuarterly: true

  burnRateAlerts:
    # Fast burn - pages. 14.4x consumes 2% of a 28d budget in 1h.
    - { longWindow: 1h, shortWindow: 5m, burnRate: 14.4, severity: page }
    # Slow burn - ticket. Sustained mild degradation matters too.
    - { longWindow: 6h, shortWindow: 30m, burnRate: 6, severity: ticket }
    - { longWindow: 3d, shortWindow: 6h, burnRate: 1, severity: review }

  thresholds:
    - consumed: 50%
      actions:
        - "Notify the platform team and publish status to consumers"
        - "Reliability items added to the next sprint"
    - consumed: 75%
      actions:
        - "New feature work on THIS capability paused"
        - "At least half of team capacity to reliability for this capability"
        - "Consumers notified with expected impact on their requests"
    - consumed: 100%
      actions:
        - "FREEZE non-essential change to this capability"
        - "All capability capacity to reliability until burn stops"
        - "Written summary to engineering leadership within 2 working days"

  # A platform freeze cannot be unqualified - consumers depend on the change
  # mechanism itself.
  freezeExclusions:
    - "Security patches and CVE remediation"
    - "Changes that directly reduce this capability's burn"
    - "Changes unblocking a consumer team's production incident"
    - "Rollbacks"

  deliberateSpend:
    allowed: true
    requires: "Recorded in advance with an expected budget cost and an owner"
    note: >
      A migration or a risky improvement may legitimately spend budget. Treating
      all consumption as failure discourages the work that improves reliability.

  repeatedExhaustion:
    afterConsecutiveWindows: 3
    action: >
      Escalate a decision: either the target is wrong for what consumers need, or
      the investment is insufficient. Three consecutive exhaustions is a staffing
      or a promise problem, not three bad months.
```

```text
Published status - what consumers see, and why it changes the conversation.

  $ platform slo status

  CAPABILITY         TARGET   BUDGET USED   BURN     STATE
  deploy             95%          38%       normal   ok
  provision (db)     95%          91%       elevated 75% THRESHOLD PASSED
                                                     -> feature work paused;
                                                        3 requests queued
  provision (bucket) 99%          12%       normal   ok
  preview env        95%          64%       normal   watch
  ingress          99.99%          8%       normal   ok
  telemetry          99%         103%       normal   EXHAUSTED
                                                     -> frozen. Cause: collector
                                                        OOM on 2026-08-07.
                                                        Reliability work in flight.

  The organisational effect: when a team asks why their database provisioning
  request is queued, the answer is a published number they can see, not a
  judgement call by the platform team. And when leadership asks for a new
  capability, the reply is a policy they signed rather than an opinion.
```

## Interview tips

- Define the budget quickly, then spend your time on the policy being the pre-agreed consequences. The whole value is having decided before the pressure arrived.
- Per capability rather than per team is a specific, correct point that most candidates miss - exhausting provisioning should not freeze deploy work.
- Multi-window multi-burn-rate alerting is the technically expected detail; explain why a fast burn pages and a slow burn tickets.
- The platform-specific function is the standout: an error budget policy signed by leadership is how a platform team declines feature work with authority rather than opinion.
- Freeze exclusions are essential and specific to platforms, because consumers depend on your change mechanism. An unqualified freeze is either ignored or harmful.
- Allowing deliberate budget spend for migrations shows you understand budgets as a resource rather than a punishment.
- The repeated-exhaustion rung - three consecutive windows means the target or the staffing is wrong - is a mature close.

---

[⬅ Back to Platform Reliability](./README.md) · [All topics](../README.md)
