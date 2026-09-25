---
title: "How do you run feature flags as a platform capability?"
id: 100
category: "Progressive Delivery and Feature Flags"
difficulty: "Advanced"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# How do you run feature flags as a platform capability?

**Short answer:** Ship a paved path nobody needs to bypass - a vendor-neutral SDK wrapper the platform owns, a flag registry reviewed as code, a CI gate that rejects a flag without an owner, a type, a kill-switch trigger, and a dashboard, and a bot that opens the removal pull request when a flag has been fully rolled out. Teams get self-service flag creation; the guardrails are not optional. The platform's job is not to decide what to flag, it is to make sure no flag can become unowned or immortal.

## Detail

**Wrap the provider behind your own interface.** Product teams should import the platform's client, not a vendor SDK. OpenFeature (a CNCF incubating project) is the natural shape for this - a vendor-neutral evaluation API with a provider behind it, covered in [What is OpenFeature and why does a vendor-neutral flag API matter?](./what-is-openfeature-and-why-does-a-vendor-neutral-flag-api-matter.md) - and it means switching providers costs one adapter rather than touching every call site. It is also where you put the defaults that matter: initialisation behaviour, cached last-known-good rules, telemetry on every evaluation, and a safe default when the provider cannot be reached.

**Make the registry an artefact, not a wiki page.** Each flag has an entry in version control with a named individual owner, a type, the kill-switch trigger, and a dashboard link. Reviewing that entry in a pull request is when the useful conversation happens: does this need to be a flag at all, or would a deploy, a config change, or a role do it?

**The CI gate is what makes the registry real.** A pre-merge check that scans the code for flag identifiers and cross-references the registry, failing on a flag with no entry and warning on an entry missing a field. Without the gate the registry is documentation and will be stale within a quarter; with it, an unregistered flag cannot merge.

**Classify at creation, because the type determines the lifespan.** Release flags exist to be removed; experiment flags end when a winner is picked; operational flags such as kill switches are permanent by design; permission flags are entitlements and arguably should not be in a flag system at all. Only the first two carry cleanup deadlines, and conflating them is why "clean up your flags" campaigns fail - they chase permanent flags alongside temporary ones.

**Never gate a security decision on a flag,** particularly not one evaluated client-side. Entitlements and authorisation belong in the authorisation system, where they are enforced server-side and audited. A flag provider is a configuration distribution system, not an access control system.

**Record the served variant in telemetry.** Every request should carry which variant it received as a span attribute or log field. OpenTelemetry's feature flag semantic conventions define a `feature_flag.evaluation` event with `feature_flag.key`, `feature_flag.result.variant`, and `feature_flag.provider.name` (the older `feature_flag.variant` and `feature_flag.provider_name` names were renamed); they are at release-candidate rather than stable status, so pin the semantic conventions version your wrapper emits. An OpenFeature hook is the natural place to emit them once for every service. Without it you cannot attribute a latency regression or an error spike to a variant, which means you cannot safely automate a rollout at all.

**Treat a flag flip as a production change.** It changes behaviour without a deploy, so it needs an audit trail, optional four-eyes approval for high-risk flags, and an annotation in your change feed and on your dashboards. Otherwise you cannot correlate an alert with the flip that caused it, and your change failure rate silently excludes your riskiest class of change.

**Evaluation architecture is a platform decision.** Prefer server-side local evaluation - rules streamed to the SDK and evaluated in process - so there is no network hop per call and no provider dependency in the request path. A relay or edge proxy helps with latency, egress containment, and data residency. Remote per-call evaluation puts a vendor in your data plane, which is a choice to make deliberately rather than by default.

## Example

```yaml
# The registry entry. The four required fields exist because each one answers a
# question someone will ask during an incident.
# flags/checkout-new-pricing-engine.yaml
key: checkout-new-pricing-engine
type: release # release | experiment | operational | permission
owner: alice@example.com # a named person, not a team - teams do not get paged
service: checkout
created: 2026-07-14
justification: >
  New pricing calculation path. Needs per-user rollout with instant rollback
  because a pricing error is customer-visible and irreversible in-flight.
kill_switch:
  trigger: "5xx > baseline + 1pp, or pricing-mismatch alert fires"
  action: "set to 0% via provider API (automated webhook)"
dashboard: https://grafana.example.internal/d/checkout-pricing
cleanup:
  criteria: "100% for 7 consecutive days with no rollback"
  target_date: 2026-10-12 # release flags: 90 days from creation (our policy)
```

```python
# The platform's wrapper. Teams import this; nobody imports a vendor SDK.
from platform_flags import flags   # OpenFeature client + platform defaults

def price(cart, user):
    # Context is propagated from the request, so bucketing is consistent across
    # services - the same user gets the same variant everywhere.
    if flags.enabled("checkout-new-pricing-engine", default=False, ctx=user.flag_ctx):
        return new_pricing.calculate(cart)
    return legacy_pricing.calculate(cart)
```

```text
What the wrapper guarantees, so no team has to get these right:

  default-safe            an unreachable provider returns the call-site default,
                          never an exception, never a hang
  no init race            waits for initialisation at startup; a flag evaluated
                          before the ruleset loads would silently return defaults
  last-known-good cache   ruleset persisted to disk, so a cold start during a
                          provider outage does not flip every user at once
  local evaluation        rules streamed and evaluated in process - no network
                          hop per call, no vendor in the request path
  consistent bucketing    same key + salt everywhere in the estate
  telemetry               feature_flag.key and feature_flag.result.variant on
                          every evaluation, via one OpenFeature hook
  audit                   every flip recorded with actor, time, and old -> new
```

```text
The CI gate - what makes the registry real rather than aspirational:

  $ platform flags audit --pre-merge

  ✗ FAIL  flag "checkout-express-lane" found in code, no registry entry
          checkout/handlers/cart.py:214
          -> add flags/checkout-express-lane.yaml before merging

  ⚠ WARN  flag "search-rerank-v2" registry entry missing `dashboard`
          -> you will want this at 3am

  ✗ FAIL  flag "billing-plan-premium" is type: permission
          -> permission flags belong in the entitlements service, not here.
             A client-side flag must never gate a security decision.

  ⚠ WARN  registry entry "old-cart-flow" has no code reference
          -> orphaned config: someone can still flip a dead switch. Remove it.

  Note the last two: the audit runs in BOTH directions. Code with no registry
  entry, and registry entries with no code. Only checking one direction leaves
  half the problem in place.
```

## Interview tips

- Frame it as the platform owning the paved path and the guardrails while teams own the flags. The platform does not decide what to flag; it makes unowned and immortal flags impossible.
- Name OpenFeature and the wrapper pattern, and give the concrete payoff: switching providers costs one adapter instead of every call site.
- The four required registry fields - owner, type, kill-switch trigger, dashboard - plus a CI gate that enforces them, is the most actionable part of the answer.
- Say the audit runs in both directions. Code without a registry entry and registry entries without code are both real problems, and most candidates only mention the first.
- "A flag flip is a production change without a deploy" is the sentence that connects this to change management, DORA metrics, and dashboard annotations.
- Refusing to gate security decisions on flags, and pushing entitlements to the authorisation system, is a strong judgement signal.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
