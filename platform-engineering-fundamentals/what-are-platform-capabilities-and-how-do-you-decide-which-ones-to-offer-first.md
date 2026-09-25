---
title: "What are platform capabilities and how do you decide which ones to offer first?"
id: 10
category: "Platform Engineering Fundamentals"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-engineering-fundamentals
  - interview-questions
---

# What are platform capabilities and how do you decide which ones to offer first?

**Short answer:** A platform capability is a distinct outcome the platform delivers to its users through a self-service interface - "get a database", "deploy a service", "open a preview environment", "get a secret into my workload" - together with the automation, defaults, guardrails, documentation, and support behind it. You decide which to offer first from evidence: the capabilities that the most teams need, that currently cost them the most time or cause the most incidents, and that you can deliver reliably with the team you have. In practice the first capability is almost always the path from repository to running production service for the most common workload shape.

## Detail

**A capability is an outcome, not a tool.** "We run Vault" is a tool. "A service can read a secret at runtime using its workload identity, rotated automatically, with access audited" is a capability. Framing capabilities as outcomes keeps the roadmap focused on what users get and lets you change the implementation later. The CNCF Platforms white paper describes a set of capability areas along these lines, which most platforms eventually cover:

| Area                         | Typical capability                                                    |
| ---------------------------- | --------------------------------------------------------------------- |
| Scaffolding and golden paths | Create a new service from a template with everything wired            |
| Build and test automation    | A shared, reusable pipeline with caching, scanning, and SBOMs         |
| Delivery and verification    | Deploy, promote, and roll back across environments                    |
| Development environments     | Ephemeral preview environments and fast local loops                   |
| Infrastructure services      | Databases, queues, caches, and buckets on request                     |
| Identity and secrets         | Workload identity and runtime secret delivery                         |
| Observability                | Logs, metrics, traces, and SLO alerts on by default                   |
| Security and compliance      | Policy enforcement, image signing, and audit evidence                 |
| Artefact storage             | Container and package registries with retention and provenance        |
| Portals and APIs             | Catalogue, ownership, docs, and a programmatic interface to all of it |

Nobody builds all of these at once, and a young platform should not try.

**What makes a capability complete.** Each capability needs an interface, automation, sensible defaults, guardrails, documentation, an owner on the platform team, and a support expectation. A capability missing any of these generates tickets rather than removing them - which is why it is better to ship three complete capabilities than eight half-finished ones.

**How to choose the first ones - gather evidence first.** Before ranking anything, collect data on where time and risk actually go:

- **Shadow a few teams** shipping a new service and count the manual steps and the waits.
- **Mine the support channel and ticket queue** for the requests that repeat.
- **Read the last year of incident reviews** for findings that name a missing default - no alert, no backup, a leaked credential.
- **Look at what teams have built themselves.** Three teams each maintaining a home-grown database module is a capability the organisation already wants.

**Then score candidates on a few explicit criteria:**

- **Reach** - how many teams need it now, and how many future services will.
- **Pain** - hours lost per use, or incident and security risk it removes.
- **Frequency** - how often it is needed. Service creation happens often; disaster recovery drills are not.
- **Dependency** - whether other capabilities build on it. Workload identity and a deployment path underpin almost everything else, so they tend to go first even when they are not the loudest request.
- **Feasibility** - whether you can build and run it reliably with current staff, or buy it.

**Why the deployment path usually wins.** The route from repository to monitored production service scores well on every criterion: every team uses it, it is frequent, it is the dependency for observability and policy defaults, and it is where onboarding time is usually lost. Portals, by contrast, are a common and costly first choice - they demo well but deliver little until there is provisioning behind them.

**The trade-offs.** Evidence-based ranking favours the common case, so specialised teams - ML, data, mobile - may wait a long time and build their own; say how you will support them in the meantime. A dependency-first order can feel slow to users who wanted the visible feature. And some capabilities jump the queue for reasons other than developer pain: a regulatory deadline or an audit finding can make policy enforcement or audit evidence the first priority regardless of scoring. Saying no to the rest is part of the job, covered in [building a platform roadmap and saying no](../platform-team-and-operating-model/how-do-you-build-a-platform-roadmap-and-say-no.md); whether to build or buy each one is covered in [deciding whether to build or buy a platform capability](../platform-architecture/how-do-you-decide-whether-to-build-or-buy-a-platform-capability.md).

## Example

```text
Candidate capabilities, scored 1-5 after three weeks of research across 22 teams.
Weighted: reach x2, pain x2, frequency x1, dependency x2, feasibility x1.

Capability                     Reach Pain Freq Dep Feas  Score  Evidence
-----------------------------  ----- ---- ---- --- ----  -----  ---------------------------------
Service scaffold + deploy path   5    4    4    5   4     36    new service takes 6 days median
Workload identity + secrets      5    4    3    5   3     34    2 leaked static keys this year
Default dashboards + SLO alerts  5    3    3    3   5     30    7 incidents with no alert
Self-service Postgres            3    4    2    2   3     23    14 tickets/month; 3 home-grown
                                                                modules
Preview environments             3    3    4    1   2     20    requested by 5 teams
Developer portal                 4    1    2    1   3     17    "nice to have" in interviews

Quarter 1: scaffold + deploy path, with workload identity built in.
Quarter 2: default observability; self-service Postgres.
Deferred:  preview environments, portal - revisit with adoption data.
Exception: audit evidence for image signing pulled forward (regulatory deadline).
```

## Interview tips

- Define a capability as an outcome with an interface, not as a tool - then list the pieces that make it complete.
- Show the evidence you would gather before prioritising. Interviewers are testing whether you would research users or start from what is technically interesting.
- Name the ranking criteria out loud, and point out that dependencies such as workload identity often go first even when they are not the loudest request.
- Say that the portal is rarely the first capability, and explain why: presentation without provisioning.
- Expect "what about the team whose needs are not on your list?" - have an answer about documented escape hatches and enabling support until their capability is justified.

---

[⬅ Back to Platform Engineering Fundamentals](./README.md) · [All topics](../README.md)
