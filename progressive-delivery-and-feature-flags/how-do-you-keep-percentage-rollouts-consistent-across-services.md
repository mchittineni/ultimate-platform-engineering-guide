---
title: "How do you keep percentage rollouts consistent across services?"
id: 57
category: "Progressive Delivery and Feature Flags"
difficulty: "Advanced"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# How do you keep percentage rollouts consistent across services?

**Short answer:** Bucket on a stable identifier with the same hash function and the same salt in every service, and propagate the evaluation context with the request rather than reconstructing it per service. Otherwise a user can be inside the rollout in the checkout service and outside it in the pricing service - which produces a genuinely broken experience that looks like a bug and is very hard to reproduce.

## Detail

**How percentage bucketing works.** The SDK hashes a bucketing key together with the flag key and a salt, maps the result into a fixed range, and compares that to the rollout percentage. Because it is deterministic, the same inputs always produce the same bucket - which is what makes a percentage rollout sticky for a user rather than random per request.

**The three ways it goes wrong across services:**

- **Different bucketing keys.** One service buckets on user ID, another on account ID, another on session ID. The same request is then evaluated against different identities.
- **Different salts.** The same key with a different salt hashes to a different bucket. Since a salt is often per-environment or per-provider-project, this happens quietly when two services are configured against different projects.
- **Reconstructed context.** A downstream service that looks up the user itself may get a stale or different attribute - a plan tier that changed, a country resolved differently - and evaluate a targeting rule differently.

**Propagate the context; do not rebuild it.** The evaluation context should be established once at the edge and travel with the request as a header, alongside your trace context. Downstream services evaluate flags against the propagated context. This also gives you a single place to enforce that the bucketing key is present and correctly scoped.

**Never bucket on session ID for anything user-facing.** A new session means a new bucket, so a user flickers between variants across visits. For experiments this destroys the measurement; for features it looks like an intermittent bug.

**Bucket on the account for business-to-business products.** Consistency matters at the level the customer perceives. Two colleagues in the same company seeing different behaviour is a support ticket regardless of how correct your percentage is.

**Sticky assignment for experiments.** Persist the assignment for the experiment's duration rather than recomputing it, so a change to the rollout percentage or to the salt does not reassign users mid-experiment. Reassignment invalidates the results and is easy to do accidentally.

**Sample ratio mismatch is the health check.** If a 50/50 split is observed as 47/53 with enough traffic to make that significant, something is wrong - inconsistent bucketing, an evaluation error biasing one arm, or lost telemetry from one variant. Checking the observed split against the intended one catches broken bucketing before you draw conclusions from a broken experiment. It is the single most useful automated check in this area.

**The platform owns all of this.** The bucketing key, the salt, the propagation header, and the sample-ratio check belong in the shared SDK wrapper and the shared middleware, not in each team's code. Consistency is not something forty teams will independently achieve.

## Example

```text
The failure, concretely. One request, two services, two answers.

  user 4821 -> web-bff -> checkout -> pricing

  checkout    buckets on user_id=4821, salt="prod-2026"    -> bucket 0412 -> IN (5%)
  pricing     buckets on session_id=a9f3..., salt="pricing-project"
                                                            -> bucket 8817 -> OUT

  Result: the new checkout UI displays a total from the OLD pricing engine.
  The user sees a wrong price. The logs show both services behaving "correctly"
  according to their own evaluation, and the bug does not reproduce for anyone
  whose session hashes into the same side.

  Two distinct causes in one example: a different bucketing key AND a different
  salt. Either alone is enough.
```

```python
# Platform middleware: establish the context once at the edge, propagate it.
# Downstream services never reconstruct it.

# --- edge (web-bff) ---
def build_flag_context(request):
    ctx = {
        # ONE canonical bucketing key for the whole estate. For B2B products this
        # is account_id, so colleagues never see different behaviour.
        "targetingKey": f"user:{request.user.id}",
        "accountId": request.user.account_id,
        "plan": request.user.plan,          # snapshotted here, not re-fetched
        "country": request.geo.country,
    }
    request.headers["x-flag-context"] = b64(json.dumps(ctx))
    return ctx

# --- downstream (checkout, pricing) ---
def flag_context(request):
    # Read the propagated context. Do NOT look the user up again - a re-fetch
    # can see a changed plan or a differently resolved country, and then the
    # targeting rules diverge between services.
    return json.loads(unb64(request.headers["x-flag-context"]))
```

```yaml
# One salt for the estate, held by the platform, identical in every service.
# A per-service or per-project salt is the quiet cause of cross-service skew.
apiVersion: v1
kind: ConfigMap
metadata: { name: platform-flag-config, namespace: platform }
data:
  bucketing.yaml: |
    # hash(flagKey + salt + targetingKey) -> 0..9999
    salt: "prod-2026-08"          # rotate ONLY with a deliberate reassignment plan
    hash: murmur3_32
    buckets: 10000
    bucketing_key: accountId      # B2B: the account is the unit of consistency
    sticky_experiments: true      # persist assignment for the experiment's life
```

```text
Sample ratio mismatch - the check that catches broken bucketing before it
corrupts a decision:

  $ platform flags srm-check cart-experiment-b

    intended split     50.0 / 50.0
    observed split     47.3 / 52.7      n = 184,220
    chi-square p       0.0003            <-- significant. This is not noise.

    likely causes, in order of frequency:
      1. inconsistent bucketing key between services
      2. one variant erroring before telemetry is emitted (losing its events)
      3. a mid-experiment salt or percentage change reassigning users

    -> experiment results are NOT trustworthy. Do not ship on this data.
```

## Interview tips

- Explain the mechanism first - hash of flag key plus salt plus bucketing key, mapped into a range - because the failures are all violations of one of those three inputs.
- The cross-service example with a wrong price displayed is the memorable version. Two services, both "correct" locally, one broken user experience.
- "Propagate the context, do not reconstruct it" is the concrete fix, and the reason - a re-fetch can see changed attributes - is the part that shows depth.
- Never bucket on session ID, and bucket on account for B2B. Both are short, specific, and frequently got wrong.
- Sample ratio mismatch is the highest-value thing to name. It is the automated check that tells you your bucketing is broken before you make a decision on corrupted data.
- Close on ownership: the salt, the key, the propagation header, and the SRM check belong in the platform, because forty teams will not independently converge.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
