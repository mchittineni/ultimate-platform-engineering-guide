---
title: "What is a feature flag?"
id: 93
category: "Progressive Delivery and Feature Flags"
difficulty: "Beginner"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# What is a feature flag?

**Short answer:** A feature flag is a conditional in your code whose value is decided at runtime by configuration held outside the code, so you can change what the software does without deploying it again. The code ships with both paths; a flag service evaluates a rule for each user or request and returns which one to run. That lets you turn a feature on for 1% of users, for internal staff only, or off in seconds during an incident.

## Detail

**The mechanism, step by step.** A flag evaluation has four parts:

1. **The call site** - the `if` in your code, with a flag key and a default value to use if nothing else answers.
2. **The evaluation context** - facts about the current request: a stable targeting key such as the user or account ID, plus attributes like country, plan, or app version.
3. **The rules** - configuration stored in a flag provider: "on for accounts in the beta list, on for 10% of everyone else, off otherwise".
4. **The result** - the variant served (a boolean, or a string, number, or object for multi-variant flags) and the reason it was chosen.

Percentage rules are deterministic: the SDK hashes the targeting key with the flag key and puts the user in a bucket, so the same user gets the same answer on every request. That stickiness is what makes a 10% rollout mean "10% of users" rather than "10% of requests, randomly".

**Where evaluation happens matters.** Most server-side SDKs download the rules and evaluate them in process, which means no network call per flag check and no outage if the provider is briefly unreachable. Client-side SDKs in browsers and mobile apps usually receive already-evaluated results instead, because shipping the full rule set to a device would leak targeting logic. A consequence worth knowing: anything evaluated on a client can be tampered with, so a flag must never be the thing that enforces a security decision.

**The four kinds of flag.** Classifying flags by purpose tells you how long each should live:

| Type        | Purpose                                  | Expected lifespan                                  |
| ----------- | ---------------------------------------- | -------------------------------------------------- |
| Release     | Hide unfinished or risky work, then ramp | Weeks - then delete it                             |
| Experiment  | A/B test two variants against a metric   | Until a winner is chosen                           |
| Operational | Kill switch or load-shedding control     | Permanent, by design                               |
| Permission  | Which customers get a feature            | Long - often better moved to an entitlement system |

**What flags give you.** Trunk-based development without long-lived branches, because unfinished work merges behind a flag that is off. Release independent of deployment. Targeted rollouts to staff or beta customers first. Instant rollback of behaviour without waiting for a pipeline.

**What they cost.** Every flag is a second code path that has to be tested in both states and removed once the decision is made. Flags that are never removed pile up as flag debt - dead branches, confusing logic, and switches someone might flip by mistake. A flag also only controls _future_ behaviour: turning it off does not un-send an email the new path already sent.

**Who uses it, and the platform's part.** Product engineers write the call sites; product managers and on-call engineers often change the rules. The platform team's job is to make flags safe by default: a shared SDK wrapper (ideally on the vendor-neutral OpenFeature API) with safe defaults and telemetry, a registry that records an owner and type for each flag, and automation that flags stale flags for removal. See [How do you run feature flags as a platform capability?](./how-do-you-run-feature-flags-as-a-platform-capability.md) for the full design.

## Example

```typescript
// Node.js service using the OpenFeature server SDK with the flagd provider.
import { OpenFeature } from "@openfeature/server-sdk";
import { FlagdProvider } from "@openfeature/flagd-provider";

await OpenFeature.setProviderAndWait(new FlagdProvider());
const flags = OpenFeature.getClient("checkout");

export async function renderCheckout(user: { id: string; country: string }) {
  // Default false: if the provider cannot answer, the old path runs.
  const useNewFlow = await flags.getBooleanValue("new-checkout-flow", false, {
    targetingKey: user.id,
    country: user.country,
  });
  return useNewFlow ? newCheckout(user) : legacyCheckout(user);
}
```

```json
{
  "$schema": "https://flagd.dev/schema/v0/flags.json",
  "flags": {
    "new-checkout-flow": {
      "state": "ENABLED",
      "variants": { "on": true, "off": false },
      "defaultVariant": "off",
      "targeting": {
        "if": [{ "==": [{ "var": "country" }, "GB"] }, { "fractional": [["on", 10], ["off", 90]] }, "off"]
      }
    }
  }
}
```

```text
Reading the rule: users in GB are split 10% on / 90% off, bucketed on their
targetingKey so each user always gets the same answer. Everyone else is off.
Changing 10 to 50 widens the rollout - no build, no deploy.
```

## Interview tips

- Define it by mechanism: a runtime conditional whose value comes from external configuration, evaluated against a context. "An on/off switch" undersells it.
- Explain deterministic bucketing on a stable key - it is the detail that shows you understand how percentage rollouts actually work.
- Name the four types and that only release and experiment flags are meant to be temporary. This leads naturally into flag debt, a common follow-up.
- Volunteer the limits: a flag does not reverse state, and a client-side flag must never enforce security.
- Mention OpenFeature as the vendor-neutral API and name the platform's role - a wrapper, a registry, and cleanup automation - so product teams get flags without owning the risks.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
