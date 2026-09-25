---
title: "What can a feature flag not roll back?"
id: 105
category: "Progressive Delivery and Feature Flags"
difficulty: "Advanced"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# What can a feature flag not roll back?

**Short answer:** A flag protects behaviour, not state. Flipping it to 0% stops the new code path for future requests and undoes nothing the new path already did - emails sent, payments captured, events published to other systems, rows written in a new shape, caches poisoned, third-party calls made. Anything with an external side effect needs its own reversibility design, and treating the flag as a rollback mechanism for state is one of the most expensive misunderstandings in progressive delivery.

## Detail

**The distinction that matters: behaviour versus state.** Behaviour is what your code does next, and a flag controls that completely and instantly. State is what has already changed in the world. The flag has no reach into state, and the confidence a flag provides - "we can turn it off in seconds" - is often mistakenly extended to cover consequences it cannot touch.

**The categories, roughly in order of how badly they bite:**

| Side effect                       | Why the flag does not help                        |
| --------------------------------- | ------------------------------------------------- |
| Outbound communication            | The email or push notification has been delivered |
| Payments and financial operations | A capture or refund has settled                   |
| Events published to a bus         | Consumers have already processed them             |
| Calls to third-party APIs         | The external system's state changed               |
| Rows written in a new shape       | The data exists; readers may not understand it    |
| Schema migrations already applied | The old code may not run against the new schema   |
| Poisoned caches                   | Wrong values are being served from cache          |
| Search or analytics indexes       | Documents indexed incorrectly persist             |
| Deleted or overwritten data       | Irreversible without a restore                    |

**The most dangerous one is often the cache.** Turn the flag off and the old code path resumes, but a shared cache now holds values computed by the new path. The bug continues to be served from cache long after the flag is off, which produces the confusing situation where the rollback appears not to have worked.

**Events are the second most dangerous** because the damage is elsewhere. Once a downstream service consumes an event describing a wrongly-priced order, correcting your own state does not correct theirs, and you now have a distributed remediation problem involving teams who were not part of your rollout.

**How to design for reversibility:**

- **Expand and contract for schema changes.** Add columns and write to both shapes, so the old code path remains valid while the new path is in use. Only remove the old shape after the flag is permanently gone.
- **Keep the old path as the source of truth during dual writes.** The new path writes alongside, and you compare rather than trust it, until you deliberately cut over. Reversal is then simply ceasing to read the new data.
- **Make consumers idempotent** so replaying or correcting events is safe.
- **Namespace cache keys by variant.** If the flag affects a cached value, the key must include the variant. The old path then reads its own keys and a rollback is clean.
- **Gate side effects behind a second, separately controlled switch,** so you can enable the new logic while suppressing outbound effects. This lets you run the new path in shadow mode and compare its output before anything leaves the building.
- **Write the remediation runbook before the rollout**, not after. If the new path can mis-price an order, the reconciliation and refund procedure should exist before phase one.

**Shadow mode is the strongest mitigation.** Run the new path, record what it would have done, and compare against the old path's actual output - with no side effects emitted. Most correctness bugs are found with zero customer impact, and the flag rollout that follows carries far less risk.

## Example

```text
A rollback that appeared not to work, and why.

  02:14  pricing-mismatch alert fires at 5% rollout
  02:15  flag set to 0%  -> new pricing code path stops executing
  02:16  wrong totals STILL being reported by support
  02:31  cause: the price cache key was `price:{sku}:{region}` with no variant
         component. Values computed by the new path were cached with a 6h TTL
         and were being served to 100% of users, including everyone the flag
         had never applied to.
  02:34  targeted cache purge - the actual rollback
  02:40  remediation begins for state the flag could never touch:
           412 orders priced by the new engine
             - 97 already captured payment       -> refund run, RB-114
             - 118 confirmation emails sent      -> cannot unsend; correction
                                                    email drafted
             - 412 order.created events published -> downstream fulfilment and
                                                     analytics both consumed them;
                                                     compensating events required
             - rows written with pricing_version=2 -> readers must tolerate both

  The flag did its job perfectly in 60 seconds. It took a further 3 weeks to
  finish undoing the state. That gap is the whole point of this question.
```

```python
# Two switches, not one: the logic and its side effects controlled separately.
# This is what makes shadow mode possible.
def complete_order(order, user):
    ctx = user.flag_ctx

    if flags.enabled("new-pricing-engine", default=False, ctx=ctx):
        total = new_pricing.total(order)
        # Cache key includes the variant, so a rollback does not serve poisoned
        # values to users the flag never applied to.
        cache.set(f"price:v2:{order.sku}:{order.region}", total, ttl=6 * 3600)
    else:
        total = legacy_pricing.total(order)
        cache.set(f"price:v1:{order.sku}:{order.region}", total, ttl=6 * 3600)

    # SEPARATE switch for anything irreversible. Off during shadow and during
    # early ramp phases: the new path runs and is compared, but nothing leaves.
    if flags.enabled("new-pricing-side-effects", default=False, ctx=ctx):
        payments.capture(order, total)
        email.send_confirmation(order, total)
        events.publish("order.created", order, total)
    else:
        shadow.record("new-pricing", order, computed=total,
                      baseline=legacy_pricing.total(order))
    return total
```

```text
The pre-rollout checklist that this question is really asking about:

  For each side effect the new path can produce:
    [ ] is it reversible by flipping the flag?          if no, then:
    [ ] is it suppressible behind a second switch?
    [ ] is the cache key namespaced by variant?
    [ ] is the schema change expand-and-contract, so old code still works?
    [ ] are downstream consumers idempotent?
    [ ] does a written remediation runbook exist BEFORE phase 1?
    [ ] can the new path run in shadow mode and be compared first?

  If more than one box is unchecked, the honest statement is "we can stop this
  quickly, and we cannot undo what it has already done" - which changes how
  aggressively you ramp.
```

## Interview tips

- "A flag protects behaviour, not state" is the sentence. Lead with it and the rest of the answer writes itself.
- Give the list of side effects, and single out the cache as the one that makes a rollback appear to fail. That specific example is memorable and very common.
- Events consumed downstream are the second key example, because they turn your incident into other teams' incidents.
- The two-switch pattern - logic and side effects controlled separately - is the concrete design answer and enables shadow mode.
- Shadow mode as the strongest mitigation, finding correctness bugs at zero customer impact, is the senior recommendation.
- "The remediation runbook exists before phase one" is the discipline point, and it reframes the rollout plan as including its own failure.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
