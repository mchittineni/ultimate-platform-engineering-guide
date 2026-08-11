---
title: "How do you give teams visibility into platform state that affects them?"
id: 116
category: "Platform Observability"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - platform-observability
  - interview-questions
---

# How do you give teams visibility into platform state that affects them?

**Short answer:** Surface the platform's state where the team is already looking and scoped to their own resources - why their deploy has not landed, whether their claim is provisioning, whether a control is unenforced, whether a capability is degraded. The failure to avoid is a platform that is observable only to the platform team, because then every question arrives as a support message and your team becomes a lookup service for your own dashboards.

## Detail

**The support load is the symptom.** "Is the platform broken or is it me?" and "why has my deploy not gone out?" are the two most common platform support messages, and both are answerable from data the platform already has. Every time a team has to ask, the platform failed to expose something it knew.

**Scope the view to the team's own resources.** A global platform dashboard is useful to the platform team and nearly useless to a product team - they need their services, their claims, their deploys, their quota. Filtering by owner from the catalogue is what turns platform telemetry into something a team will actually open.

**Expose the state of each in-flight request.** A deploy or a provisioning claim should have a visible status with a reason: waiting for CI, queued for reconciliation, applying, waiting for health checks, failed with this error. Status conditions on the platform's own custom resources make this straightforward, and surfacing them - in the portal, in the pull request, or via the CLI - is the difference between a transparent platform and an opaque one.

**Report back into the pull request.** The pull request is where the team already is. A comment saying the change is deployed to production, or that it is queued behind a reconciliation backlog, or that it failed a policy check with the specific field named, removes an entire class of enquiry at essentially no cost.

**Publish per-capability status, not one overall health indicator.** "The platform is degraded" tells a team nothing. "Provisioning is degraded, deploys are normal, ingress is normal" tells them whether to wait or to escalate. This maps directly onto the capability SLOs, which is another reason to define them that way.

**Make silent conditions loud to the affected team.** If policy is unenforced because the engine is unavailable, if flag rules are stale, if telemetry is being sampled more aggressively under load, or if a quota is close to exhausted - the affected team should see it. Silent degradation is worse than failure because nobody investigates, and the team is the one who can act on some of these.

**Show them their quota and cost.** Approaching a quota limit should be visible before it causes a failed deploy, and cost attribution should be visible continuously rather than in a monthly report. Both are cases where the platform holds information the team needs to make decisions.

**Give them the change feed for their scope.** Deploys, flag flips, infrastructure changes, and policy changes affecting their services, in one timeline. This answers the first question of every incident - what changed - without the team needing to check four systems.

**Measure the support channel to find what is still missing.** Categorise the questions asked; each recurring category is a piece of state you have not exposed. That closes the loop and turns support load into a roadmap for observability, which is the same product-feedback pattern as escape hatches and break-glass activations.

## Example

```text
The team-scoped view - filtered by owner, so it is worth opening.

  $ platform status --team team-payments

  YOUR SERVICES
    checkout        tier 1   healthy    v1.4.2   SLO: 99.94% (budget 38% used)
    pricing         tier 2   healthy    v2.1.0   SLO: 99.97% (budget 11% used)
    refunds-worker  tier 3   healthy    v0.9.4   SLO: n/a

  IN FLIGHT - with a REASON, not just a spinner
    deploy checkout v1.4.3
      merged 09:14 · image built 09:19 · QUEUED FOR RECONCILIATION since 09:21
      reason: reconciliation backlog on prod-eu-1 (platform incident INC-2291)
      expected: within 25 min · you do not need to do anything
    claim postgres/reporting-db
      created 09:02 · PROVISIONING · waiting for the instance to become available
      expected: within 6 min

  PLATFORM CAPABILITIES AFFECTING YOU - per capability, not one health light
    deploy .............. DEGRADED   reconciliation lag 22m (SLO 15m) · INC-2291
    provision ........... normal
    ingress ............. normal
    secret delivery ..... normal
    telemetry ........... normal

  CONDITIONS YOU SHOULD KNOW ABOUT - loud, not silent
    ⚠ policy `require-resource-requests` is currently UNENFORCED platform-wide
      (policy engine degraded). Your next deploy will not be checked.
    ⚠ your namespace quota: 34/40 CPU used. A deploy needing >6 CPU will fail.

  YOUR COST THIS MONTH
    compute $6,200 · data $1,900 · observability $6,700 · total $14,800
    observability is 45% of your spend - see the cardinality report

  RECENT CHANGES AFFECTING YOU - one timeline, four sources
    13:47  FLAG    checkout-new-pricing 0% -> 5%      alice
    11:02  INFRA   checkout-db resized                 bob (PR #1204)
    09:14  DEPLOY  checkout v1.4.2                     alice / dave / carol
    08:30  POLICY  require-resource-requests -> Enforce platform-team
```

```yaml
# The mechanism: status conditions on the platform's own resources, surfaced
# wherever the team is looking.
apiVersion: platform.example.com/v1
kind: Service
metadata: { name: checkout, namespace: team-payments }
status:
  observedGeneration: 7 # distinguishes "reconciled" from "not looked at yet"
  conditions:
    - type: Ready
      status: "False"
      reason: ReconciliationQueued
      # A reason a developer can act on - or, here, correctly NOT act on
      message: >
        Deploy of v1.4.3 is queued. Reconciliation backlog on prod-eu-1
        (INC-2291). Expected within 25 minutes. No action needed.
      lastTransitionTime: "2026-08-11T09:21:00Z"
    - type: PolicyEnforced
      status: "False"
      reason: PolicyEngineDegraded
      message: "require-resource-requests is not being evaluated; engine degraded."
```

```text
Closing the loop - the support channel as a list of things not yet exposed:

  $ platform support categorise --last 90d

  CATEGORY                                    COUNT   EXPOSED NOW?
  "why has my deploy not gone out"              41     ✓ in-flight status + PR
                                                         comment. Was 41, now ~3.
  "is the platform broken or is it me"          33     ✓ per-capability status
  "why did my deploy fail policy"               18     ✓ named field in the PR
                                                         comment
  "am I near my quota"                          12     ✓ quota panel + alert at 85%
  "what is my observability cost"                9     ✓ cost panel
  "did anything change before my incident"       7     ✓ change feed
  "how do I get a bigger database"               6     ✗ documentation gap, not an
                                                         observability gap
  "my private endpoint does not resolve"         4     ✗ fixed by policy instead
                                                         (DeployIfNotExists)

  Six of eight categories were state the platform already knew and had not shown.
  Each recurring question is an observability defect, not a support burden.
```

## Interview tips

- Frame it by the support load: "is it broken or is it me" and "why has my deploy not gone out" are both answerable from data the platform already holds, so every such question is a defect.
- Scoping by owner is what makes the view usable. A global dashboard serves the platform team and not the product teams.
- Per-capability status rather than one health indicator is the concrete design point, and it maps onto the capability SLOs.
- Reporting into the pull request is the cheapest high-value channel, because it is where the team already is.
- Exposing a reason for in-flight state - queued behind a backlog, no action needed - is the difference between transparency and a spinner. Status conditions with `observedGeneration` are the mechanism.
- Making silent conditions loud, especially unenforced policy and near-exhausted quota, shows you understand that silent degradation is worse than failure.
- Categorising the support channel to find unexposed state is the closing loop, and it turns support load into an observability roadmap.

---

[⬅ Back to Platform Observability](./README.md) · [All topics](../README.md)
