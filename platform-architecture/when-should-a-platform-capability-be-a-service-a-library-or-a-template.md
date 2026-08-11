---
title: "When should a platform capability be a service, a library, or a template?"
id: 20
category: "Platform Architecture"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-architecture
  - interview-questions
---

# When should a platform capability be a service, a library, or a template?

**Short answer:** The deciding question is how you will ship a fix. A service you upgrade centrally and every consumer gets it immediately - at the cost of becoming a runtime dependency. A library you upgrade centrally but consumers must adopt, which means a fix propagates only as fast as forty teams rebuild. A template is copied once and then diverges permanently, so it is right only for things you never need to change. Pick by change cadence and blast radius, not by elegance.

## Detail

**The three shapes:**

| Shape        | Fix propagation                      | Runtime coupling         | Use when                                             |
| ------------ | ------------------------------------ | ------------------------ | ---------------------------------------------------- |
| **Service**  | Instant, you control it              | High - a live dependency | Central policy, cross-cutting state, frequent change |
| **Library**  | Requires consumer rebuild and deploy | Low - in-process         | Per-request logic, must be in the language runtime   |
| **Template** | Never - copies diverge               | None                     | Initial scaffolding you accept diverging             |

**Service: instant fixes, real coupling.** A rate limiter or authorisation service can be fixed for everyone in one deploy. The price is that you are now in someone's request path with data-plane reliability requirements, added latency, and an outage that is everyone's outage. Choose it when the capability needs shared state, must be consistent across services, or changes often enough that library upgrades would never keep pace.

**Library: the upgrade treadmill is the whole problem.** A library gives you no runtime coupling and no latency, which is why it fits per-request concerns like structured logging, telemetry instrumentation, and flag evaluation. But shipping a critical fix means getting every consumer to bump a version, rebuild, and deploy - and the long tail is measured in months. If you have three languages in the estate, you have three implementations to maintain, which is the hidden cost people underestimate.

**Template: for things you will not change.** Scaffolding is the honest use case: generate the repository, then the team owns it. The failure mode is using a template for something that needs to evolve - a copied CI pipeline in forty repositories cannot be updated, and you discover this the first time you need to change how images are signed.

**The two hybrids that solve most real cases:**

- **Thin library over a service.** The library is a stable, minimal client; the logic and policy live in the service. Fixes to behaviour ship centrally, and the library changes rarely. OpenFeature's SDK-plus-provider model is exactly this shape, and it is why it is a good pattern to cite.
- **Sidecar or agent.** Runs alongside the workload, so it is language-agnostic and upgradeable by the platform through a rolling restart, without being in a separate network hop. This is how service meshes and telemetry collectors escape the library treadmill, at the cost of per-pod resource overhead.

**Reconciled generation beats templating.** If you want template-like ergonomics with the ability to change things later, generate the artefacts from a declarative spec and reconcile them continuously. The developer writes twenty lines, the platform owns the output, and improving the output improves every service - the property a template can never give you.

**The decisive test.** Ask: "a critical bug is found in this capability on a Friday - how does the fix reach production everywhere?" Service, one deploy. Sidecar, a rolling restart you control. Library, a campaign. Template, individual pull requests to forty repositories, forever.

## Example

```text
The same estate, capability by capability, decided by the Friday-fix test.

CAPABILITY                     SHAPE            WHY
  authorisation decisions       service          shared policy, must be consistent,
                                                 changes weekly, cannot be stale
  rate limiting                 service          needs shared counter state
  secret retrieval              sidecar/CSI      language-agnostic, platform-upgradeable
  telemetry collection          sidecar/agent    escapes per-language libraries;
                                                 OTel collector upgraded by us
  structured logging fields     thin library     must run in-process; kept minimal
                                                 so it almost never needs a bump
  feature flag evaluation       thin lib + svc   OpenFeature SDK (stable) + provider
                                                 (all logic and rules server-side)
  new repository scaffold       template         one-time; divergence is expected
  CI pipeline definition        NOT a template   -> reusable workflow / shared pipeline
                                                 referenced by version, so we can fix it
  Kubernetes manifests          NOT a template   -> generated + reconciled from the
                                                 Service spec, so defaults improve
                                                 for everyone at once

The two "NOT a template" rows are where most organisations get this wrong. A
copied Jenkinsfile or a copied Helm chart in 40 repositories is a decision to
never improve them again.
```

```text
Friday-fix test, applied to one capability at each end of the spectrum:

  Critical bug in authorisation logic (service)
    12:10  fix merged
    12:25  deployed behind a flag, 1% -> 100% over 40 minutes
    13:05  every service in the estate is fixed.        Elapsed: ~1 hour.

  Critical bug in the logging library (library)
    12:10  fix merged, v2.4.1 published
    12:30  automated bump PRs raised across 41 repositories
    Day 3  28 merged and deployed
    Wk 3   38 deployed
    Wk 9   41 deployed - the last three needed direct conversations.
                                                        Elapsed: ~9 weeks.

  This asymmetry is the entire decision. It is also why anything security-critical
  should be a service or a sidecar, never a library.
```

## Interview tips

- Lead with the Friday-fix test. It reframes the question from taste to operations and is the framing interviewers remember.
- Say explicitly that a template is a decision never to change something. Most candidates treat templates as harmless.
- The thin-library-over-a-service hybrid, with OpenFeature as the example, is the strongest technical detail available here.
- "Anything security-critical should not be a library" follows directly from propagation speed and is a good, defensible conclusion to volunteer.
- Expect "we have four languages" - that is the argument for sidecars and services over libraries, and for keeping any unavoidable library as thin as possible.

---

[⬅ Back to Platform Architecture](./README.md) · [All topics](../README.md)
