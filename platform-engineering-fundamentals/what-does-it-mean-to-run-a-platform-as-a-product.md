---
title: "What does it mean to run a platform as a product?"
id: 11
category: "Platform Engineering Fundamentals"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-engineering-fundamentals
  - interview-questions
---

# What does it mean to run a platform as a product?

**Short answer:** It means treating your internal engineers as customers who could choose something else, and adopting the apparatus that implies: user research, a prioritised roadmap driven by their problems rather than your interests, versioned interfaces with migration support, real documentation, a support model, and adoption as the headline success metric. The practical test is whether your backlog is populated by evidence from users or by technology you wanted to try.

## Detail

**Voluntary adoption is what makes it a product.** If teams must use the platform, you have a captive market and no feedback signal - complaints become the only channel, and they arrive as escalations. Keeping adoption voluntary for anything that is not a security guardrail is what keeps the feedback loop honest. This is why golden paths and product thinking are the same argument.

**What the practice actually involves:**

- **User research.** Sit with three teams and watch them deploy. The gap between what teams say in a survey and what they do is where your roadmap is. Support-channel questions and the steps people do by hand are the richest sources.
- **A named product owner.** Someone accountable for outcomes rather than delivery - who says no, sequences work, and can explain the platform's value in the terms leadership funds. Platform teams without this build what is technically interesting.
- **Versioned interfaces and migrations you perform.** The platform's API is a contract. Breaking it without a version, a deprecation window, and bot-raised migration pull requests is how a platform loses trust permanently. Migrate for people; do not ask them to.
- **Documentation as a first-class deliverable.** For an internal product, docs are the support interface. A capability without documentation generates support load that scales with adoption, which is the worst possible shape.
- **A support model with expectations.** A channel, a response expectation, an escalation path, and an on-call rotation. "Ask in Slack and someone might answer" is not a support model for critical infrastructure.
- **Marketing, unironically.** Internal launch posts, demos, office hours, and migration guides. A capability nobody knows about has zero adoption regardless of quality.

**Metrics that behave like product metrics:** adoption (share of services on the supported path), retention (teams that stayed after adopting - the ones who leave are your most valuable interview), time to first deploy for a new service, lead time for change, and a periodic developer satisfaction measure. Component counts and ticket throughput are activity, not outcome.

**Where the analogy breaks, and saying so is a strong move.** You cannot deprecate an internal capability the way a SaaS vendor sunsets a tier - your users cannot switch away, so you own the migration. Your funding comes from a budget conversation rather than revenue, so the value story has to be told in cost and cycle time. And some things must be mandated; a platform is a product with a regulatory floor underneath it.

## Example

```text
Two backlogs for the same quarter. The difference is where the items came from.

Project-shaped platform team (what to avoid)
  - Migrate to service mesh                        (source: architecture ambition)
  - Build Backstage portal                         (source: conference talk)
  - Replace Helm with our own templating           (source: engineer preference)
  - Multi-cluster federation                       (source: "we'll need it eventually")
  Outcome: months of work; developers still cannot get a staging database.

Product-shaped platform team
  - Self-service Postgres with backups + PITR      (source: 14 support tickets/month,
                                                    3 teams built their own badly)
  - Cut new-service setup 3 days -> 30 min         (source: onboarding interviews;
                                                    measured, published baseline)
  - Migrate all consumers off Service API v1       (source: v2 shipped last quarter;
                                                    bot-raised PRs, we do the work)
  - Fix the 4 reasons teams left the golden path   (source: exemption register)
  Outcome: adoption 40% -> 78%; support tickets down; measurable lead-time change.

Every item in the second list names its evidence. That is the whole discipline.
```

## Interview tips

- The one-line version: a platform is a product with users who can route around you - so you need research, a roadmap, versioning, docs, and support.
- Quote adoption as the headline metric and be able to say how you would adjust it for coercion. Adoption under a mandate measures compliance, not value.
- "Migrate for people, do not ask them to" is a high-signal sentence, and it is the concrete behaviour that distinguishes teams that keep trust.
- Naming where the product analogy breaks - captive users, budget funding, mandatory controls - is what separates senior answers from repeating a blog post.
- Expect "how do you prioritise between two teams both blocked?" Have an answer involving tier, blast radius, and how many future teams the capability unblocks.

---

[⬅ Back to Platform Engineering Fundamentals](./README.md) · [All topics](../README.md)
