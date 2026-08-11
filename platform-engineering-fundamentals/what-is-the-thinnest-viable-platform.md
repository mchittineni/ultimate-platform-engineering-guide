---
title: "What is the thinnest viable platform?"
id: 5
category: "Platform Engineering Fundamentals"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-engineering-fundamentals
  - interview-questions
---

# What is the thinnest viable platform?

**Short answer:** The thinnest viable platform is the smallest set of things you can offer that genuinely reduces the cognitive load on your stream-aligned teams - and nothing more. The term comes from Team Topologies, and its point is that a platform is defined by the outcome it produces, not by how much of it you built. A well-maintained template repository plus a good pipeline and a page of documentation can be a complete platform for a ten-person engineering organisation.

## Detail

**Why the concept matters.** The default failure mode of a platform team is to build the platform they would want at a company ten times the size: a portal, a control plane, custom resource definitions, a service mesh, an internal CLI. That work is real and expensive, and if the teams it serves needed a working pipeline and clear database defaults, none of it helped. Thinnest viable platform is the discipline of asking, for each capability, whether removing it would increase anyone's cognitive load.

**Thin does not mean low quality.** The parts you do ship must be reliable, documented, and supported. A thin platform with one excellent golden path beats a broad platform where five capabilities are half-finished, because a capability that cannot be trusted still has to be understood - which is the cost you were trying to remove.

**A platform can be documentation.** Team Topologies makes this point deliberately: if the thing that removes cognitive load is a well-written, maintained decision guide - "here is how we choose a datastore, here are the three approved options and their defaults" - then that document is the platform for now. Most organisations skip this stage and regret it.

**How platforms usually should grow:**

| Stage      | Typical shape                                                               | Trigger to move on                              |
| ---------- | --------------------------------------------------------------------------- | ----------------------------------------------- |
| Documented | Decision guides, conventions, a reference repository                        | People follow it but copy-paste drifts          |
| Templated  | Scaffolding template, shared pipeline definition, shared modules            | Updating the template does not update consumers |
| Automated  | Reconciled provisioning, self-service environments, generated observability | Interface churn breaks teams                    |
| Abstracted | A versioned platform API, portal, catalogue, scorecards                     | -                                               |

**How you decide what to build next.** Look at where the time and the incidents actually go: onboarding time for a new service, the questions repeated in the support channel, the steps every team does by hand, the post-incident findings that name a missing default. That evidence is what justifies a capability. "It would be nice to have a portal" is not evidence.

**The counter-pressure to name.** Thin platforms can become an excuse for never investing, leaving teams with a wiki page and no automation. The test is not size, it is whether cognitive load is measurably going down.

## Example

```text
Ten engineers, three services, one cloud account.

Thinnest viable platform (a week of work, sufficient for a year):
  - one template repository: Dockerfile, healthcheck, structured logging, CI config
  - one reusable pipeline definition consumed by every repo
  - one Terraform module per resource type teams actually need (db, queue, bucket)
  - one dashboard template + one alerting rule set applied per service
  - one page: "how to add a service", "how to get a database", "who to page"

Not yet justified at this size:
  - a portal (three services fit in your head; a catalogue solves nothing)
  - custom resource definitions and a control plane (no scale of repetition yet)
  - a service mesh (mTLS between three services is cheaper another way)
  - a dedicated platform team (this is one engineer's 20% time)

The trigger to invest further is repetition, not ambition: when the same manual
step is done for the eighth time, automate that step - not the whole platform.
```

## Interview tips

- Attribute the idea to Team Topologies if you can; it shows you know the source of the vocabulary you are using.
- The strongest version of this answer includes "a platform can legitimately be documentation right now" - it demonstrates you optimise for outcome over artefact.
- Have the growth stages ready, and tie each transition to a concrete trigger. Vague maturity models are unconvincing; triggers are not.
- Expect the mirror question - "when has a platform become too thin?" - and answer it with evidence: onboarding time, repeated support questions, and incidents caused by missing defaults.

---

[⬅ Back to Platform Engineering Fundamentals](./README.md) · [All topics](../README.md)
