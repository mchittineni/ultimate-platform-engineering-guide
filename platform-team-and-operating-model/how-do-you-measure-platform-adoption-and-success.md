---
title: "How do you measure platform adoption and success?"
id: 125
category: "Platform Team and Operating Model"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-team-and-operating-model
  - interview-questions
---

# How do you measure platform adoption and success?

**Short answer:** Adoption as the headline - the share of services on the supported path, adjusted for whether adoption was voluntary - plus retention, the outcomes adoption is supposed to produce such as lead time and change failure rate, and a periodic satisfaction measure. What you must not measure is components shipped, resources managed, or tickets closed, because those are activity and a platform can maximise all three while making nobody's life better.

## Detail

**Adoption is the headline metric, with one important qualifier.** The share of services using each capability tells you whether teams find it worth using. But adoption under a mandate measures compliance, not value - so it should be reported alongside whether the capability is mandatory, and voluntary adoption is the number that carries information.

**Retention is the sharper signal, and it is the one platform teams neglect.** A team that adopted a capability and then left is your most valuable interview. Voluntary adoption tells you the capability looked worth trying; retention tells you it was. Tracking departures, and treating each as a defect report rather than a betrayal, is what separates teams that improve from teams that keep shipping capabilities.

**Measure the outcome the platform exists to produce.** Adoption is a means. The end is faster, safer delivery, which means lead time from commit to production, deployment frequency, change failure rate, and time to restore - the DORA set - plus time to first production change for a new engineer and time to create a new service. Compare teams on the platform against teams not on it, and compare before against after, while being honest that this is not a controlled experiment.

**A useful set, with the trap each avoids:**

| Metric                                         | Avoids the trap of                         |
| ---------------------------------------------- | ------------------------------------------ |
| Voluntary adoption per capability              | Counting mandated compliance as value      |
| Retention after adoption                       | Celebrating adoption that did not stick    |
| Lead time for change (p50 and p95)             | Measuring only the happy path              |
| Change failure rate                            | Optimising speed at the cost of safety     |
| Time to first production change (new engineer) | Ignoring onboarding cost                   |
| Time to create a new service                   | Measuring the demo rather than the journey |
| Escape hatch and exception usage               | Assuming the paved road fits               |
| Support question volume by category            | Treating support load as unavoidable       |
| Developer satisfaction (periodic survey)       | Trusting system metrics alone              |
| Platform overhead per service                  | Ignoring whether the platform amortises    |

**Escape hatch usage is an underrated success measure.** If teams leave the golden path for the same reason repeatedly, adoption will plateau no matter what you build. That register is both a health metric and a roadmap.

**Publish the numbers, including the bad ones.** A platform team that reports its own adoption plateau and its own departures builds credibility that a team reporting only wins does not. It also makes the prioritisation conversation evidential rather than political.

**Baseline before you build, because you will be asked.** Lead time, onboarding time, and time to create a service, measured before the platform exists, are cheap to capture and impossible to reconstruct later. The most common reason a platform team cannot demonstrate value is that nobody recorded the starting point.

**Beware the metrics that look like success and are not.** Number of clusters managed, resources provisioned, capabilities shipped, tickets closed, dashboards created. Each can rise while developer experience worsens. Ticket throughput is the most actively harmful, because it rewards handling requests rather than eliminating them.

**Do not measure individuals or rank teams.** Metrics used for performance assessment are gamed within a quarter, and you lose the signal permanently. Aggregate trends are legitimate; league tables are not.

## Example

```text
The platform scorecard - and note the two rows that carry the most information.

  ADOPTION                                 now    6mo ago   note
    services on the golden path            78%      41%     VOLUNTARY - the
                                                            number that means
                                                            something
    self-service provisioning              84%      52%     voluntary
    generated observability                91%      63%     voluntary
    signed images at admission            100%     100%     MANDATED - this is
                                                            compliance, not value.
                                                            Reported separately.
    RETENTION after adoption               96%      89%     <-- the sharper signal
      teams that adopted then left: 2 (of 47)
      team-data left self-service provisioning: needed a resource we do not
      support, went back to Terraform. TREATED AS A DEFECT REPORT.
      team-ops left the golden path: our default probe configuration did not fit
      their workload. Fixed; they returned.

  OUTCOMES (what adoption is supposed to produce)
    lead time p50            3.2h    (was 5.1h)     baseline before platform: 2.4d
    lead time p95            6.1d    (was 6.4d)     <-- barely moved. Review queue,
                                                        not our tooling. Say so.
    deploy frequency/svc/wk   4.1     (was 3.3)
    change failure rate        11%    (was 14%)     speed did NOT cost safety
    time to restore p50       24m     (was 31m)
    new engineer -> 1st prod change  4.1d  (was 13.5d)
    time to create a service         41m   (was 3d)

  HEALTH
    escape hatch usage: GPU scheduling (6 teams)    <-- MISSING CAPABILITY, proven
                                                        demand. Roadmap item.
                        readinessProbe override (11) <-- WRONG DEFAULT. Fix it.
    support questions: 41/mo -> 9/mo after exposing in-flight deploy status
    developer satisfaction: 3.9/5 (was 3.4)  n=84, 71% response
    platform overhead per service: $232 (was $389)  <-- amortising

  PUBLISHED IN FULL, including the p95 that barely moved and the two departures.
```

```text
Metrics deliberately NOT on the scorecard, and why:

  clusters managed .................. rose from 4 to 9. That is COST, not success.
  resources provisioned ............. rises with growth regardless of quality
  capabilities shipped .............. we shipped 14; only 9 have >50% adoption.
                                      The count says nothing.
  tickets closed .................... actively harmful. Rewards handling requests
                                      rather than eliminating them. A platform
                                      optimising this becomes a better service
                                      desk, not a platform.
  dashboards created ................ nobody opens most of them
  per-team rankings ................. gamed within a quarter, signal lost
                                      permanently

  The test for any candidate metric: could it improve while developer experience
  gets worse? If yes, it is activity, not outcome.
```

## Interview tips

- Lead with adoption as the headline and immediately qualify it: adoption under a mandate measures compliance, so voluntary adoption is the number that carries information.
- Retention is the differentiator. Most candidates stop at adoption; saying that a team which adopted and left is your most valuable interview shows product thinking.
- Name the DORA metrics as the outcome layer, and be honest that comparing on-platform against off-platform is not a controlled experiment.
- Baseline before building is the practical warning, and the most common reason platform teams cannot demonstrate value.
- Escape hatch usage as both a health metric and a roadmap connects measurement to what you would do next.
- Give the explicit list of metrics you would refuse, with ticket throughput as the actively harmful one because it rewards handling requests rather than eliminating them.
- The test - could this metric improve while developer experience worsens - is a crisp closing heuristic, along with refusing to rank teams.

---

[⬅ Back to Platform Team and Operating Model](./README.md) · [All topics](../README.md)
