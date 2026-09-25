---
title: "How do you run a production readiness review?"
id: 205
category: "Platform Reliability"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-reliability
  - interview-questions
---

# How do you run a production readiness review?

**Short answer:** A production readiness review (PRR) checks, before a service takes real traffic or before an operations team takes on its pager, that it can be run safely: it has SLOs and alerts that fire on them, runbooks, an owner on call, tested rollback and backups, known dependencies and failure modes, and capacity for expected load. Done well it is tiered by criticality, mostly automated from what the platform already knows, and ends in a clear outcome with conditions. On a good platform most checks pass by default because the golden path satisfies them, so the human review focuses on the parts that are unusual.

## Detail

**What a PRR is for.** It moves the discovery of operational gaps from the first incident to a conversation a few weeks before launch. The classic failures it catches are mundane: no alert on the thing users care about, a runbook that does not exist, a single replica, a dependency on a service with a weaker SLO, a database with backups nobody has restored, or an owning team with no on-call rotation. Each is cheap to fix before launch and expensive during an outage.

**Who it serves.** The service team, who get an expert second opinion on operability; the on-call engineers, who will be woken by the service; and, for a platform team, the platform itself, because every service launched on it inherits and depends on its capabilities. It is not a gate for its own sake, and framing it as a pass/fail exam produces teams that game the checklist.

**The areas a checklist should cover:**

| Area                | Typical questions                                                             |
| ------------------- | ----------------------------------------------------------------------------- |
| Ownership           | Named owning team in the catalogue? On-call rotation with an escalation?      |
| SLOs and alerting   | SLIs defined from the user's side? Burn-rate alerts that page? Runbook links? |
| Observability       | Metrics, logs, and traces flowing? A dashboard someone new could read?        |
| Deploy and rollback | Progressive rollout? Rollback tested, and is it faster than a fix forward?    |
| Capacity            | Load tested to expected peak plus headroom? Autoscaling limits set?           |
| Dependencies        | Each one listed with its SLO? Timeouts, retries, and a degraded mode?         |
| Data                | Backups configured, restore tested, RPO and RTO agreed for the tier?          |
| Resilience          | Spread across zones? Disruption budgets? A failure test or game day run?      |
| Security            | Secrets from the platform store? Image signed and scanned? Least-privilege?   |

**Tier the review by criticality.** A tier-1 customer-facing payments service deserves a full review with a reliability engineer, a load test, and a game day. An internal batch job needs a short automated check. Applying the heaviest process to everything makes the PRR a bottleneck that teams route around; applying the lightest to everything misses the services that can hurt the business.

**Automate the checks the platform can already answer.** Whether a service has an owner, an SLO definition, alerts with runbook annotations, more than one replica, a disruption budget, a signed image, and a backup policy are all facts the catalogue and cluster already hold. Running these continuously as a scorecard, rather than as a one-off form, means readiness is visible from day one of development and does not decay after launch. The [service scorecards question](../developer-experience/how-do-you-design-service-scorecards-that-teams-do-not-resent.md) covers doing this without breeding resentment.

**The golden path should make most items pass by default.** If the service template ships with standard dashboards, burn-rate alerts generated from an SLO file, a disruption budget, topology spread, and backups wired to the tier, most of the checklist is satisfied the moment a team scaffolds the service. That is the platform's real contribution to production readiness: not the review, but the defaults that make the review short. Items that keep failing across many reviews are a signal that the platform is missing a default.

**Keep the human part focused on judgement.** Automation cannot tell you whether the failure modes are understood, whether the degraded behaviour when a dependency fails is acceptable, or whether the load test resembled real traffic. Spend the meeting on the architecture, the dependencies, and a walkthrough of "what happens when X fails", with the owning team explaining and a reviewer asking questions.

**End with a clear outcome.** Typically: ready, ready with conditions (specific items with owners and dates, often due before a traffic milestone), or not yet. Record it next to the service in the catalogue. Conditions without dates are how launch reviews turn into permanent exceptions.

**Re-review on significant change.** A service that was ready at launch may not be after it doubles its traffic, adds a new datastore, or moves up a criticality tier. Triggering a lightweight re-review on tier changes or architecture changes keeps the result honest.

**Trade-offs.** A PRR costs reviewer time, which is scarce, and it can slow launches. The mitigations are tiering, automation, and starting the review early enough that it informs design rather than blocking a date. If the PRR is also a condition for an SRE or platform team taking over the pager, be explicit about that contract, and about how a service can be handed back if it stops meeting the bar.

## Example

```yaml
# The readiness definition for a tier, evaluated continuously by the platform
# against the catalogue and the cluster. Human review covers the rest.
apiVersion: platform.example.com/v1
kind: ReadinessStandard
metadata: { name: tier-1 }
spec:
  appliesTo: { tier: 1 }
  automatedChecks:
    - { id: owner, rule: "catalogue.owner is a team with an on-call schedule" }
    - { id: slo, rule: "at least one SLO defined in slo.yaml" }
    - { id: alerts, rule: "burn-rate alerts exist and every page has a runbook annotation" }
    - { id: replicas, rule: "minReplicas >= 3 and topology spread across zones" }
    - { id: pdb, rule: "PodDisruptionBudget present" }
    - { id: image, rule: "image signature verified and no critical CVEs older than 14 days" }
    - { id: backups, rule: "every datastore has a backup policy and a restore test in the last 90 days" }
  humanReview:
    required: true
    reviewers: [reliability-engineer, platform-on-call-representative]
    topics:
      - "Dependency walkthrough: what happens when each one is slow or down?"
      - "Load test method and result versus expected peak plus 50% headroom"
      - "Rollback demonstration in staging"
      - "Game day result for the top failure mode"
  outcomes: [ready, ready-with-conditions, not-yet]
  reReviewOn: [tier-change, new-datastore, traffic-doubled]
```

```text
Readiness report for a new tier-1 service, three weeks before launch.

  $ platform readiness payments-ledger

  AUTOMATED (from the catalogue and cluster)
    ✓ owner            team-ledger, on-call schedule present
    ✓ slo              2 SLOs: availability 99.95%, write latency p99 < 250ms
    ✓ alerts           burn-rate alerts generated from slo.yaml, runbooks linked
    ✓ replicas         3, spread across 3 zones        (from the service template)
    ✓ pdb              minAvailable 2                  (from the service template)
    ✓ image            signed, no critical CVEs
    ✗ backups          policy present; NO restore test recorded

  HUMAN REVIEW
    ✓ dependency walkthrough: fraud-score is slow -> 800ms timeout, queue for
      later scoring; accepted by product
    ✗ load test used 40% of expected peak traffic; re-run required
    ✓ rollback demonstrated in staging in 3 min

  OUTCOME  ready-with-conditions
    - restore test for ledger-db              owner: Ana   due: 2026-10-14
    - load test at 150% of expected peak      owner: Jo    due: 2026-10-16
    launch gated on both; recorded in the catalogue entry

  6 of 7 automated checks passed because the service used the golden path.
  The review time went on the two things only people could judge.
```

## Interview tips

- Start with the purpose: finding operational gaps before the first incident, not certifying a service. Then name who it serves, including the on-call engineers who will carry it.
- Give the checklist areas quickly - ownership, SLOs and alerting, observability, rollback, capacity, dependencies, data, resilience, security - rather than reciting every item.
- Tiering by criticality is the point that shows you have run these; one heavyweight process for everything becomes a bottleneck that teams avoid.
- The platform angle is the strongest part of the answer: automate the checks the platform can answer, and make the golden path satisfy most of them by default, so the human review is short and focused on judgement.
- Say that repeated failures of the same item across reviews mean the platform is missing a default.
- Close with the outcome - ready, ready with conditions, not yet - with owned, dated conditions and re-review triggers. Expect a follow-up on how you handle a team that wants to launch anyway.

---

[⬅ Back to Platform Reliability](./README.md) · [All topics](../README.md)
