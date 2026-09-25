---
title: "How do you answer a platform design interview question?"
id: 260
category: "Platform Engineering Interviews"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-engineering-interviews
  - interview-questions
---

# How do you answer a platform design interview question?

**Short answer:** Establish the users and constraints, design the developer-facing interface before any component, then work backwards to the implementation - and volunteer the trade-offs, the failure modes, and what you would deliberately not build. The mistake that costs most candidates the round is drawing an architecture diagram of tools when the question was about an interface other engineers have to live with.

## Detail

**Spend the first five minutes on users and constraints.** How many teams, what workload shapes, what they do today, what hurts, what the team's size is, what the compliance requirements are, and what is already in place. A candidate who designs without asking produces something generic; a candidate who asks produces something that fits, and the asking is itself part of what is being assessed.

**Design the interface first, and say why.** What does a developer write? Twenty lines of declarative specification, and here is what each field means and why it is there. That is the product. The components behind it are implementation detail you should be free to replace, and stating that explicitly is a strong signal.

**Then work backwards.** From the interface, derive what must exist: something to accept and validate the declaration, something to reconcile it, something to hold credentials, something to enforce policy, something to make the result observable. That order - interface, then mechanism - is the opposite of how most candidates proceed and it is what distinguishes a platform answer from an infrastructure answer.

**Volunteer the trade-offs.** Every design choice has a cost, and naming it before you are asked is the most reliable way to sound senior. Reconciliation versus a reviewable plan. Namespace versus cluster isolation. Build versus buy. A candidate who presents a design as obviously correct invites the interviewer to find the hole; a candidate who names the holes has already demonstrated the judgement being tested.

**Cover the four things that are almost always probed:**

| Probe               | What a good answer includes                                     |
| ------------------- | --------------------------------------------------------------- |
| Escape hatch        | The interface is escapable; overrides are recorded and reviewed |
| Versioning          | The interface is a contract; you migrate consumers yourself     |
| Failure behaviour   | Control-plane failure stops change, not serving                 |
| Deletion and safety | Orphan stateful resources; deletion needs explicit intent       |

The deletion hazard in particular is a strong volunteer: saying "and I would set the deletion policy to orphan, because otherwise deleting a namespace destroys a production database" is memorable and demonstrably experience-derived.

**Say what you would not build.** No portal in the first six months. No service mesh without a named requirement. No abstraction over multiple clouds. Scoping down is what senior candidates do and what junior candidates find counter-intuitive, and it also shows you would not spend the team's quarter on something interesting.

**State how you would know it worked.** Adoption, lead time, time to create a service, support question volume. A design with no success measure is an architecture; a design with one is a product.

**Think out loud, and manage the time.** Unspoken reasoning scores nothing. Narrate the decision, name the alternative you rejected, and say why. And watch the clock: a design round that spends forty minutes on the provisioning mechanism and never reaches observability, security, or adoption has left most of the assessment unaddressed.

**Handle scope changes gracefully.** Interviewers commonly add a constraint mid-round - "now it has to work on two clouds", "now there is a compliance requirement". They are testing whether your design bends or breaks. If you designed the interface first, it usually bends, and you can say so.

## Example

```text
"Design a capability that lets 40 teams provision databases themselves."

  MINUTES 0-5  USERS AND CONSTRAINTS - ask, do not assume
    how many teams, what do they do today, how long does it take now?
    what hurts - the wait, the inconsistency, or the cost?
    one cloud or more? regulated data? existing Kubernetes?
    how big is the platform team? (this bounds what is buildable)
    -> "40 teams, 3.5 days median wait, all AWS, PCI scope for one team,
        Kubernetes already, 5 platform engineers."

  MINUTES 5-15  THE INTERFACE FIRST - this is the product
    "Here is what a developer writes:"

      kind: PostgresInstance
      spec:
        size: small          # small|medium|large - not instance classes
        backups: daily
        pitr: true
        writeConnectionSecretToRef: { name: checkout-db-conn }

    "Four fields. Note what is ABSENT: no encryption toggle, no subnet, no
     public-access flag, no tags. Those are applied unconditionally, so a
     non-compliant database is not expressible. That is a stronger control than
     a policy that rejects one."
    "And the test for this interface: could I move to Cloud SQL without changing
     a single service's spec? Yes - nothing here is AWS-specific."

  MINUTES 15-30  WORK BACKWARDS TO THE MECHANISM
    accept + validate ...... CRD with schema validation and CEL cross-field rules
    authorise .............. Kubernetes RBAC on namespaced resources
    reconcile .............. Crossplane v2 composition of a namespaced composite
                             resource - no separate claim needed (drift
                             corrected, no state file)
                             -> TRADE-OFF, volunteered: no first-class plan, so
                                previewing a change is harder than with Terraform.
                                Mitigate with staging plus admission policy on
                                dangerous fields.
    credentials ............ controller holds the AWS role via EKS Pod Identity
                             (IRSA remains supported); teams get
                             ZERO AWS permissions
    policy ................. admission for the rules the schema cannot express
                             (size: large needs budget approval)
    observability .......... dashboards, connection metrics, and cost tags
                             generated from the resource

  MINUTES 30-45  THE FOUR PROBES, VOLUNTEERED NOT EXTRACTED
    deletion  "orphan on delete for anything stateful (managementPolicies
               without Delete in Crossplane v2), plus admission
               rejecting deletion of production databases without an explicit
               annotation. Otherwise deleting a namespace destroys a production
               database - which is the sharpest edge of this whole design."
    escape    "Terraform escape in the team's own boundary for anything the five
               supported resources cannot serve, recorded as an exception with a
               review date. And I track those - four teams needing the same
               unsupported resource is my next roadmap item."
    versioning "the CRD is a contract 40 repos will encode. Two served versions
               with a conversion webhook, and I raise the migration PRs myself.
               Breaking 40 teams once costs a year of trust."
    failure    "controller down means no NEW databases; existing ones are
               unaffected. Control-plane failure stops change, not serving."

  MINUTES 45-55  WHAT I WOULD NOT BUILD, AND HOW I WOULD KNOW IT WORKED
    not building: a portal (Git plus a CLI is enough at this scale); an
    abstraction over multiple clouds (no requirement named); support for every
    AWS resource (five cover ~94% of requests).
    success: median time to a database 3.5 days -> under 10 minutes; voluntary
    adoption; the 14 monthly support tickets in this category going to near zero.

  MINUTES 55-60  SCOPE CHANGE, if it comes
    "now you need this on Azure too" -> the interface does not change at all; a
    second composition targets Azure. That is exactly why the interface came
    first. What I would NOT do is abstract the two behind a lowest-common-
    denominator layer.
```

## Interview tips

- Ask about users and constraints for the first five minutes. It is not a delay - the asking is part of the assessment, and it is what stops the design being generic.
- Design the interface before any component, and say out loud that the components are implementation detail. That single move most distinguishes a platform answer from an infrastructure answer.
- The swap test - could you change cloud provider without editing a service specification - is a compact way to prove your interface does not leak.
- Volunteer the four probes: escape hatch, versioning, failure behaviour, and deletion safety. The deletion hazard is the most memorable and most clearly experience-derived.
- Name a trade-off for every significant choice, before being asked. Presenting a design as obviously correct invites the interviewer to find the hole.
- Say what you would not build, and give reasons. Scoping down reads as senior; wanting to build everything reads as junior.
- State a success measure, manage the clock so you reach security, observability, and adoption, and think out loud throughout - unspoken reasoning scores nothing.

---

[⬅ Back to Platform Engineering Interviews](./README.md) · [All topics](../README.md)
