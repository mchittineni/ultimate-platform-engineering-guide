---
title: "What does Team Topologies say about platform teams?"
id: 123
category: "Platform Team and Operating Model"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-team-and-operating-model
  - interview-questions
---

# What does Team Topologies say about platform teams?

**Short answer:** It defines four team types - stream-aligned, platform, enabling, and complicated-subsystem - and three interaction modes, and it positions the platform team as existing to reduce the cognitive load on stream-aligned teams. The two ideas that matter most in practice are that the platform should be as thin as it can be while still doing that, and that the platform team's interaction with its consumers should be self-service rather than collaboration - because a platform whose normal mode is collaboration is a bottleneck.

## Detail

**The four team types:**

| Type                  | Purpose                                                                     |
| --------------------- | --------------------------------------------------------------------------- |
| Stream-aligned        | Owns a flow of change for a product or service; the default                 |
| Platform              | Provides internal services that reduce stream-aligned teams' cognitive load |
| Enabling              | Helps other teams gain capability, then leaves                              |
| Complicated-subsystem | Owns something requiring deep specialist knowledge                          |

Most teams should be stream-aligned. The other three exist to make that possible, which is a useful corrective to organisations that create many specialist teams and wonder why delivery is slow.

**The three interaction modes, and this is the more practically useful half:**

| Mode           | Meaning                                   | For a platform                 |
| -------------- | ----------------------------------------- | ------------------------------ |
| Collaboration  | Two teams working closely, high bandwidth | Temporary only                 |
| X-as-a-Service | One team consumes what another provides   | **The target steady state**    |
| Facilitating   | One team helps another improve            | During onboarding or migration |

The insight is that collaboration is expensive and should be time-boxed - useful while discovering what a capability should be, and a failure mode if it persists. If a platform team is permanently collaborating with its consumers, the capability is not actually self-service and the platform team's capacity limits everyone's delivery.

**Cognitive load is the stated design constraint,** and specifically the extraneous load a stream-aligned team should not have to carry. That gives you a test for any capability: does removing it increase what a product team must understand? If not, it is not pulling its weight.

**Thinnest viable platform.** The platform should be the smallest thing that reduces cognitive load - explicitly including the possibility that it is documentation and a template repository at this stage. This is the corrective to platform teams building for a much larger organisation than they have.

**Platform as an enabling relationship, not a ticket queue.** A platform team providing X-as-a-Service is not doing work on request; it is providing something teams use themselves. When work arrives as tickets, the team has become a service desk and the model has broken down - and the diagnostic question is whether the team ships interfaces or performs tasks.

**Conway's law, used deliberately.** The book's framing is that organisational structure and system architecture mirror each other, so you should design the team structure you want the architecture to reflect. For a platform, that means the platform's interface boundaries will end up matching the team boundaries - which is an argument for drawing the platform's API around what teams genuinely own.

**The honest caveat.** Team Topologies is a vocabulary and a set of heuristics, not a proof. It is genuinely useful for naming problems - "we are permanently in collaboration mode" is a much sharper diagnosis than "the platform team is overloaded" - and it does not tell you what to build. Being able to use it as a lens rather than as a doctrine is the right register.

## Example

```text
Interaction modes over the life of one capability - and the failure if it stalls.

  MONTH 0-2   COLLABORATION (deliberately temporary)
    the platform team works closely with two volunteer teams to discover what
    self-service database provisioning should look like. High bandwidth, lots of
    conversation, joint debugging.
    -> correct at this stage. The capability does not exist yet.

  MONTH 2-4   FACILITATING
    the capability exists. The platform team helps five more teams adopt it,
    fixing the rough edges each one finds. Still hands-on, but the direction is
    toward independence.

  MONTH 4+    X-AS-A-SERVICE  (the target steady state)
    teams declare a database and get one. No conversation required. The platform
    team's involvement is documentation, support for genuine defects, and the
    next capability.
    -> if this never arrives, the platform team's capacity limits everyone's
       delivery, permanently.

  THE FAILURE MODE, named precisely:
    still in COLLABORATION at month 12 - every database still needs a
    conversation with the platform team.
    -> the diagnosis is not "the platform team is overloaded". It is "the
       capability is not self-service", which points at a completely different
       fix. That precision is what the vocabulary buys you.
```

```text
Team types in one organisation - and note that most teams are stream-aligned.

  STREAM-ALIGNED (34 teams) - the default, and they should be the majority
    team-payments, team-search, team-web, team-data, ...
    each owns a flow of change end to end

  PLATFORM (1 team, 6 engineers)
    provides: golden paths, self-service infrastructure, delivery, observability,
              policy guardrails
    target interaction: X-as-a-Service
    measured on: whether stream-aligned teams' cognitive load went down

  ENABLING (1 team, 3 engineers, rotating)
    currently helping teams adopt tracing well; will move on when that is done
    NOT a permanent team - the whole point is that it leaves

  COMPLICATED-SUBSYSTEM (1 team, 4 engineers)
    the pricing engine - genuinely requires specialist domain knowledge
    justified because the knowledge cannot reasonably be spread

  The ratio matters. Four specialist teams and thirty-four stream-aligned teams
  is healthy. Twelve specialist teams and twenty stream-aligned teams would
  suggest capability has been centralised rather than enabled.
```

## Interview tips

- Name the four types and three modes, but spend your time on the modes - they are the more practically useful half and fewer candidates use them.
- "X-as-a-Service is the target steady state; collaboration is temporary" is the sentence to land, with the consequence: permanent collaboration means the platform team's capacity limits everyone.
- The precise diagnosis - "the capability is not self-service" rather than "the platform team is overloaded" - is a good illustration of what the vocabulary actually buys you.
- Cognitive load as the design constraint, with the removal test, connects this to how you would evaluate a capability.
- Thinnest viable platform, including the possibility that the platform is currently documentation, shows you understand the corrective the book is offering.
- Mention Conway's law being used deliberately: design the team structure you want the architecture to reflect.
- Close with the honest caveat that it is a vocabulary and a set of heuristics rather than a prescription. Treating it as doctrine is a weaker answer than treating it as a lens.

---

[⬅ Back to Platform Team and Operating Model](./README.md) · [All topics](../README.md)
