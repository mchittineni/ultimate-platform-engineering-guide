---
title: "How do you write an architecture decision record for a platform choice?"
id: 27
category: "Platform Architecture"
difficulty: "Beginner"
tags:
  - platform-engineering
  - platform-architecture
  - interview-questions
---

# How do you write an architecture decision record for a platform choice?

**Short answer:** An architecture decision record (ADR) is a short, dated, immutable document capturing one significant decision: the context and forces at play, the options considered, the choice made, and the consequences accepted. Write one when a decision is hard to reverse, would surprise someone without the context, and involved a real trade-off. Its value is not the decision - it is that in two years someone can tell whether the reasoning still holds.

## Detail

**The problem it solves.** Platform decisions have long half-lives and short memories. Two years on, nobody remembers why the platform uses Kustomize rather than Helm, whether the constraint that drove it still exists, or whether the option someone is now proposing was already rejected for a good reason. Without ADRs, teams either relitigate settled decisions endlessly or preserve them as unexplained tradition. Both are expensive.

**The structure, and what each section is really for:**

| Section          | Purpose                                                                        |
| ---------------- | ------------------------------------------------------------------------------ |
| Title and date   | Identifies the decision and pins it in time                                    |
| Status           | Proposed / Accepted / Superseded by ADR-NNNN                                   |
| Context          | The forces, constraints, and facts at the time - **the most valuable section** |
| Options          | What else was considered, and why each was rejected                            |
| Decision         | What was chosen, stated plainly                                                |
| Consequences     | What you accepted, including the bad parts                                     |
| Revisit criteria | What would make this decision wrong                                            |

**Context is the section that pays off.** It should include facts that will change: how many teams there were, what the team knew, what the budget was, what was already in place. A future reader's real question is "do those conditions still hold?" - and only a well-written context lets them answer it. "We had four engineers, none with Go experience, and 200 services already using Helm" is useful forever.

**Consequences must include the costs.** An ADR listing only benefits is marketing. Write down the thing you are accepting: the lock-in, the operational burden, the capability you are giving up. This is also what makes the record credible to the people who disagreed.

**Revisit criteria are the underused section.** "Revisit if we exceed 50 clusters, or if the upstream project is archived, or if we need multi-cloud." That single line converts a static document into something that can be triggered, and it is the field most ADR templates omit.

**They are immutable.** You do not edit an accepted ADR to reflect a new decision; you write a new one and mark the old superseded. The history of decisions is the point - an edited ADR loses exactly the information you were preserving.

**When not to write one.** Reversible decisions, obvious choices with no trade-off, and implementation details. If you can undo it in an afternoon and nobody would be surprised, it does not need a record. Teams that ADR everything produce a directory nobody reads, which is the same outcome as writing none.

## Example

```markdown
# ADR-0014: Use Crossplane for cloud resource provisioning, not Terraform modules

- **Status:** Accepted
- **Date:** 2026-03-11
- **Deciders:** platform team, staff engineer (infrastructure), security lead
- **Supersedes:** ADR-0006 (Terraform modules per service)

## Context

Facts as of March 2026 - the conditions a future reader should re-check:

- 41 stream-aligned teams, 218 services, one cloud provider (AWS), 4 accounts.
- Teams need databases, queues, and buckets self-service. Today they open a PR
  against `infra-modules`; median time to a provisioned database is 3.5 days,
  almost all of it waiting for platform review.
- 14 support tickets per month are "my Terraform plan is confusing".
- Terraform state is a single S3 backend with a lock table. Two incidents in six
  months from concurrent applies; blast radius is all resources in the workspace.
- Platform team is 5 engineers. Three are comfortable with Kubernetes controllers;
  none want to own an HCP Terraform-style runner fleet.
- Resources drift: 9% of database parameter groups differ from the module output,
  because manual console changes are never reconciled back.

## Options considered

1. **Terraform (or OpenTofu) modules + Atlantis-style PR automation.** Familiar, large ecosystem,
   and drift can be detected on a schedule. Rejected: run-to-completion means drift
   is corrected only when a plan runs, we still own a runner fleet, and state
   blast radius stays large.
2. **Terraform per service with separate state.** Fixes blast radius. Rejected:
   218 state files and a workspace-provisioning problem of its own.
3. **Crossplane with composite resources.** Continuous reconciliation, resources
   modelled as Kubernetes objects, RBAC and admission control we already run,
   and namespaced composite resources (Crossplane v2) give teams a small interface. Chosen.
4. **Cloud-native service catalogue (AWS Service Catalog).** Rejected: weaker
   interface design, ties the platform API to one provider.

## Decision

Provision cloud resources through Crossplane composite resources, exposed to teams
as namespaced composite resources (`PostgresInstance`, `Queue`, `Bucket`) - no separate claim objects, which Crossplane v2 no longer requires. Terraform is retained
only for account-level and bootstrap infrastructure that must exist before the
cluster does.

## Consequences

**Accepted costs:**

- Crossplane becomes critical platform infrastructure with its own upgrade and
  on-call burden. The management cluster's availability now affects provisioning.
- Provider coverage is thinner than Terraform's. Anything unsupported needs a
  provider contribution or a Terraform escape hatch, which we must document.
- The team must learn composition functions; this is a real ramp cost.
- Deletion semantics are dangerous by default. Requires `deletionPolicy: Orphan`
  on stateful resources plus admission policy - see ADR-0015.

**Benefits expected:** self-service provisioning in minutes; drift corrected
continuously; per-resource blast radius; one RBAC and policy model for compute and
infrastructure.

## Revisit criteria

Revisit this decision if any of these become true:

- We adopt a second cloud provider and provider coverage blocks us.
- Crossplane upstream stops being actively maintained.
- Provisioning-related incidents exceed 2 per quarter for two consecutive quarters.
- The platform team drops below 3 engineers comfortable with controllers.
```

## Interview tips

- Name context and consequences as the two sections that matter, and say why: context lets a future reader test whether the reasoning still holds.
- Putting numbers in the context - team count, ticket volume, incident count - is what separates a useful ADR from a rationalisation. Show that in your example.
- Revisit criteria are a strong differentiator; most candidates do not mention them and they are what make a decision reviewable rather than permanent.
- Say ADRs are immutable and superseded rather than edited. It is a small point that signals you have maintained a real set.
- Volunteer when _not_ to write one. Interviewers are wary of process enthusiasm without judgement.

---

[⬅ Back to Platform Architecture](./README.md) · [All topics](../README.md)
