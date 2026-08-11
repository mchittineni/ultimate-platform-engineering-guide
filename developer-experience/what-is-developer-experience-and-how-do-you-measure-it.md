---
title: "What is developer experience and how do you measure it?"
id: 9
category: "Developer Experience"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - developer-experience
  - interview-questions
---

# What is developer experience and how do you measure it?

**Short answer:** Developer experience (DevEx) is how it feels and how long it takes to get software from an idea to production in your organisation - the friction, the waiting, and the number of things you must understand along the way. You measure it with a deliberate mix of system metrics (lead time, deployment frequency, failure rate, recovery time) and perceptual metrics (survey data on friction, confidence, and flow), because either one alone is misleading.

## Detail

**Why you need both kinds of data.** System metrics are objective but narrow: they cannot tell you that the pipeline is fast because engineers stopped writing tests, or that lead time looks good because the painful work happens before the first commit. Perceptual metrics catch what instrumentation misses but are noisy and can drift with morale unrelated to tooling. Used together, the disagreements are the interesting part - a fast pipeline that engineers describe as untrustworthy usually means flaky tests.

**The frameworks worth knowing by name:**

| Framework | Measures                                                                         | Best used for                        |
| --------- | -------------------------------------------------------------------------------- | ------------------------------------ |
| DORA      | Deployment frequency, lead time for change, change failure rate, time to restore | Delivery capability, trend over time |
| SPACE     | Satisfaction, Performance, Activity, Communication, Efficiency and flow          | Choosing a balanced metric set       |
| DevEx     | Feedback loops, cognitive load, flow state                                       | Diagnosing _why_ DevEx is poor       |

DORA tells you how you are doing. The DevEx framework's three dimensions - feedback loops, cognitive load, flow state - tell you where to intervene, which is what a platform team actually needs.

**Metrics a platform team can act on:**

- **Time to tenth commit in production** for a new engineer - a single number capturing onboarding, access, tooling, and docs.
- **Time to create a new production service** - the golden path's real latency, measured end to end rather than at the happy-path demo.
- **Local feedback loop time** - build, test, and run cycle on a laptop or dev environment. Often the biggest daily cost and the most neglected.
- **Pull request lead time**, split into waiting-for-review versus waiting-for-CI. These have completely different fixes.
- **Deployment self-service rate** - what fraction of deploys need no platform-team involvement.
- **Support question volume by category** - your backlog, effectively, and the cheapest research you will ever do.

**The measurement traps.** Never measure individuals - metrics used for performance review get gamed within a quarter and you lose the signal permanently. Do not use commit counts, lines changed, or story points as DevEx proxies; they measure activity, not friction. And beware averages: a median lead time of two hours with a 95th percentile of nine days means most of the pain is invisible in the headline.

**Qualitative research beats both.** The highest-value thing a platform team does is watch three engineers deploy a service while saying nothing. Every survey has a ceiling on what it can reveal; observation does not.

## Example

```text
A quarterly DevEx scorecard that is actually actionable.
Each metric has an owner and a diagnosis, not just a number.

SYSTEM                                 now     prev    target   diagnosis
  lead time, commit -> prod (p50)      3.2h    5.1h    <4h      ok
  lead time, commit -> prod (p95)      6.1d    6.4d    <2d      review queue, not CI
  deploy frequency / service / week    4.1     3.3     >3       ok
  change failure rate                  11%     9%      <15%     ok
  time to restore (p50)                24m     31m     <30m     ok
  CI pipeline duration (p50)           14m     22m     <10m     test parallelism next
  local build + test cycle             4m10s   4m05s   <1m      NOT IMPROVING - biggest
                                                                daily cost, no owner

ONBOARDING
  new engineer -> 1st PR merged        2.1d    3.4d    <2d      ok
  new engineer -> 10th commit in prod  9d      14d     <7d      access requests dominate
  new service -> production            41m     3d      <1h      golden path working

PERCEPTUAL (quarterly survey, 5-point, n=84, 71% response)
  "I can deploy with confidence"       4.1     3.6     >4.0     ok
  "I can find the docs I need"         2.8     2.7     >3.5     WORST SCORE - docs are
                                                                the next investment
  "I spend my time on real work"       3.4     3.2     >4.0     watch

The two flagged rows - local loop time and docs - are the quarter's roadmap.
Notice neither would have been visible from DORA metrics alone.
```

## Interview tips

- Insisting on both system and perceptual data, and explaining what each one misses, is the core of a strong answer.
- Name DORA and the DevEx framework, and be clear about the division of labour: DORA measures outcomes, feedback loops and cognitive load explain them.
- Percentiles, not averages. Saying "p50 and p95 tell different stories and the p95 is where the pain lives" is a strong, concrete signal.
- Say plainly that you would never measure individuals, and why - it will be tested, sometimes as "how would you identify the least productive team?"
- The best close is that you would sit with three teams and watch them deploy before instrumenting anything.

---

[⬅ Back to Developer Experience](./README.md) · [All topics](../README.md)
