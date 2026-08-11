---
title: "When do you use a feature flag instead of a canary deployment?"
id: 56
category: "Progressive Delivery and Feature Flags"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# When do you use a feature flag instead of a canary deployment?

**Short answer:** A canary splits _requests_ between two deployed versions of a binary; a flag splits _behaviour_ for chosen users within one version. Use a canary to validate a release - a new binary, a dependency upgrade, a runtime change - and a flag to validate a feature, where you need per-user consistency, targeting, and instant rollback without a redeploy. Mature setups use both: canary the deploy, flag the behaviour.

## Detail

**The mechanism is genuinely different, and everything follows from it.** A canary runs two versions side by side and routes a fraction of traffic to the new one. A user's requests may hit either version, so they can see inconsistent behaviour across a session. A flag runs one version and decides per evaluation, keyed on a stable identifier, so the same user gets the same behaviour every time.

| Property                         | Canary deployment                     | Feature flag                        |
| -------------------------------- | ------------------------------------- | ----------------------------------- |
| Unit of split                    | Requests or pods                      | Users, accounts, or segments        |
| Per-user consistency             | No - a session may see both           | Yes, with stable bucketing          |
| Rollback speed                   | Redeploy or shift traffic             | Seconds, no deploy                  |
| Targeting                        | Not really                            | By attribute, cohort, or account    |
| Catches whole-binary regressions | Yes - the whole version is under test | No - only the flagged path          |
| Code complexity                  | None added                            | A branch that must later be removed |
| Validates infrastructure changes | Yes                                   | No                                  |

**Use a canary when the risk is in the artefact.** A dependency upgrade, a base image change, a runtime version bump, a memory-management change, a rewritten hot path - these can regress in ways no flag covers, because the whole binary differs. Only a canary exercises the new binary as a whole against real traffic.

**Use a flag when the risk is in the behaviour.** A new pricing calculation, a redesigned flow, a different algorithm. You want specific users first, consistency for each user, the ability to target internal staff and beta customers, and rollback in seconds without waiting for a deployment pipeline.

**They compose, and that is the strong answer.** Deploy the new binary as a canary with the new behaviour flagged off. Verify the binary is healthy across all traffic - no memory regression, no latency change - and complete the rollout. Then, separately, ramp the flag to expose the behaviour. Two independent risks, controlled independently, with two independent rollback mechanisms. Conflating them means a bad signal leaves you unsure whether to roll back the deploy or the feature.

**The costs of each.** A flag adds a code branch that must be tested in both states and removed later - real, permanent maintenance until cleanup. A canary requires traffic-splitting infrastructure, enough traffic for a meaningful signal, and version compatibility between the two versions, including any shared database schema.

**Where neither is sufficient.** Anything writing state needs migration discipline regardless of which mechanism you use. Expand-and-contract schema changes, dual writes with a clear source of truth, and idempotent consumers are the actual protection; the rollout mechanism only controls which code path runs.

**The platform's role.** Provide both, make them composable, and default the choice by risk: infrastructure and dependency changes get canary analysis automatically; behavioural changes get a flag with a generated rollout plan. Teams should not be assembling either from scratch.

## Example

```text
The same release, both mechanisms, used for what each is good at.

STEP 1 - CANARY THE BINARY (risk: the artefact)
  checkout v1.4.2 introduces the new pricing engine, flagged OFF, plus a Go
  runtime bump and an updated JSON library.

    5% of requests -> v1.4.2       95% -> v1.4.1
    watching: p99 latency, memory RSS, GC pause, 5xx, CPU
    -> the JSON library upgrade adds 8ms at p99. Caught here, and it could NOT
       have been caught by a flag, because the flagged path is off - the
       regression is in the binary, not the behaviour.
    -> fixed, v1.4.3 canaried, clean, rolled to 100%.

  At this point every request is served by the new binary and behaviour is
  unchanged. Zero customer-visible risk has been taken.

STEP 2 - FLAG THE BEHAVIOUR (risk: the logic)
  Now ramp the flag, on one uniform binary:
    internal -> 1% -> 5% -> 25% -> 100%, per-user consistent, kill switch armed
    watching: pricing reconciliation, conversion, support tickets
    -> a rounding error appears at 5% for one currency. Flag to 0% in seconds.
       No redeploy, and nobody's session flipped mid-checkout.

  Two risks, two mechanisms, two rollback paths. If these had been combined,
  the 8ms latency regression and the rounding error would have appeared in the
  same signal, and the response - roll back the deploy, or the feature? - would
  have been a guess.
```

```text
Choosing, quickly:

  Is the risk in the artefact (deps, runtime, base image, perf)?   -> CANARY
  Is the risk in the behaviour (logic, UX, algorithm)?             -> FLAG
  Do specific users need it first (internal, beta, one account)?   -> FLAG
  Must a given user see consistent behaviour across a session?     -> FLAG
  Do you need rollback in seconds without a pipeline run?          -> FLAG
  Is it an infrastructure change with no code branch to write?     -> CANARY
  Both kinds of risk in one release?                               -> BOTH, in that
                                                                      order
```

## Interview tips

- Open with the mechanism: requests versus behaviour, two versions versus one. Every other difference derives from it, and stating it first structures the whole answer.
- Per-user consistency is the sharpest single differentiator - a canary can show one user both behaviours in a session, which for a checkout flow is a real bug.
- "A canary catches whole-binary regressions a flag cannot" is the argument for canaries that flag enthusiasts miss, and the latency-regression example makes it concrete.
- The compose answer - canary the deploy with the feature off, then ramp the flag - is what interviewers are hoping to hear, and the reason is that it separates two signals that would otherwise be confounded.
- Close by noting neither mechanism protects state. Migration discipline is separate, and saying so pre-empts the follow-up.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
