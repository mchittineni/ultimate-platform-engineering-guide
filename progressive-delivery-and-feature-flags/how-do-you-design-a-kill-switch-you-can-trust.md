---
title: "How do you design a kill switch you can trust?"
id: 55
category: "Progressive Delivery and Feature Flags"
difficulty: "Advanced"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# How do you design a kill switch you can trust?

**Short answer:** It must work when the thing you depend on is the outage. That means a local override the workload reads before consulting any provider, a documented trigger in the runbook with the exact command, verification in staging before the feature ever ships, and a game day that actually exercises it. A kill switch that requires the flag provider to be reachable is not a kill switch when the provider is what failed.

## Detail

**The failure that invalidates most kill switches.** The switch lives in a flag provider. The incident is that the provider is unreachable, or your network path to it is degraded, or an authentication dependency is down. You reach for the switch and cannot set it. Worse, if your SDK is configured to fail toward defaults, an unreachable provider may itself flip behaviour for everyone at once - the outage and the loss of control arrive together.

**The break-glass local override is the fix.** The SDK checks, in order: a local override source (an environment variable, a file, a config map mounted into the Pod), then the provider's streamed rules, then the cached last-known-good ruleset, then the call-site default. Because the override is first and local, it works with no network at all, and setting it is a deploy-free change to a config map that your existing tooling can apply.

**Cache the last-known-good ruleset on disk.** Without it, a Pod restarting during a provider outage evaluates every flag to its call-site default. In a scaling event or a rolling restart that means behaviour changing for a large share of traffic at the worst possible moment. Persisting the ruleset means a cold start behaves like a warm one.

**Test the switch before the feature ships,** not after. In staging: enable the feature, exercise it, throw the switch, and confirm the old path resumes fully - including that in-flight requests complete correctly and no state was left half-written. A switch that has never been thrown is an assumption.

**Write the trigger down, with the exact words and the exact command.** "Disable if error rate is elevated" is not usable at 3am by someone who did not build the feature. "If the `pricing-mismatch` alert fires, or 5xx exceeds baseline by 1 point, run `platform flags kill checkout-new-pricing-engine`" is. The runbook entry belongs in the registry so it is discoverable from the alert.

**Automate the obvious cases.** Threshold breaches should trigger the switch without waiting for a human. Keep the manual path for judgement calls, and make sure both paths are the same mechanism so the automated one is exercised regularly.

**Be explicit about what the switch cannot undo.** Flipping to 0% stops the new behaviour for future requests. It does not un-send emails, un-capture payments, un-publish events, un-poison a cache, or un-write rows the new path created. Reversibility of _state_ is a separate design problem and the switch does not solve it.

**Never let the switch depend on the system it protects.** A kill switch for the authentication service that requires authenticating to the flag provider is circular. Break the cycle deliberately - for the most critical switches, the local override is the primary mechanism rather than the fallback.

## Example

```text
Resolution order in the platform SDK. The first source is local, so the switch
works with no network, no provider, and no authentication.

  1. LOCAL OVERRIDE      env var PLATFORM_FLAG_OVERRIDE_<KEY>, or
                         /etc/platform/flag-overrides.yaml (mounted ConfigMap)
                         -> works with zero connectivity. THE break-glass path.
  2. streamed rules      from the provider or a local relay, evaluated in process
  3. last-known-good     ruleset cached on disk from the previous successful sync
                         -> a cold start during a provider outage behaves like a
                            warm one instead of flipping everyone to defaults
  4. call-site default   the safe value the developer wrote

  A provider outage therefore changes nothing: 3 covers evaluation, 1 covers control.
```

```yaml
# The break-glass override. Applying this needs only cluster access - no flag
# provider, no vendor console, no internet.
apiVersion: v1
kind: ConfigMap
metadata:
  name: flag-overrides
  namespace: team-payments
data:
  overrides.yaml: |
    # INC-2291 - pricing mismatch. Set 2026-08-11T02:14Z by bob.
    # Expires when the provider is reachable and the flag is set to 0% there.
    checkout-new-pricing-engine: "false"
```

```yaml
# The registry entry carries the trigger, so it is discoverable from the alert
# rather than living in someone's memory.
key: checkout-new-pricing-engine
type: release
owner: alice@example.com
kill_switch:
  # Exact words, so an on-call engineer who has never seen this feature can act.
  trigger: |
    Kill if ANY of:
      - alert `pricing-mismatch` fires
      - 5xx rate exceeds baseline by more than 1 percentage point
      - a customer reports an incorrect total and it is reproducible
  command: platform flags kill checkout-new-pricing-engine
  break_glass: |
    If the flag provider is unreachable:
      kubectl -n team-payments patch configmap flag-overrides \
        --type merge -p '{"data":{"overrides.yaml":"checkout-new-pricing-engine: \"false\"\n"}}'
      kubectl -n team-payments rollout restart deploy/checkout
  automated: true # threshold breaches fire the same mechanism, unattended
  not_reversed_by_kill: |
    Orders already priced with the new engine are written and may have been
    charged. The switch stops future mispricing; it does not correct past orders.
    Remediation requires the pricing-recon job plus a refund run - see RB-114.
  verified_in_staging: 2026-07-16 # tested BEFORE the feature shipped
  last_game_day: 2026-08-01 # exercised since
```

```text
The game day that turns the assumption into a fact:

  $ platform game-day flag-kill-switch --flag checkout-new-pricing-engine

  1. block egress to the flag provider from the checkout namespace
     ✓ evaluation continues from the on-disk last-known-good ruleset
     ✓ a pod restarted during the outage did NOT fall back to defaults
  2. attempt the normal kill path
     ✓ fails as expected - provider unreachable
  3. apply the break-glass ConfigMap override
     ✓ new pricing path disabled within 40s of the rollout restart
     ✓ legacy path serving correctly; no in-flight request errors
  4. restore egress
     ✓ provider rules resume; local override still wins until removed
     ✓ removing the override returns control to the provider

  Result: the switch works during a provider outage. Before this drill it was
  a design intention.
```

## Interview tips

- The defining line: a kill switch that needs the provider to be reachable is not a kill switch when the provider is the outage.
- Give the four-level resolution order with the local override first. It is concrete, and it is the mechanism that makes the guarantee real.
- The cold-start problem - a Pod restarting during a provider outage falling back to defaults for every flag - is a strong detail that shows you have thought past the happy path.
- Insist the switch is tested before the feature ships, and that a game day exercises it afterwards. Untested switches are assumptions and interviewers know it.
- Be explicit about what the switch cannot undo. Naming un-sent emails, captured payments, and published events, and separating behaviour from state, is the senior close.
- Circular dependencies - a kill switch for auth that requires auth - is a sharp example worth having ready.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
