---
title: "How do you design a progressive rollout and its abort criteria?"
id: 102
category: "Progressive Delivery and Feature Flags"
difficulty: "Advanced"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# How do you design a progressive rollout and its abort criteria?

**Short answer:** Choose the ramp curve from the risk of the change, and write down the abort threshold, the verification step, and the hold time for every phase _before_ the rollout starts. Then wire the abort to automation rather than to a human watching a dashboard. A rollout plan without pre-committed abort criteria is not a plan - during an incident the pressure is always to explain away a bad signal and continue.

## Detail

**Match the curve to the risk, not to preference:**

| Strategy      | Ramp                          | Use for                                           | Hold per step |
| ------------- | ----------------------------- | ------------------------------------------------- | ------------- |
| Ring / canary | 1 → 5 → 25 → 50 → 100%        | Payments, auth, data integrity, latency-sensitive | 24-72h        |
| Linear        | Even daily increments         | Standard launches                                 | Daily check   |
| Front-loaded  | Fast early, slow at the end   | Low-risk copy and UI changes                      | Start and end |
| Cohort        | Internal → beta → free → paid | Risk or value differs by audience                 | Per cohort    |
| Account-based | Whole accounts at a time      | **B2B** - see below                               | Per account   |

**For business-to-business products, ramp by account, not by user.** A random 10% of users inside one enterprise customer means some of their staff see one behaviour and some another, which that customer experiences as a bug rather than a rollout. This is a frequent and avoidable mistake.

**Abort criteria must be numeric and pre-committed.** Concrete thresholds, expressed against a concurrent baseline rather than yesterday's numbers:

| Signal        | Example threshold             | Severity    |
| ------------- | ----------------------------- | ----------- |
| 5xx rate      | baseline + 1 percentage point | Abort       |
| 4xx rate      | baseline + 5 points           | Investigate |
| p99 latency   | baseline × 1.2                | Investigate |
| p99.9 latency | baseline × 1.5                | Abort       |
| Conversion    | below baseline × 0.95         | Investigate |
| Datastore CPU | above 80%                     | Abort       |

Compare against a concurrent control, not a historical baseline: an unrelated traffic pattern or a neighbouring deployment will otherwise be attributed to your change.

**Automate the abort.** A webhook that sets the flag to 0% or halts the rollout when a threshold is breached responds in seconds; a human reading a dashboard responds in minutes and only while awake. The automated path also removes the judgement call under pressure, which is exactly when judgement is worst.

**Hold times need calendar awareness.** Off-hours time does not count as bake-in, because the traffic mix that would reveal the problem is not present - a phase starting at 18:00 on Friday holds until Monday morning. Weekend ramps need explicit on-call cover, and going to 100% on a Friday afternoon is a decision to discover problems with nobody around.

**Each phase needs a verification step, not just a threshold.** "No alerts fired" is weak. "The pricing-mismatch reconciliation job found zero discrepancies for the canary cohort" is a verification. Thresholds catch degradation; verification catches silent incorrectness, which is the failure mode thresholds miss entirely.

**Do not advance on schedule when a metric is soft.** The next ring typically exposes several times more users, so advancing on an ambiguous signal multiplies the problem. Hold, investigate, then decide.

**The platform's contribution.** Teams should not design this from scratch each time. The platform should provide the rollout mechanism, the default curves per tier, the baseline comparison, the automated abort wiring, and a generated phase plan - so the team's decision is which curve and which extra verification, not how to build progressive delivery.

## Example

```text
Generated phase plan for a tier-1 pricing change. Every row has a threshold, a
verification, and a hold - all agreed BEFORE phase 1 starts.

  PHASE  %     USERS     COHORT          ABORT IF                    VERIFY
  1      1     ~2,400    internal +      5xx > base+1pp              pricing recon:
                         opted-in beta   p99 > base x1.2             0 discrepancies
         hold 24h (business hours only)
  2      5     ~12,000   random          as above, + conversion      recon + manual
                                         < base x0.95                spot-check 20 orders
         hold 48h
  3      25    ~60,000   random          as above, + db CPU > 80%    recon + support
                                                                     ticket rate flat
         hold 72h  (crosses a weekend -> on-call cover confirmed)
  4      50    ~120,000  random          as above                    recon
         hold 48h
  5      100   all       -               kill switch remains armed    recon for 7d
                                         for 30 days

  Scheduling rules applied automatically:
    - phase 5 not scheduled for a Friday
    - phase 3 hold extended to cover the weekend
    - off-hours time excluded from hold accounting
```

```yaml
# Automated abort, wired to the same SLO burn-rate rules the service already has.
# The response is a webhook in seconds, not a human noticing in minutes.
apiVersion: platform.example.com/v1
kind: Rollout
metadata: { name: checkout-new-pricing-engine, namespace: team-payments }
spec:
  flag: checkout-new-pricing-engine
  strategy: ring
  steps: [1, 5, 25, 50, 100]
  holdHours: [24, 48, 72, 48]
  schedule:
    businessHoursOnly: true # off-hours does not count as bake-in
    excludeDays: [Friday] # for the final step
  baseline:
    type: concurrent # compare against the control cohort, NOT yesterday
    cohort: control
  abortOn:
    - { metric: http_5xx_rate, comparison: absolute, threshold: 0.01, action: abort }
    - { metric: latency_p999, comparison: ratio, threshold: 1.5, action: abort }
    - { metric: latency_p99, comparison: ratio, threshold: 1.2, action: hold }
    - { metric: conversion_rate, comparison: ratio, threshold: 0.95, action: hold }
    - { metric: db_cpu_utilisation, comparison: absolute, threshold: 0.8, action: abort }
  verify:
    - name: pricing-reconciliation # catches silent incorrectness, which no
      job: pricing-recon-canary #    threshold above would detect
      requires: "discrepancies == 0"
  onAbort:
    setPercentage: 0
    notify: [pagerduty:team-payments, "#platform-alerts"]
```

## Interview tips

- The thesis: thresholds, verification, and hold times are written down before phase 1, because during a rollout the pressure is always to explain away a bad signal.
- Match the curve to risk and name the B2B case - ramp by account, not by user, because a partial rollout inside one customer reads as a bug.
- Concurrent baseline rather than historical is a precise, high-signal detail; it is how you avoid attributing an unrelated traffic change to your rollout.
- Automated abort via webhook, and the reason: seconds instead of minutes, and no judgement call under pressure.
- Hold-time calendar awareness - off-hours does not count, no 100% on a Friday - is the operational detail that reads as experience rather than theory.
- The verification step catching silent incorrectness is the strongest single idea here. Thresholds detect degradation; only verification detects wrong answers returned successfully.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
