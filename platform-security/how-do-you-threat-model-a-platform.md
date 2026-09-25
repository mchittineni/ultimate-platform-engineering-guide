---
title: "How do you threat model a platform?"
id: 132
category: "Platform Security"
difficulty: "Advanced"
tags:
  - platform-engineering
  - platform-security
  - interview-questions
---

# How do you threat model a platform?

**Short answer:** Model the platform as what it is - a system with privileged, cross-tenant reach that every team depends on - and work through the boundaries in order: tenant to tenant, tenant to platform, supply chain to production, and platform operator to everything. The distinctive threat is that the platform's own automation is the most privileged actor in the estate, so a compromise of the control plane or the pipeline is a compromise of every service at once.

## Detail

**Why a platform threat model differs from an application one.** An application's threat model concerns its own data and users. A platform's concerns everyone else's: it can create infrastructure, read secrets, mutate workloads, and deploy code across every tenant. Its controllers hold the broadest credentials in the organisation, and its pipeline can put code into production. Those two facts dominate the analysis.

**Work the boundaries rather than the components.** Components produce a list of technologies; boundaries produce a list of attack paths.

| Boundary                    | Representative threat                                                                                                 |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Tenant → tenant             | Assuming another tenant's cloud role; reading their secrets; exhausting shared capacity                               |
| Tenant → platform           | Escalating via an over-broad controller; crafting a resource that makes the controller act privileged on their behalf |
| Supply chain → production   | Compromised dependency or build; unsigned image admitted                                                              |
| CI → production             | A fork pull request obtaining deploy credentials                                                                      |
| Control plane → everything  | Compromised controller credential; malicious admission webhook                                                        |
| Operator → everything       | Insider or compromised laptop with standing privileged access                                                         |
| External → platform surface | Exposed preview environment, portal, or dashboard                                                                     |
| Agent → platform            | A prompt-injected AI coding agent or MCP server acting with a developer's or pipeline's credentials                   |

**The confused-deputy problem is the distinctive platform threat.** A controller acts on behalf of users with far more privilege than any of them. If a tenant can submit a resource that causes the controller to do something on their behalf that they could not do directly - reference a secret in another namespace, target a resource outside their scope, template a value into a privileged field - they have escalated through your automation. Validating that every referenced object is within the requester's own scope is the control, and it is easy to omit.

**Enumerate the standing privileges honestly.** List every identity with broad reach - controller service accounts, CI roles, operator break-glass, the reconciler - and for each ask what a compromise achieves and what would detect it. This exercise usually finds at least one credential that is far broader than anyone remembered.

**Model your own tooling as an attack surface.** An admission webhook that can mutate any Pod is a code-execution vector into every workload. A portal that renders user-supplied templates can be abused. A controller that fetches a URL from a resource spec is a server-side request forgery primitive pointed at your metadata endpoint. Platform teams routinely threat model tenant workloads and never their own controllers.

**Treat AI agents as a new class of tenant.** Coding assistants and agents now call platform APIs, open pull requests, and use MCP servers that expose platform capabilities. Each is an identity acting on untrusted input, so give it its own scoped, short-lived credentials rather than a borrowed human token, keep destructive operations behind the same approvals a human would face, and log its actions as its own.

**Include availability, because for a platform it is a security property.** A tenant able to exhaust the API server, fill etcd, or trigger unbounded reconciliation denies service to every other tenant. Fail-closed admission webhooks are self-inflicted versions of the same thing.

**Prioritise by what a control actually removes.** Some findings are cheap to fix and remove a whole class - narrowing a trust policy condition, adding admission verification, scoping a controller's role by tag. Others are expensive and reduce one path. Rank by class elimination, not by severity score.

**Make it repeatable and tied to change.** Threat model each new platform capability at design time using the same boundary list, and re-run the whole model when the tenancy model changes. A one-off document written by a consultant is a snapshot; the boundary list embedded in your design review is a practice.

## Example

```text
Boundary walk for one platform, with the finding and the control that removes
the largest class in each case.

TENANT -> TENANT
  threat  assume another tenant's cloud role
  finding one trust policy uses a wildcard subject
  control pin exact subject + audience; automated audit for wildcards
          -> removes the entire cross-tenant escalation class, cheaply

  threat  read another tenant's secrets
  finding secret store policy grants read on secret/* to all workloads
  control per-tenant path scoping enforced at policy generation

  threat  exhaust shared capacity
  control ResourceQuota incl. object counts + API priority and fairness +
          PriorityClass by tier

TENANT -> PLATFORM  (the confused deputy - the distinctive platform threat)
  threat  a claim referencing a secret in another namespace, which the
          controller - not the tenant - has permission to read
  finding the provisioning controller resolved secretRef without checking that
          the referenced namespace matched the claim's namespace
  control admission validation: every cross-object reference must be within the
          requester's own scope. This is the highest-value finding in the model.

  threat  a value from a tenant spec templated into a privileged field
  control allowlist and type-constrain everything templated; never interpolate
          tenant strings into RBAC, node selectors, or image references

SUPPLY CHAIN -> PRODUCTION
  threat  unsigned or externally-built image runs
  control admission verification of signature AND provenance (repo, ref, builder)

  threat  fork pull request obtains deploy credentials
  control privileged jobs only from trusted refs; trust policy pinned to
          environment, not to the organisation

CONTROL PLANE -> EVERYTHING
  threat  compromised provisioning controller credential
  finding controller IAM role unbounded by region or tag
  control bound by resource prefix + tag condition + region; separate provider
          config per environment; alert on use outside expected patterns

  threat  malicious or compromised mutating webhook injects a sidecar everywhere
  control webhook image signed and pinned by digest; narrow match rules;
          its own changes reviewed as production changes

OPERATOR -> EVERYTHING
  threat  standing privileged access, or a compromised operator laptop
  control no standing access; time-bound break-glass, recorded and reviewed

EXTERNAL -> PLATFORM SURFACE
  finding preview environments reachable without authentication
  control SSO in front of every preview; never publicly routable
```

```text
Standing privilege inventory - the exercise that finds the forgotten credential:

  IDENTITY                     REACH                        COMPROMISE = ?         DETECTED BY
  crossplane-provider-aws      create/delete infra in 4      total infrastructure   CloudTrail anomaly,
                               accounts, bounded by tag      control                unexpected region
  argocd-application-ctrl      apply anything in 9 clusters  arbitrary workload     drift + audit log
                                                             in every tenant
  ci-publish role              push images, sign artefacts   supply chain           transparency log
  kyverno webhook              mutate every Pod              code execution in      manifest diff
                                                             every workload
  platform-operator break-glass cluster-admin, 30m           everything, briefly    activation alert
  legacy-backup-runner          read all volumes             all data at rest       <-- NOTHING.
                                                                                    Created 2024,
                                                                                    owner left, no
                                                                                    monitoring. DELETE.

  The last row is what this exercise is for. Every platform has one.
```

## Interview tips

- Open by naming what makes a platform different: its automation is the most privileged actor in the estate, so a control-plane or pipeline compromise is a compromise of every service.
- Work boundaries, not components. Boundaries yield attack paths; component lists yield technology inventories.
- The confused-deputy problem is the highest-value thing to raise - a tenant crafting a resource that makes your controller act privileged on their behalf. Give the cross-namespace `secretRef` example; it is concrete and common.
- Threat modelling your own tooling - webhooks as code execution vectors, controllers fetching URLs as SSRF primitives - is the point most candidates miss entirely.
- Include availability as a security property, because for a platform denying service to one tenant denies it to all.
- The standing privilege inventory is a strong practical suggestion, and the forgotten credential with no monitoring is a realistic finding worth describing.
- Close on repeatability: the boundary list belongs in your design review for each new capability, not in a one-off document.

---

[⬅ Back to Platform Security](./README.md) · [All topics](../README.md)
