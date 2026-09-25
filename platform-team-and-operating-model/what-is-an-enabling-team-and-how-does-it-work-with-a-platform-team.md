---
title: "What is an enabling team and how does it work with a platform team?"
id: 240
category: "Platform Team and Operating Model"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-team-and-operating-model
  - interview-questions
---

# What is an enabling team and how does it work with a platform team?

**Short answer:** An enabling team is a small group of specialists who help other teams learn a capability - testing, observability, security practices, a new delivery model - and then move on. It is one of the four team types in Team Topologies, and it works in "facilitating" mode: it coaches, pairs, and removes blockers, but does not do the work permanently. With a platform team, the usual split is that the platform builds the self-service capability and the enabling team helps product teams adopt it well, feeding back what gets in their way.

## Detail

**The defining property is that it leaves.** An enabling team succeeds when the team it helped no longer needs it. If a product team still depends on the enabling team six months later for the same thing, the help has turned into a permanent service, and that is a different team type with different problems.

**What it looks like day to day.** Two or three engineers with depth in a topic join a stream-aligned team for a few weeks. They pair on real work, run a short workshop, write down the patterns that worked, and hand over. Then they pick the next team. Typical topics are OpenTelemetry tracing, writing useful SLOs, test automation, container security, or moving to a new deployment model.

**How it differs from a platform team:**

| Aspect           | Platform team                           | Enabling team                                |
| ---------------- | --------------------------------------- | -------------------------------------------- |
| Output           | A self-service product others consume   | Capability inside other teams                |
| Interaction mode | X-as-a-Service (steady state)           | Facilitating (time-boxed)                    |
| Lifetime of work | Long-lived; the platform is maintained  | Short engagements; moves on                  |
| Success measure  | Adoption, outcomes, satisfaction        | Team can do it unaided; engagement ends      |
| Scales by        | Better interfaces and more self-service | Leaving behind docs, patterns, and champions |

**Why a platform team needs one, or needs to behave like one sometimes.** A golden path removes most of the effort, but not all the understanding. A team can adopt generated dashboards and still not know how to read a trace during an incident. Building more platform features does not fix that; teaching does. Without an enabling function, the platform team either gets pulled into endless one-to-one support or watches adoption plateau.

**The feedback loop is the valuable part.** An enabling team sits inside product teams and sees exactly where the platform is awkward - the default that does not fit, the doc that is wrong, the step that nobody understands. That is some of the best roadmap evidence a platform can get, provided there is a regular channel to pass it back.

**Common setups.** In a large organisation, a separate enabling team (for example, a developer productivity or reliability coaching group). In a smaller one, platform engineers rotate into an enabling role for a quarter, which also builds empathy for their users. Both work; the rotation model is cheaper but easier to let slide into "the platform team does support".

**Trade-offs and failure modes.** An enabling team that does the work instead of teaching creates dependency. One with no end date on its engagements becomes an unofficial second platform team. And one with no connection to the platform team teaches workarounds for problems the platform should have fixed. Time-box each engagement, define the exit condition up front, and route the findings to the platform backlog.

## Example

```text
An enabling engagement to help teams adopt the platform's tracing capability.

  CONTEXT
    platform team shipped auto-instrumented tracing via the golden path.
    adoption of the capability: 80% of services emit traces.
    actual use during incidents: almost none. Teams still grep logs.

  ENGAGEMENT - enabling team (3 engineers), 4 weeks per product team
    week 1   pair with team-payments during their on-call rotation
    week 2   run a 90-minute session on reading traces from their own services
    week 3   team adds custom spans to the two flows that matter most
    week 4   hand-over: runbook updated to start from a trace, not a log search
    exit condition (agreed on day 1): team resolves one incident using traces
                                     without the enabling team present

  FEEDBACK TO THE PLATFORM TEAM (fortnightly)
    - trace sampling default drops the slow requests teams care about -> fix it
    - trace links missing from alert notifications -> add them to the template
    - two teams confused by the span naming convention -> doc rewritten

  RESULT after 5 teams
    enabling team moves on; tracing used as first step in 70% of incidents
    for those teams. The platform fixed 3 defaults it would not have found.
```

## Interview tips

- Define it by its exit: an enabling team succeeds when it is no longer needed.
- Tie it to Team Topologies - one of four team types, working in facilitating mode - and contrast that with the platform team's X-as-a-Service mode.
- Explain the partnership: platform builds the capability, enabling team helps teams use it well, and feeds back the friction.
- Name the users on both sides: product engineers are helped, and the platform team is a consumer of the enabling team's findings.
- Mention failure modes: doing the work instead of teaching, and engagements with no end date.
- Likely follow-up: "how would you know an engagement worked?" Answer with an exit condition agreed on day one. Related: [what Team Topologies says about platform teams](./what-does-team-topologies-say-about-platform-teams.md) and [how to migrate teams without a mandate](./how-do-you-migrate-teams-onto-the-platform-without-a-mandate.md).

---

[⬅ Back to Platform Team and Operating Model](./README.md) · [All topics](../README.md)
