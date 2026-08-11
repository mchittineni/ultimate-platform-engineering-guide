---
title: "How do you decide whether your organisation needs a platform team?"
id: 6
category: "Platform Engineering Fundamentals"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-engineering-fundamentals
  - interview-questions
---

# How do you decide whether your organisation needs a platform team?

**Short answer:** You need a platform team when the same infrastructure work is being repeated by enough teams that centralising it costs less than the duplication, or when consistency is a hard requirement you cannot meet by convention. The signal is repetition and drift, not headcount alone - though as a rough guide, dedicated platform investment starts paying off somewhere around a dozen stream-aligned teams, and earlier if compliance demands provable uniformity.

## Detail

**The signals that say yes:**

- **Repetition with divergence.** Every team writes its own pipeline, and no two are alike. The cost is not the duplicated effort, it is that improvements do not propagate and each variant fails differently.
- **The same questions, endlessly.** Your senior infrastructure engineers spend their week answering "how do I get a database", "why is my deployment stuck", "what do I put in this Helm chart".
- **Reliability that correlates with who set the service up.** Some services have alerts, backups, and runbooks; others do not, for no reason other than history.
- **Compliance requires proof, not intent.** If you must demonstrate that every service encrypts data, logs access, and is patched, convention will not survive an audit.
- **Onboarding time is measured in weeks.** A new engineer needing three weeks to ship a service is a cognitive load problem.
- **Infrastructure work is blocking product work through a ticket queue.** The queue is the symptom; the platform is the treatment.

**The signals that say not yet:**

- Fewer than roughly five teams, one runtime, one cloud account. A template repository and a shared pipeline is the correct platform at this size.
- The bottleneck is elsewhere. If deployments are fine and the constraint is unclear requirements or a slow test suite, a platform team will not help and will consume your strongest infrastructure engineers.
- You cannot staff it properly. A platform team of one becomes a person-shaped ticket queue with a title, and when they leave you have critical undocumented infrastructure.
- No one will own it as a product. Without someone doing user research and prioritisation, you get a technically interesting platform nobody adopts.

**The honest cost.** A platform team is typically three to six engineers who are no longer shipping product, plus a permanent operational commitment: the platform becomes critical infrastructure with its own upgrades, on-call, and support load. If the duplication you are removing is smaller than that, do not do it.

**The intermediate option people forget.** Before a dedicated team, try an enabling rotation: two engineers on a fixed-term mission to build the golden path, then return to their teams. It builds the paved road, spreads knowledge, and gives you evidence about whether the permanent investment is warranted.

**Buy before you build.** For many organisations the right answer is a managed platform - a PaaS, a managed Kubernetes offering with an opinionated delivery tool, or a commercial IDP - with a small team integrating it. Building your own control plane because it is more interesting is the classic misapplication.

## Example

```text
A rough decision test - count what is actually happening, not headcount alone:

  1. How many teams deploy independently?           <5: no  |  5-12: maybe  |  12+: likely
  2. How many distinct pipeline implementations?    1-2: no |  3-5: maybe   |  6+: likely
  3. Do all production services have alerts + an owner recorded?   no -> likely
  4. Time for a new engineer to ship to production? <1d: no  |  >1w: likely
  5. Must you prove uniform controls to an auditor?  yes -> likely
  6. Can you staff 3+ engineers and a product owner? no -> not yet, whatever else

Sequence when the answer is "likely":
  Month 0-1   Research: shadow three teams, count the manual steps, list top pain
  Month 1-3   One golden path for the most common workload shape, end to end
  Month 3-6   Migrate 3-5 volunteer teams yourself; publish adoption + lead time
  Month 6+    Expand paths only where evidence justifies it
```

## Interview tips

- Answer with signals and evidence rather than a headcount threshold; if you give a number, frame it as a rough guide and say what would move it.
- Naming the cost - engineers off product, plus a permanent operational commitment - is what makes the answer credible. Candidates who only list benefits sound like they are selling.
- The enabling-rotation and buy-not-build options are strong differentiators; most candidates jump straight to "hire a platform team".
- Expect "we already have a platform team that everyone complains about" as a follow-up. The answer there is user research and adoption metrics, not more capabilities.

---

[⬅ Back to Platform Engineering Fundamentals](./README.md) · [All topics](../README.md)
