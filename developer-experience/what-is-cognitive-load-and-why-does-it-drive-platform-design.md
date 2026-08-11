---
title: "What is cognitive load and why does it drive platform design?"
id: 10
category: "Developer Experience"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - developer-experience
  - interview-questions
---

# What is cognitive load and why does it drive platform design?

**Short answer:** Cognitive load is the total amount a team must hold in their heads to do their work. Team Topologies argues it is the real constraint on team effectiveness, and that a platform's job is to remove the kind of load that is incidental to the team's mission. It drives platform design because it gives you a test for every capability: does this reduce what a product team must understand, or does it just move the complexity somewhere they still have to look at it?

## Detail

**The three kinds, and only one is worth removing.** The distinction comes from cognitive load theory and is what makes the concept usable:

| Type       | In this context                                                                | What to do                              |
| ---------- | ------------------------------------------------------------------------------ | --------------------------------------- |
| Intrinsic  | The inherent difficulty of the domain - how payments settlement works          | Train and hire for it; cannot remove    |
| Extraneous | Incidental mechanics - how to write a Helm chart, how IRSA trust policies work | Remove it; this is the platform's job   |
| Germane    | Effort spent building useful models - the business domain, the architecture    | Protect it; this is what you want spent |

A platform that removes extraneous load frees capacity for germane load. A platform that adds a large bespoke abstraction with its own quirks has converted one kind of extraneous load into another, and gained nothing.

**Why it is the constraint rather than skill or effort.** A team of six cannot be expert in payments logic, Kubernetes networking, Terraform state, IAM policy evaluation, Prometheus query semantics, and their cloud provider's quota model. Asking them to be produces shallow competence everywhere, which is how you get services with no alerts and IAM policies with wildcards. The load is not reduced by working harder; it has to be absorbed by something.

**The design tests it gives you:**

- **The removal test.** If this capability disappeared, what would each team have to learn? If the answer is "nothing", the capability is not pulling weight.
- **The concept count test.** How many new concepts does a developer need in order to use this? Three is a good interface. Fifteen means you built a second Kubernetes.
- **The failure test.** When it breaks, does the developer need to understand the implementation to diagnose it? If yes, you hid the complexity from the happy path only - which is where most platform abstractions actually fail.

**Where load hides.** Not just in tooling. It hides in the number of repositories a change must touch, the number of systems to check during an incident, the number of approvals, the number of ways to do the same thing, and the amount of tribal knowledge with no written home. Cutting three ways of deploying down to one reduces load even if no code changes.

**The counter-argument to have ready.** Hiding too much creates a different problem: engineers who cannot debug production because they have never seen the layer underneath. The resolution is that abstractions should be escapable and inspectable - the generated manifests are visible, the platform explains what it did - so the default is simple but the mechanism is learnable.

## Example

```text
The same requirement - "this service needs a Postgres database" - by load.

High extraneous load (no platform)
  A developer must understand, correctly, first time:
    subnet groups, parameter groups, engine version policy, storage autoscaling,
    backup windows vs maintenance windows, PITR, multi-AZ failover semantics,
    connection limits vs pooling, secret rotation, credential delivery to pods,
    monitoring for replication lag, cost implications of instance class
  ~12 concepts, none of them about the product. Every team learns them separately,
  most learn a subset, and the gaps show up as incidents.

Low extraneous load (platform capability)
  dependencies:
    - postgres: { size: small, backups: daily, pitr: true }

  3 concepts: size, backup cadence, point-in-time recovery. The platform owns the
  other 9, applies them consistently, and can improve them for everyone at once.

Still low load when it breaks - the escape hatch keeps it learnable:
  $ platform explain postgres checkout
    -> shows the generated Terraform / CRD, the chosen instance class and why,
       the secret path, the dashboards, and the runbook link
  The developer can see the mechanism when they need to, and ignore it when they
  do not. That is the difference between an abstraction and a black box.
```

## Interview tips

- Distinguishing extraneous from intrinsic and germane load is the whole answer. Candidates who say only "platforms reduce cognitive load" have quoted the phrase without the content.
- Attribute it to Team Topologies, and note that the three-type split comes from cognitive load theory - it shows the concept is understood rather than borrowed.
- Give a concrete concept count. "Twelve things to understand, reduced to three" is far more persuasive than "simpler".
- Volunteer the counter-argument about engineers losing the ability to debug, and resolve it with escapable, inspectable abstractions. Interviewers probe for this.
- Mentioning that load hides in process - repositories touched, approvals, number of ways to do one thing - shows breadth beyond tooling.

---

[⬅ Back to Developer Experience](./README.md) · [All topics](../README.md)
