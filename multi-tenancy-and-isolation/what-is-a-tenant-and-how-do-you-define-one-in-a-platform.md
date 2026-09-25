---
title: "What is a tenant, and how do you define one in a platform?"
id: 41
category: "Multi-Tenancy and Isolation"
difficulty: "Beginner"
tags:
  - platform-engineering
  - multi-tenancy-and-isolation
  - interview-questions
---

# What is a tenant, and how do you define one in a platform?

**Short answer:** A tenant is the unit of ownership and isolation on the platform - the group that owns a set of workloads, is accountable for them, and is kept apart from other groups. In an internal platform that is usually a team, not a person and not a single service. You define a tenant explicitly, as a record with an owner, a tier, and limits, so that everything the platform creates for it can be derived from and traced back to that one definition.

## Detail

**A tenant answers "whose is this?"** Every resource on a shared platform - a namespace, a database, a DNS record, a cloud bill - must have an answer to that question. The tenant is that answer. It is the thing that gets access, gets quota, gets paged when something breaks, and gets the cost report.

**Choosing the granularity is the real design decision.** There are three common choices, and each has a clear failure mode:

| Tenant is a... | Works well when                            | Goes wrong when                                    |
| -------------- | ------------------------------------------ | -------------------------------------------------- |
| Service        | Services are large and independently owned | Hundreds of tiny tenants; quota and RBAC sprawl    |
| Team           | Teams own several services together        | Team reorganisations force re-tenanting            |
| Business unit  | Chargeback is the main concern             | Too coarse; one unit's teams can affect each other |

Most platforms pick the team as the tenant and give each tenant one namespace per service or per environment underneath. That keeps accountability at the level where on-call and budgets actually live, while still letting individual services have their own quotas and network rules.

**A tenant is more than a namespace.** It is tempting to say "a tenant is a namespace", but a namespace is only one of the things a tenant owns. The same tenant usually also has cloud IAM roles, secret store paths, a budget, alert routing, repository permissions, and a catalogue entry. If the tenant exists only as a naming convention on namespaces, there is nowhere to hang those other things, and they drift.

**What a good tenant definition contains:**

- **A stable identifier** that is safe to use in names and labels, such as `team-search`.
- **An owner**, preferably an identity provider group rather than individual people, so ownership survives staff changes.
- **A tier or criticality**, which drives defaults such as priority classes, backup policy, and alerting.
- **Limits** - quota and budget - so fairness is declared, not negotiated per incident.
- **Contacts** for on-call and communication.
- **A data classification**, because it decides which clusters and controls the tenant is allowed to use.

**Define it once, in one place.** The strong pattern is to make the tenant a declared object - often a custom resource or an entry in the developer portal's catalogue - and have automation derive the namespaces, roles, quotas, and policies from it. The weak pattern is a wiki page and a runbook. The declared version lets the platform answer "which tenants lack a budget?" with a query, and makes offboarding possible later.

**Who the user is.** The team leads and engineers who make up the tenant. A clear tenant definition means they know exactly what they own and what limits apply, and a new team member inherits access through group membership rather than by filing tickets. For the platform team, it is the key used by every other capability: cost reporting, policy, access, and support.

**The trade-off.** A precise, enforced tenant model adds some friction at creation time and must be kept in step with reorganisations. The alternative - implicit tenancy by naming convention - is frictionless until the first cost dispute, security review, or team deletion, when nobody can say what belonged to whom.

## Example

```yaml
# A tenant declared as a platform custom resource. Namespaces, RBAC, quotas,
# network policy, and cost tags are all derived from this one object.
apiVersion: platform.example.com/v1
kind: Tenant
metadata:
  name: team-search
  labels:
    platform.example.com/tier: "2"
spec:
  owner: group:team-search # identity provider group, not named people
  costCentre: eng-discovery
  tier: 2
  dataClassification: internal # decides which clusters it may use
  quota:
    cpu: "40"
    memory: 80Gi
    pods: 200
  environments: [dev, staging, prod]
  contacts:
    oncall: pagerduty:team-search
    chat: "#team-search"
```

```text
What that one definition becomes in the prod cluster:

  Namespace  search-api-prod      labels: tenant=team-search, tier=2
  Namespace  search-index-prod    labels: tenant=team-search, tier=2
  RoleBinding  group team-search -> edit   (in both namespaces only)
  ResourceQuota                            (split from spec.quota)
  NetworkPolicy default-deny + baseline allows
  Cost report  rows grouped by label tenant=team-search
```

## Interview tips

- Lead with "a tenant is the unit of ownership and isolation", then say that on internal platforms it is usually a team.
- Talk about granularity as a trade-off. Explaining why "service" and "business unit" are both awkward choices shows judgement.
- Say explicitly that a tenant is more than a namespace, and list the other things it owns: identity, secrets, budget, alerts.
- Mention owners as groups, not people. It is a small detail that interviewers notice because it is what keeps ownership accurate over time.
- If asked how it is implemented, describe a declared object reconciled by a controller; the full lifecycle is covered in [How do you design tenant onboarding and offboarding?](./how-do-you-design-tenant-onboarding-and-offboarding.md).

---

[⬅ Back to Multi-Tenancy and Isolation](./README.md) · [All topics](../README.md)
