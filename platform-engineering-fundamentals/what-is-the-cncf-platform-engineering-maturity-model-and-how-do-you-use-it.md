---
title: "What is the CNCF platform engineering maturity model and how do you use it?"
id: 9
category: "Platform Engineering Fundamentals"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-engineering-fundamentals
  - interview-questions
---

# What is the CNCF platform engineering maturity model and how do you use it?

**Short answer:** It is a framework published by the CNCF's TAG App Delivery Platforms working group, as a companion to the CNCF Platforms white paper, that describes platform maturity across five aspects - investment, adoption, interfaces, operations, and measurement - each with four levels: provisional, operational, scalable, and optimising. Its value is not the score. Used well, it is a structured conversation that finds the aspect holding everything else back and turns it into a short list of improvements; the model itself says reaching the top level should not be a goal in its own right.

## Detail

**The grid.** Each aspect is assessed independently, because organisations are rarely at the same level everywhere:

| Aspect      | Level 1 - Provisional  | Level 2 - Operational | Level 3 - Scalable     | Level 4 - Optimising         |
| ----------- | ---------------------- | --------------------- | ---------------------- | ---------------------------- |
| Investment  | Voluntary or temporary | Dedicated team        | As product             | Enabled ecosystem            |
| Adoption    | Erratic                | Extrinsic push        | Intrinsic pull         | Participatory                |
| Interfaces  | Custom processes       | Standard tooling      | Self-service solutions | Integrated services          |
| Operations  | By request             | Centrally tracked     | Centrally enabled      | Managed services             |
| Measurement | Ad hoc                 | Consistent collection | Insights               | Quantitative and qualitative |

**What each aspect is really asking:**

- **Investment** - how the platform is funded and staffed. Level 1 is side-of-desk work by volunteers; level 3 is a team funded and run as a product with a product owner; level 4 is when other teams contribute capabilities through the platform's own extension points.
- **Adoption** - why teams use it. "Extrinsic push" means mandates and top-down pressure; "intrinsic pull" means teams choose it because it is the easiest route; "participatory" means consumers help shape and extend it. This is the aspect that most exposes an organisation that has confused a mandate with success.
- **Interfaces** - how users consume capabilities. From bespoke per-request processes, to documented standard tools, to genuine self-service, to capabilities that compose into one coherent experience.
- **Operations** - how capabilities are run and maintained over their lifetime. "By request" is a ticket queue; "managed services" is capabilities whose upgrades, patching, and lifecycle the platform handles on the consumer's behalf.
- **Measurement** - how the team knows it is working. From anecdote, to collected data, to data that drives decisions, to combining quantitative metrics with qualitative user research.

**How to use it - as a diagnostic, not a certificate.** A workable approach:

1. **Assess with users, not just the platform team.** Run the assessment with a handful of product engineers and their leads. Platform teams consistently rate their interfaces and adoption higher than their consumers do, and that gap is itself a finding.
2. **Score each aspect separately and record the evidence.** "Interfaces: level 2, because database requests still go through a ticket" is useful. "We are about a 2.5" is not.
3. **Find the constraining aspect.** The aspects depend on one another. Self-service interfaces (level 3) with ad hoc measurement (level 1) means you cannot prove the investment was worth it; product-style investment with extrinsic-push adoption means you are funding a product nobody chose. The lowest or most mismatched aspect is usually the one to fix first.
4. **Pick a target level per aspect deliberately.** The model is explicit that higher levels cost more. A thirty-engineer company may be well served at level 2 on investment and operations indefinitely. Tie the target to a business need, not to the top of the grid.
5. **Turn it into roadmap items and reassess on a cadence.** Every gap becomes a concrete piece of work with an owner - "publish a baseline for time to first deploy", "replace the database ticket with a self-service claim" - and the assessment is repeated every six or twelve months to show movement.

**Where it fits with other models.** It pairs naturally with the CNCF Platforms white paper, which describes the capabilities a platform typically offers, and with delivery and experience metrics such as DORA's, which give the measurement aspect its numbers. It is complementary to Team Topologies, which describes team interaction rather than platform maturity. Measurement in practice is covered in [how to measure platform adoption and success](../platform-team-and-operating-model/how-do-you-measure-platform-adoption-and-success.md).

**Limitations to name.** The levels are qualitative, so two assessors can reasonably disagree. It is easy to game if the assessment is used to judge the platform team rather than to improve the platform - scores inflate as soon as they feed a performance review. And a maturity grid says nothing about whether the platform is solving the organisation's most important problem; a very mature platform for the wrong workloads still fails.

## Example

```text
Assessment, mid-sized organisation (40 product teams), run with 6 engineers
from 4 consumer teams plus the platform team. Evidence recorded per score.

Aspect       Score  Evidence                                          Target
-----------  -----  ------------------------------------------------  ------
Investment     3    Funded team of 7 with a product owner and roadmap    3
Adoption       2    68% of services on the golden path, but mostly       3
                    because the old pipeline was switched off
Interfaces     3    Services, databases, queues are self-service         3
                    via service.yaml; environments still a ticket
Operations     2    Upgrades tracked centrally but performed by each     3
                    team from a runbook
Measurement    1    No baseline for lead time or onboarding; one         2
                    survey two years ago

Constraint: measurement. Adoption cannot be shown to be pull rather than push,
and the investment is undefended at the next budget cycle.

Next two quarters:
  1. Baseline time to first deploy and lead time for change (DORA metrics)
  2. Quarterly developer survey plus five user interviews per quarter
  3. Automate the base image and runtime upgrades teams currently do by hand
  4. Reassess in six months, same assessors
```

## Interview tips

- Know the five aspects and be able to name a couple of level descriptions - "extrinsic push" versus "intrinsic pull" for adoption is the pair worth remembering.
- Stress that the output is a list of things to improve, not a score. Candidates who talk about "getting to level 4" signal that they have not used it.
- Explain that you assess with consumers present, and that the disagreement between platform team and users is the most valuable result.
- Expect "where would you put us?" - ask for evidence per aspect before answering, and identify the constraining aspect rather than giving an average.
- Name its limits: qualitative, gameable, and silent on whether the platform is solving the right problem.

---

[⬅ Back to Platform Engineering Fundamentals](./README.md) · [All topics](../README.md)
