---
title: "How do SPACE, DevEx, and DX Core 4 differ as measurement frameworks?"
id: 24
category: "Developer Experience"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - developer-experience
  - interview-questions
---

# How do SPACE, DevEx, and DX Core 4 differ as measurement frameworks?

**Short answer:** They answer different questions and sit at different altitudes. SPACE (2021) is a _framework for choosing metrics_. It names five dimensions of productivity and argues you need several of them at once, but it deliberately prescribes no specific metrics. The DevEx framework (2023) is a _diagnostic model_ of what developers experience: feedback loops, cognitive load, and flow state, measured mostly by asking developers. DX Core 4 (late 2024) is a _prescriptive metric set_: four dimensions, one key metric each, designed to be reported to executives and to absorb DORA, SPACE, and DevEx into something a company can deploy. A platform team typically uses DevEx to decide what to fix, DORA-style system metrics to confirm it worked, and something like Core 4 when leadership asks for one productivity picture.

## Detail

**SPACE: a warning against single metrics.** Published by Nicole Forsgren, Margaret-Anne Storey, and colleagues from GitHub, Microsoft Research, and the University of Victoria, SPACE stands for Satisfaction and well-being, Performance, Activity, Communication and collaboration, and Efficiency and flow. Its central claim is that productivity is multidimensional, so any single metric (commits, story points, PR count) is misleading. It recommends picking metrics from at least three dimensions and mixing perceptual (survey) and system data. Its strength is as a check: "our dashboard is all Activity and no Satisfaction" is a SPACE critique. Its weakness is that it does not tell you what to measure, so two organisations "using SPACE" can have nothing in common.

**DevEx: a model of the developer's day.** Written by Abi Noda, Margaret-Anne Storey, Nicole Forsgren, and Michaela Greiler, the DevEx framework narrows the focus to the lived experience of doing the work, along three dimensions:

- **Feedback loops**: how quickly developers learn whether something worked (build, test, review, deploy).
- **Cognitive load**: how much they have to understand to get something done.
- **Flow state**: how often they get uninterrupted, focused time.

Each dimension is measured with both perceptions ("how satisfied are you with CI speed?") and workflows ("how long does CI take?"). This is the most useful of the three for a platform team, because every dimension maps to something a platform can change. Slow feedback loops point to CI and environments. Cognitive load points to abstractions and documentation. Flow points partly to process (meetings, interruptions), which is a useful reminder that not everything is a tooling problem.

**DX Core 4: a deployable scorecard.** Built by DX (Noda, Laura Tacho, and collaborators including Storey and Greiler), Core 4 is explicitly an attempt to reconcile the others into a small, balanced set that leadership can compare over time:

| Dimension     | Key metric                                   | Borrowed from       |
| ------------- | -------------------------------------------- | ------------------- |
| Speed         | Diffs (merged PRs) per engineer              | Activity/flow, DORA |
| Effectiveness | Developer Experience Index (DXI), survey     | DevEx, SPACE        |
| Quality       | Change failure rate                          | DORA                |
| Impact        | Percentage of time spent on new capabilities | Business alignment  |

Each dimension also has secondary metrics, such as lead time, deployment frequency, and perceived rate of delivery. The four are meant to counterbalance one another: pushing Speed while Quality falls is visible straight away. The contentious choice is diffs per engineer. Core 4 insists it is only ever read as an organisational average and never at the individual level, but critics point out that it is an activity metric and will be gamed as soon as anyone treats it as a target. It is also worth saying that DXI is a proprietary survey instrument, so Core 4 in full is easiest to run with DX's tooling. The structure can be copied with your own survey.

**How they compare:**

| Question                       | SPACE                          | DevEx                             | DX Core 4                         |
| ------------------------------ | ------------------------------ | --------------------------------- | --------------------------------- |
| What is it?                    | Framework for picking metrics  | Diagnostic model of friction      | Prescriptive metric set           |
| Does it name specific metrics? | No (examples only)             | Suggests measures per dimension   | Yes, one key metric per dimension |
| Main data source               | Mix of survey and system       | Mostly survey, plus workflow data | Mix, with a standard survey (DXI) |
| Best audience                  | Whoever designs the metric set | Platform and enablement teams     | Engineering leadership, finance   |
| Main risk                      | Too vague to act on            | Survey fatigue, perception drift  | Activity metric becomes a target  |

**Where DORA fits.** DORA metrics are not a competitor. They measure delivery performance (throughput and instability), and all three frameworks include DORA-style metrics somewhere: SPACE under Performance and Efficiency, DevEx as workflow measures of feedback loops, Core 4 directly under Quality and as secondary Speed metrics. See [What are the DORA metrics and what do they measure?](./what-are-the-dora-metrics-and-what-do-they-measure.md).

**How a platform team should choose.** Use the question you need answered. "Where should we invest next quarter?" is a DevEx question. "Did the golden path improve delivery?" is a DORA question. "Is engineering getting more productive, and can we show the board?" is a Core 4 question. SPACE is the review you apply to whatever you end up with. The rules that apply to all of them are the same: never report individuals, combine perception with system data, and prefer trends over benchmarks.

## Example

```text
A platform team's metric set, deliberately assembled from all three.

  QUESTION WE ANSWER                 METRIC                              FRAMEWORK
  Where does friction live?          DevEx survey: feedback loops,       DevEx
                                     cognitive load, flow (quarterly)
  Is the fix working?                CI p95, PR wait-for-review p50,     DevEx workflow
                                     time to first deploy (new service)  measures
  Is delivery improving?             lead time, deploy frequency,        DORA
                                     change fail rate, rework rate
  What do we tell leadership?        Speed / Effectiveness / Quality /   Core 4 shape,
                                     Impact, org-level only              own survey

  SPACE check before publishing:
    Satisfaction  - yes (survey)          Performance - yes (fail rate, rework)
    Activity      - yes, org-level only   Communication - WEAK: add review wait
    Efficiency    - yes (CI, lead time)   and cross-team dependency questions
```

## Interview tips

- Lead with altitude: SPACE tells you how to choose metrics, DevEx tells you where friction comes from, Core 4 gives you a specific set to report. Saying "they are three lists of metrics" misses the point.
- Name the three DevEx dimensions and map each one to a platform lever. That is what makes the answer useful to a platform team.
- Know the Core 4 dimensions and be ready to criticise diffs per engineer. A balanced view (useful at org level, harmful if it becomes a target) lands better than either defending or dismissing it.
- Place DORA as delivery performance that all three include, not as a fourth competitor.
- Close with the rules that apply to all of them: no individual measurement, perception plus system data, trends over benchmarks.

---

[⬅ Back to Developer Experience](./README.md) · [All topics](../README.md)
