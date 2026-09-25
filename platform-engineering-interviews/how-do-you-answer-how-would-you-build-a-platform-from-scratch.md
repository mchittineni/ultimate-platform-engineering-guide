---
title: "How do you answer 'how would you build a platform from scratch'?"
id: 261
category: "Platform Engineering Interviews"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-engineering-interviews
  - interview-questions
---

# How do you answer 'how would you build a platform from scratch'?

**Short answer:** Refuse to start building. Spend the first phase finding out what actually hurts - shadow three teams, measure the current journey, read the support channel - then ship one complete golden path for the most common workload shape, migrate a handful of volunteer teams yourself, and publish the numbers before expanding. The answer that fails is a technology plan; the answer that succeeds is a sequence with evidence gates and an explicit statement of what you would not build in year one.

## Detail

**Establish the context before answering.** How many teams, what they ship, what the constraints are, what exists today, and what your team size and mandate are. An answer that does not depend on those is a generic answer, and the question is largely a test of whether you ask.

**Phase one is research, and say so confidently.** Two to four weeks: sit with three teams and watch them deploy, measure the current journey end to end with timestamps, categorise the support channel, and count the manual steps. Candidates worry this sounds slow; it is the strongest possible opening because it is what distinguishes a platform team that builds the right thing from one that builds an interesting thing.

**Baseline before you build.** Lead time, time to create a service, time for a new engineer to reach production, support volume by category. Cheap to capture now and impossible to reconstruct later, and without it you cannot demonstrate value when you are asked to - which is how platform teams lose their funding.

**Phase two is one complete golden path.** The single most common workload shape, end to end: repository scaffold, pipeline, deploy mechanism, observability, ownership, secrets. Complete beats broad - a team must be able to go from nothing to a monitored, owned production service without a ticket. Half-finished capabilities are worse than absent ones because they still have to be understood.

**Phase three is volunteer migration, done by you.** Three to five teams, chosen because your capability removes their actual pain. Pair with them, fix every rough edge immediately, then have them publish what changed. That write-up is the highest-return artefact of the whole first year.

**Phase four is expansion driven by evidence.** Now the escape hatch register, the support categories, and the adoption plateaus tell you what to build next. Before this point you are guessing; after it you are responding.

**Say what you would not build in year one.** No portal. No service mesh without a named requirement. No multi-cloud abstraction. No custom operator where composition would do. No second supported runtime. Being specific about the exclusions is what makes the plan credible, and it is the part interviewers remember.

**Name the sequencing dependencies.** Some things are prerequisites: a catalogue with ownership before alert routing or scorecards; cost attribution before any cost accountability; provisioning before a portal. Shipping the visible thing first is the classic error and produces a portal over a ticket queue.

**Address the organisational question, because it is half the job.** How you get adoption without a mandate, how you would resist a mandate if offered, who owns the product decisions, how you would report progress. A purely technical answer to this question is incomplete at senior level.

**Have a realistic time frame.** Something useful in the first quarter, real adoption by two quarters, and the operating model in place by a year. Promising a full platform in a quarter reads as inexperience; taking a year to ship anything reads as unable to prioritise.

## Example

```text
"You are the first platform engineer at a company with 25 product teams. Go."

  FIRST, ESTABLISH CONTEXT - the question is partly a test of whether you ask
    what do the teams ship - services, mobile, data pipelines?
    what exists today - any shared tooling, or 25 different setups?
    one cloud? Kubernetes anywhere? regulated?
    is it me, or am I hiring? what is my mandate?
    what is leadership's actual complaint - speed, reliability, cost, or consistency?

  PHASE 1 - RESEARCH AND BASELINE (weeks 1-4). No building.
    shadow 3 teams deploying, saying nothing
    instrument the journey: commit -> production, with timestamps at each stage
    categorise 3 months of the support channel
    count the manual steps in creating a new service
    BASELINE, because it is impossible to reconstruct later:
      lead time p50/p95, time to create a service, new-engineer time to first
      production change, support volume by category
    typical finding, and it is rarely what was expected: the pain is not
    Kubernetes, it is that access provisioning takes four days and there are
    nine different pipelines.

  PHASE 2 - ONE COMPLETE GOLDEN PATH (weeks 5-14)
    pick the most common shape - say a stateless HTTP service
    end to end, and COMPLETE beats broad:
      repository scaffold with a working service and Dockerfile
      one reusable pipeline: build, test, scan, sign, deploy
      one deploy mechanism: GitOps reconciliation
      observability by default: dashboards, SLO, alert routing
      ownership recorded in a generated catalogue
      secrets by reference, no stored credentials
    the test: nothing -> monitored, owned production service, no ticket, under an hour

  PHASE 3 - VOLUNTEER MIGRATION, BY ME (weeks 15-24)
    3-5 teams, chosen because the capability removes their real pain
    I write the migration, I am there for the first deploy
    fix every rough edge the same week
    THEY publish what changed, with numbers
    publish adoption and the baseline deltas

  PHASE 4 - EXPAND ON EVIDENCE (quarter 3 onward)
    now the escape hatch register, support categories, and adoption plateaus
    drive the roadmap. Before this, I was guessing.
    likely next: self-service databases, preview environments, a second workload
    shape - but the evidence decides, not this plan.

  WHAT I WOULD NOT BUILD IN YEAR ONE - the credible part of the answer
    ✗ a portal - Git plus a CLI is sufficient at 25 teams, and a portal with no
      provisioning behind it is a nicer form for the same wait
    ✗ a service mesh - no requirement named
    ✗ any multi-cloud abstraction
    ✗ a custom operator where composition would do
    ✗ a second supported runtime - one, done well
    ✗ scorecards - premature before there is a paved road to score against

  SEQUENCING DEPENDENCIES, so the visible thing is not shipped first
    catalogue with ownership  BEFORE  alert routing and scorecards
    cost attribution          BEFORE  any cost accountability
    provisioning              BEFORE  a portal
    a golden path             BEFORE  policy enforcement on it

  THE ORGANISATIONAL HALF
    adoption: earned, not mandated. If leadership offers a mandate I would ask
    for a quarter and evidence instead - a mandate costs me the feedback signal
    and produces shadow tooling.
    product decisions: mine initially, explicitly, with user research as the input.
    reporting: adoption, the baseline deltas, and support volume - monthly,
    including what has not worked.

  TIME FRAME
    quarter 1: something useful for a handful of teams
    quarter 2: real voluntary adoption, published numbers
    year 1: operating model in place - SLOs, error budget policy, RFC process,
            evidence-driven roadmap
```

## Interview tips

- Ask about context first. The question is deliberately open, and whether you ask is part of what is being assessed.
- Lead with research and baselining, confidently. It sounds slow and it is the strongest opening, because it is what separates building the right thing from building an interesting thing.
- Baselining is the practical detail most candidates miss, and the consequence - being unable to demonstrate value when asked - is worth stating.
- "Complete beats broad" for the first golden path, with the concrete test: nothing to a monitored, owned production service without a ticket.
- Doing the migration yourself, and having the team publish the result, is the adoption mechanism that works and the artefact with the highest return.
- The list of what you would not build in year one is the part interviewers remember. Be specific, and give a reason for each.
- Name the sequencing dependencies - catalogue before scorecards, provisioning before a portal - because shipping the visible thing first is the classic failure.
- Answer the organisational half too: adoption without a mandate, resisting a mandate if offered, who owns product decisions, how you report. At senior level a purely technical answer is incomplete.

---

[⬅ Back to Platform Engineering Interviews](./README.md) · [All topics](../README.md)
