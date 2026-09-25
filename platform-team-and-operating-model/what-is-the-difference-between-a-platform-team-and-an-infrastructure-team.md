---
title: "What is the difference between a platform team and an infrastructure team?"
id: 239
category: "Platform Team and Operating Model"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-team-and-operating-model
  - interview-questions
---

# What is the difference between a platform team and an infrastructure team?

**Short answer:** An infrastructure team runs the underlying systems - networks, clusters, cloud accounts, databases - and is usually judged on whether those systems are up and secure. A platform team builds a self-service product on top of that infrastructure for product engineers, and is judged on whether those engineers ship faster and more safely. The practical difference is the interface: an infrastructure team is typically reached through tickets and requests, while a platform team is reached through an API, a template, or a CLI that engineers use themselves.

## Detail

**Who the customer is.** An infrastructure team's customer is often the organisation as a whole: keep production running, keep costs sensible, pass the audit. A platform team's customer is a specific group - the engineers in stream-aligned product teams - and its success depends on whether they choose to use what it provides.

**How work arrives.** This is the clearest test. If a product team needs a database and the answer is "raise a ticket and we will create it", that is an infrastructure service. If the answer is "declare it in your service file and the platform creates it with backups, monitoring, and credentials already wired", that is a platform. The first scales with the infrastructure team's headcount; the second scales with the quality of the interface.

| Dimension       | Infrastructure team                       | Platform team                                      |
| --------------- | ----------------------------------------- | -------------------------------------------------- |
| Primary user    | The organisation, operations, security    | Product engineers                                  |
| Interface       | Tickets, requests, runbooks               | APIs, templates, CLI, golden paths                 |
| Success measure | Uptime, cost, compliance                  | Adoption, lead time, onboarding time, satisfaction |
| Typical output  | A running cluster, a VPC, a database      | "Create a service" in minutes, with defaults       |
| Failure mode    | Becoming a bottleneck as requests pile up | Building something nobody adopts                   |

**The platform usually sits on top of the infrastructure, not instead of it.** Someone still has to run the Kubernetes control plane, manage the cloud landing zone, and patch the nodes. In a small organisation the same team may do both. In a larger one, the infrastructure team (sometimes called cloud engineering or foundations) owns the substrate, and the platform team composes it into something product teams can consume without learning it.

**Product thinking is the real difference.** A platform team does user research, keeps a roadmap, measures adoption, and deprecates things deliberately. An infrastructure team can do all of that too - and the good ones increasingly do - but it is not the traditional expectation. Renaming an infrastructure team to "platform" without changing how it takes work in and how it is measured changes nothing; this is one of the most common ways platform initiatives stall.

**Team Topologies gives vocabulary for this.** A platform team provides capabilities in "X-as-a-Service" mode, reducing the cognitive load on stream-aligned teams. An infrastructure team that works through tickets is closer to a traditional shared-services function, which Team Topologies warns becomes a flow bottleneck.

**The trade-off.** Building self-service interfaces costs more up front than just doing the task when asked. For a rare, complicated request - a new cloud region, a direct-connect link - a ticket is the right interface, and automating it would be wasted effort. The judgement is to self-serve what is frequent and routine, and keep a human in the loop for what is rare and risky.

## Example

```text
The same request - "I need a PostgreSQL database for my new service" - handled two ways.

  INFRASTRUCTURE TEAM, ticket-driven
    day 0   product engineer raises INFRA-4821 with size, version, network
    day 2   ticket triaged; questions about backups and access
    day 4   database created; credentials sent in a password manager share
    day 5   engineer wires up connection, discovers no metrics dashboard
    cost to the infra team: ~2 hours per request, growing with every new service

  PLATFORM TEAM, self-service
    minute 0  engineer adds to their service file:
                database: { engine: postgres, size: small }
    minute 12 platform has created it with backups, alerts, a dashboard,
              and credentials injected as a secret the workload can read
    cost to the platform team: built once, ~0 per request

  Underneath BOTH, the same infrastructure: a managed database service in a
  cloud account the foundations team owns. The platform did not replace it -
  it made it consumable.
```

## Interview tips

- Start with the user and the interface: product engineers, reached through self-service rather than tickets. That distinction answers most of the question.
- Say that a platform usually sits on top of infrastructure rather than replacing it, and that in small organisations one team may hold both roles.
- Warn that renaming a team without changing its intake model and success metrics is a common failure.
- Give the trade-off: self-service is worth building for frequent, routine requests, not for rare, complex ones.
- Likely follow-ups: "how would you move an infrastructure team towards a platform model?" and "how would you measure the difference?" Related reading: [how platform engineering differs from DevOps and SRE](../platform-engineering-fundamentals/how-is-platform-engineering-different-from-devops-and-sre.md), [why self-service is the defining property of a platform](../platform-engineering-fundamentals/what-is-self-service-and-why-is-it-the-defining-property-of-a-platform.md), and [what Team Topologies says about platform teams](./what-does-team-topologies-say-about-platform-teams.md).

---

[⬅ Back to Platform Team and Operating Model](./README.md) · [All topics](../README.md)
