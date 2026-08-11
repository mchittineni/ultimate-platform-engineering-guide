---
title: "What are the most common ways platform initiatives fail?"
id: 8
category: "Platform Engineering Fundamentals"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-engineering-fundamentals
  - interview-questions
---

# What are the most common ways platform initiatives fail?

**Short answer:** Platforms fail far more often for organisational reasons than technical ones - built without users, mandated instead of adopted, staffed as a renamed operations team, or measured by components shipped rather than developer outcomes. The technical failure that matters most is the leak-proof abstraction, which turns the platform team into exactly the bottleneck it was created to remove.

## Detail

**Built without users.** The team designs from first principles, ships a control plane after two quarters, and discovers the actual pain was a slow test suite and unclear database defaults. The tell is a backlog with no evidence attached to its items.

**Mandated rather than adopted.** Leadership decrees the platform is compulsory. Teams comply on paper, then build shadow tooling around it - a wrapper script, a second pipeline, a "temporary" cluster. You now support both, and you have no honest signal about what is wrong because complaints arrive as escalations rather than as usage data.

**The service desk with a new name.** The operations team is renamed, but work still arrives as tickets and capabilities are still delivered by humans. Throughput becomes the metric, which rewards handling more tickets rather than eliminating their cause. The diagnostic question: does the team ship interfaces, or perform tasks?

**Leak-proof abstractions.** The platform hides Kubernetes entirely and exposes fifteen fields. It works beautifully until a workload needs a sidecar, a node affinity rule, or a custom probe - and then the only route is a ticket to the platform team, who become the bottleneck. Abstractions must be escapable: let a senior engineer see and override the generated output.

**No migration support for breaking changes.** The platform ships v2 of its interface and asks forty teams to migrate. Half do not, you support both indefinitely, and trust is gone. The platform team's job is to raise the pull requests itself.

**Staffed too thin.** One or two engineers cannot build a product and run critical infrastructure and provide support. What emerges is an overloaded pair, undocumented systems, and a severe bus-factor problem.

**Success measured as output.** Dashboards counting clusters managed, resources provisioned, and tickets closed. None of these tell you whether engineers ship faster or more safely, so the platform cannot tell whether it is working - and neither can the finance conversation that funds it.

**Platform reliability treated as an afterthought.** Once everyone deploys through you, your outage is everyone's outage, and your maintenance window is the whole organisation's. Platforms that skip their own SLOs, degradation design, and disaster recovery lose credibility in a single bad week.

**Ignoring the cost of the platform itself.** Control planes, observability pipelines, idle preview environments, and shared clusters accumulate real spend. A platform that cannot attribute or defend its own cost gets cut in the first budget round.

## Example

```text
A recognisable eighteen-month failure, and the intervention at each point.

Q1  Team formed from the ops team. Mandate announced. Ticket queue continues.
    -> Intervention: pick one workload shape, ship one golden path end to end.

Q2  Portal built first, because it demos well. No provisioning behind it.
    -> Intervention: provisioning before presentation; Git as the interface is fine.

Q3  Mandate enforced via admission policy. Two teams build wrapper scripts.
    -> Intervention: treat the wrappers as a bug report. Ask what the path is missing.

Q4  Interface v2 ships; 40 teams asked to migrate. 18 do.
    -> Intervention: bot-raised migration PRs, run the codemod yourself, keep v1
       until consumers are at zero - then delete it.

Q5  Control plane outage blocks all deploys for 4 hours. No SLO, no runbook.
    -> Intervention: platform SLOs, degraded-mode design, break-glass path.

Q6  Review: "what did we get?" Metrics show 12 clusters and 4,000 resources.
    Nobody can say whether lead time improved. Budget cut; team dissolved.
    -> Intervention that was needed in Q1: baseline lead time and onboarding time
       on day one, so the value story exists before it is demanded.
```

## Interview tips

- Lead with the organisational failures. Interviewers hear technical answers constantly and are usually probing whether you understand that platforms fail socially.
- Have one failure you personally saw or contributed to, with what you would do differently. This question is often a disguised "tell me about a failure".
- "Abstractions must be escapable" and "measure outcomes, not components" are the two sentences to land.
- The strongest close is that you would baseline lead time and onboarding time before writing any code, so the value conversation has evidence when it arrives.

---

[⬅ Back to Platform Engineering Fundamentals](./README.md) · [All topics](../README.md)
