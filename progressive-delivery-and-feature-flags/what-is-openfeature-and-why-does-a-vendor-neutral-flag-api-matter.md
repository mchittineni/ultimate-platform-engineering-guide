---
title: "What is OpenFeature and why does a vendor-neutral flag API matter?"
id: 99
category: "Progressive Delivery and Feature Flags"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# What is OpenFeature and why does a vendor-neutral flag API matter?

**Short answer:** OpenFeature is a CNCF incubating project that defines a standard API and SDKs for evaluating feature flags, with the actual flag system plugged in behind it as a "provider". Application code calls `getBooleanValue("new-checkout", false, context)` the same way whether the answer comes from a commercial vendor, an open-source server such as flagd, or an in-house system. That matters because flag calls end up in thousands of places in a codebase: without a neutral API, changing or consolidating providers means touching every one of them, and every team instruments, defaults, and tests flags differently.

## Detail

**What OpenFeature standardises - and what it does not.** It standardises the _evaluation_ side: how code asks for a flag value, what context it passes, what comes back, and how you extend that pipeline. It does not standardise how flags are defined, targeted, or managed in a UI; that remains the provider's job. The specification is language-agnostic and is implemented by SDKs for the major languages, server and client-side.

**The building blocks.**

- **Evaluation API.** Typed calls - boolean, string, number, object - each with a mandatory default, returning either a value or a details object with the variant, the reason (`TARGETING_MATCH`, `SPLIT`, `DEFAULT`, `ERROR` and so on), and any error code. The API is designed never to throw into application code: on failure you get the default plus an error reason.
- **Providers.** Adapters that translate the standard calls into a specific flag system. Swap the provider at start-up and no call site changes. Domains let different clients bind to different providers in one process, which is how you migrate one service area at a time.
- **Evaluation context.** The targeting key and attributes used for rules. Context can be set globally, per client, per request (transaction context propagation), and per call, and is merged in a defined order - so the platform can attach region and service version once while the request middleware attaches the user.
- **Hooks.** Code that runs before, after, on error, and finally around every evaluation. This is where a platform adds telemetry, validation, and logging once for everyone.
- **Events.** Provider lifecycle signals such as ready, error, stale, and configuration changed, so an application can wait for initialisation instead of serving defaults during start-up.
- **Tracking.** A `track` call that records a user action such as a completed checkout against the flags they were served, giving experimentation back-ends the outcome data in a vendor-neutral way.

**The wider ecosystem.** flagd is the project's reference flag daemon, driven by flag definitions in JSON or YAML that can live in Git, a ConfigMap, or a custom resource via the OpenFeature Operator on Kubernetes. The OpenFeature Remote Evaluation Protocol (OFREP) standardises the wire protocol for evaluating flags against a remote service, so one generic provider can talk to any compatible back-end. A multi-provider composes several providers with a strategy - use the first that has the flag, or evaluate both and compare - which is the practical tool for migrating between systems.

**Why the neutral API matters for a platform.**

- **Migration becomes an adapter change.** Moving vendors, consolidating after an acquisition, or moving to a self-hosted system for data residency changes one provider registration, not every repository.
- **Guardrails live in one place.** Safe defaults, readiness waits, hooks for telemetry, and context propagation are written once in the platform wrapper and apply regardless of provider.
- **Consistent observability.** OpenTelemetry's feature flag semantic conventions (`feature_flag.key`, `feature_flag.result.variant`, `feature_flag.provider.name` and others, still at release-candidate stability) map naturally onto OpenFeature's evaluation details, so every service reports flag evaluations the same way.
- **Testing without the vendor.** An in-memory provider lets unit tests set flag values directly, with no network and no mocking of a vendor SDK.
- **Mixed estates are normal.** Large organisations often run more than one flag system. A common API means developers learn one interface and code reviews look the same everywhere.

**The trade-offs and limits.**

- **Lowest common denominator.** Vendor-specific features - experiment analysis, rich debugging, some client-side capabilities - are not in the standard API. You either give them up, reach through to the vendor SDK (reintroducing lock-in at that call site), or use provider-specific extensions deliberately and sparingly.
- **Maturity varies.** Parts of the specification are still marked experimental or hardening, and SDK and provider quality differs between languages. Check the provider you need exists and is maintained for each language you run.
- **It is not a flag management system.** Adopting OpenFeature does not give you targeting, audit logs, approvals, or a UI; the provider still does. It also does not remove the need for a registry and cleanup process.
- **Another layer to understand.** Initialisation, event handling, and context merging add concepts; the platform wrapper should hide most of them from product teams.

**Who uses it.** Product engineers use it indirectly, through the platform's wrapper, and see one stable interface. The platform team uses it to own defaults and telemetry centrally and to keep the option of changing providers without a migration programme across every team.

## Example

```typescript
// platform-flags/index.ts - the platform's wrapper around OpenFeature.
// Product teams import `flags`; they never import a vendor SDK directly.
import { OpenFeature, type Hook, type HookContext, type EvaluationDetails, type FlagValue } from "@openfeature/server-sdk";
import { FlagdProvider } from "@openfeature/flagd-provider";

// One hook, applied to every evaluation in every service.
const telemetryHook: Hook = {
  after(ctx: HookContext, details: EvaluationDetails<FlagValue>) {
    metrics.increment("feature_flag.evaluation", {
      "feature_flag.key": ctx.flagKey,
      "feature_flag.result.variant": details.variant ?? "unknown",
      "feature_flag.provider.name": ctx.providerMetadata.name,
    });
  },
  error(ctx: HookContext, err: unknown) {
    log.warn("flag evaluation failed, default served", { key: ctx.flagKey, err });
  },
};

export async function initFlags() {
  OpenFeature.addHooks(telemetryHook);
  OpenFeature.setContext({ service: process.env.SERVICE_NAME, region: process.env.REGION });
  // Wait for readiness, so the first requests do not silently get defaults.
  await OpenFeature.setProviderAndWait(new FlagdProvider());
}

export const flags = OpenFeature.getClient();
```

```typescript
// A product team's call site - identical whichever provider the platform chooses.
import { flags } from "@example/platform-flags";

const details = await flags.getBooleanDetails("checkout-new-pricing-engine", false, {
  targetingKey: `account:${user.accountId}`,
  plan: user.plan,
});
// details.value, details.variant, details.reason ("SPLIT", "DEFAULT", "ERROR", ...)

await flags.track("checkout-completed", { targetingKey: `account:${user.accountId}` }, { value: order.total });
```

```text
Migrating providers, as the platform team runs it:

  week 1   register a multi-provider: [new-vendor, flagd]
           strategy: evaluate both, serve flagd's answer, log mismatches
  week 2   mismatch rate 0.00% across 42 services -> serve new-vendor first
  week 4   remove flagd from the provider list

  Application code changed in that migration: none. One package version bump.
```

## Interview tips

- Define it precisely: a standard evaluation API and SDKs with pluggable providers, CNCF incubating. Say it standardises evaluation, not flag management.
- Name the building blocks - providers, evaluation context, hooks, events, tracking - and give each a platform use: hooks for telemetry, events for readiness, context for consistent bucketing.
- The strongest argument is migration cost: an adapter change instead of touching every call site. The multi-provider comparison strategy makes it concrete.
- Mention flagd and OFREP to show you know the ecosystem beyond the API.
- Be honest about the limits: lowest-common-denominator features, varying SDK maturity, and that you still need a flag management system and a cleanup process.
- Connect it to OpenTelemetry's feature flag conventions; consistent evaluation telemetry is what makes automated rollouts and incident correlation possible.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
