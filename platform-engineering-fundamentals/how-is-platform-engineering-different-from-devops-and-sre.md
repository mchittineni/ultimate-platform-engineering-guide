---
title: "How is platform engineering different from DevOps and SRE?"
id: 3
category: "Platform Engineering Fundamentals"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-engineering-fundamentals
  - interview-questions
---

# How is platform engineering different from DevOps and SRE?

**Short answer:** DevOps is a set of cultural principles about shared ownership between development and operations. SRE is a specific engineering practice for making reliability measurable and managed, through SLOs and error budgets. Platform engineering is a delivery model: it builds an internal product that makes the DevOps ideal achievable at scale without every team having to become experts in everything. They are not competing answers to the same question, and saying so is the point of the answer.

## Detail

**The clean separation:**

| Discipline           | Primary question                                                 | Unit of work          | Success looks like                       |
| -------------------- | ---------------------------------------------------------------- | --------------------- | ---------------------------------------- |
| DevOps               | How should development and operations collaborate?               | A practice or norm    | Shared ownership, fast feedback          |
| SRE                  | How reliable is this service, and how much risk can we spend?    | A service's SLO       | Reliability managed, toil reduced        |
| Platform engineering | How do teams get what they need without assembling it each time? | A platform capability | Teams self-serve; the paved road is used |

**Why platform engineering emerged.** DevOps asked product teams to own their operations. In practice that transferred an enormous amount of infrastructure complexity onto people whose job is product code, and the industry's honest description of the result is unsustainable cognitive load. Platform engineering is the response: keep the ownership, remove the requirement to assemble the machinery. It does not repudiate DevOps; it is how DevOps survives at fifty teams.

**Where SRE and platform engineering genuinely overlap.** Both care about reliability, both fight toil, both use automation. The distinction is the customer and the deliverable. An SRE embedded with the checkout team improves checkout's reliability; a platform engineer builds the SLO tooling, dashboards, and alerting defaults that every team including checkout gets for free. SRE optimises a service; platform engineering optimises the conditions under which all services run.

**They stack in practice.** Mature organisations run all three: DevOps as the cultural expectation, platform engineering supplying the paved road, and SRE applied to the highest-tier services - including the platform itself, which needs its own SLOs precisely because everyone depends on it.

**The trap.** Many organisations rename their operations team "platform team" and change nothing: work still arrives as tickets, capabilities are still delivered by humans. That is a service desk. The distinguishing question is whether the team ships interfaces or performs tasks.

## Example

```text
A single request - "my new service needs a Postgres database" - by model:

DevOps-as-practised (no platform)
  Team reads cloud docs, writes Terraform, guesses at backups, sizing, and
  network placement. Ships in days. Every team's answer differs.

Ops team renamed "platform team"
  Team files a ticket. Platform engineer writes the Terraform. Ships in a
  week, consistent, but the platform team is the bottleneck and scales linearly
  with demand.

Platform engineering
  Team adds 4 lines to service.yaml. A controller provisions it with backups,
  PITR, private networking, credentials in the secret store, dashboards, and
  cost tags. Ships in minutes. Platform team's work went into the capability,
  once, not into this request.
```

## Interview tips

- Do not present these as three names for the same job, and do not claim platform engineering "replaced" DevOps - both are common weak answers.
- The strongest framing is cognitive load: platform engineering exists because "you build it, you run it" does not scale without something absorbing the complexity.
- Use the customer test if you are pushed: SRE's customer is a service, the platform team's customer is other engineers.
- Expect "which one are we hiring for?" as an implicit subtext - be ready to say which you have actually done and where you would want support.

---

[⬅ Back to Platform Engineering Fundamentals](./README.md) · [All topics](../README.md)
