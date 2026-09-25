---
title: "What is an error budget?"
id: 199
category: "Platform Reliability"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-reliability
  - interview-questions
---

# What is an error budget?

**Short answer:** An error budget is the amount of unreliability an SLO allows: one minus the target, over the SLO's window. A 99.9% SLO over 30 days permits 0.1% bad events, which is about 43 minutes of full outage or one failed request in every thousand. The budget turns reliability from an argument into a shared resource - while there is budget left, teams ship; when it runs out, they spend their time on reliability instead.

## Detail

**The arithmetic is simple and worth knowing by heart.** The budget is `(1 - SLO) x window`. For time-based thinking over 30 days: 99% allows about 7.2 hours, 99.9% about 43 minutes, 99.95% about 22 minutes, and 99.99% about 4.3 minutes. For request-based SLOs it is a count: a service handling 10 million requests a month at 99.9% may fail 10,000 of them. Request-based budgets are usually more accurate, because an outage at 3am with no traffic costs users far less than one at peak.

**It exists to resolve a real conflict.** Product teams want to ship quickly; the people on call want stability. Without a shared measure, the argument is decided by whoever is more senior or more tired. The error budget gives both sides the same number: reliability above the target is spare capacity that can be spent on change, and the risk of a release is paid out of it.

**Spending budget is intended, not a failure.** A team that finishes every window with 100% of its budget left is almost certainly over-investing in caution - shipping too slowly, or holding a target stricter than users need. Deliberately spending budget on a risky migration or a chaos experiment is a legitimate use of it.

**Burn rate tells you how fast you are spending.** A burn rate of 1 means you will use exactly the whole budget by the end of the window. A burn rate of 14.4 sustained for one hour uses 2% of a 30-day budget - and if it continued, the entire budget would be gone in about two days. Alerting on burn rate rather than on raw error rate is the standard practice: a fast burn over a short window pages someone immediately, while a slow burn over a longer window raises a ticket. This catches serious problems quickly without paging for every brief blip.

**The budget only works with a policy.** The number on its own changes nothing. The team and its leadership agree in advance what happens as the budget is consumed - for example, at 75% consumed new feature work slows, and at 100% non-essential releases stop until the service is back within its objective. Agreeing this before it is needed is the whole point, because negotiating during an outage always ends with "ship it anyway". The [error budget policy question](./what-does-an-error-budget-policy-look-like-for-a-platform-team.md) covers what that document looks like for a platform team.

**For a platform, the users are other engineers.** A platform team might keep separate budgets for "deploys reach production within 15 minutes" and "databases are provisioned within 10 minutes". When the provisioning budget is exhausted, the platform team pauses new provisioning features and fixes reliability, and the teams waiting on a new feature can see exactly why. It is one of the few tools that lets a platform team say no to feature requests with evidence rather than opinion.

**Trade-offs and limits.** An error budget is only as good as the SLI behind it: if the SLI misses the failures users actually feel, the budget will say everything is fine while they complain. Budgets also need enough traffic to be meaningful - a service with a hundred requests a day can blow a 99.9% budget with a single error. And freezes need exceptions for security fixes and rollbacks, or they are either ignored or harmful.

## Example

```text
One 30-day window for a service with a 99.9% request-based SLO.

  Valid requests this window (projected) ...... 12,000,000
  Error budget (0.1%) .......................... 12,000 failed requests

  Day  3   bad deploy, rolled back in 9 min ..... 3,100 failed   (26% of budget)
  Day 11   dependency timeout, 20 min .......... 2,900 failed   (24%)
  Day 12   background errors so far ............ 1,400 failed   (12%)
  -----------------------------------------------------------------------
  Consumed by day 12 ........................... 7,400 / 12,000 (62%)
  Burn rate over the window so far ............. 1.54x
    -> at this pace the budget runs out around day 19

  Policy says: past 50% consumed, reliability items go into the next sprint.
  The team adds a canary stage and a timeout to the dependency call, rather
  than debating whether "a few incidents" is acceptable.
```

```yaml
# Multi-window burn-rate alerts for a 99.9% SLO (0.1% error budget).
# Assumes recording rules for the error ratio over each window.
groups:
  - name: checkout-error-budget
    rules:
      - alert: CheckoutErrorBudgetFastBurn
        expr: |
          checkout:error_ratio:rate1h > (14.4 * 0.001)
          and checkout:error_ratio:rate5m > (14.4 * 0.001)
        labels: { severity: page }
        annotations:
          summary: "Checkout is burning error budget 14.4x - 2% of the monthly budget per hour"
      - alert: CheckoutErrorBudgetSlowBurn
        expr: |
          checkout:error_ratio:rate6h > (6 * 0.001)
          and checkout:error_ratio:rate30m > (6 * 0.001)
        labels: { severity: ticket }
```

## Interview tips

- Give the definition as arithmetic - one minus the SLO, over the window - and quote one worked number, such as 99.9% over 30 days being about 43 minutes. It proves you have used it.
- Explain the conflict it resolves between shipping and stability. That is the reason error budgets exist, and it is what distinguishes a good answer from a definition.
- Say that spending budget is intended. Candidates who treat any consumption as failure have missed the idea.
- Mention burn rate and multi-window alerting; it is the practical follow-up almost every interviewer asks.
- Stress that the budget needs a pre-agreed policy, or it is just a dashboard.
- Name the user: for a platform team, budgets attach to capabilities other engineers depend on, and they give the team evidence for declining work.

---

[⬅ Back to Platform Reliability](./README.md) · [All topics](../README.md)
