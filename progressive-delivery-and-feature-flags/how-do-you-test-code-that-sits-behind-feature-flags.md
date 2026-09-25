---
title: "How do you test code that sits behind feature flags?"
id: 98
category: "Progressive Delivery and Feature Flags"
difficulty: "Intermediate"
tags:
  - platform-engineering
  - progressive-delivery-and-feature-flags
  - interview-questions
---

# How do you test code that sits behind feature flags?

**Short answer:** Do not test the combinatorial matrix - with n flags there are 2^n states and it is hopeless. Test all flags at their current production values, plus the single flag under change flipped in both directions. That covers what you are actually changing against the configuration it will actually meet, and it is a fixed amount of work regardless of how many flags exist.

## Detail

**Why the matrix is a trap.** Twenty flags means over a million combinations. Teams that attempt exhaustive coverage either give up or build a suite so slow that it is disabled. Worse, the exhaustive framing distracts from the far more likely failure: the new path was tested with every flag off, and production has fourteen of them on.

**The strategy that works.** Pin the test configuration to production's actual flag values, then vary only the flag under change. Two runs: production configuration with the new flag off, and production configuration with it on. Both must pass before merge. That is the realistic definition of "does this work".

**Fetch the production flag values into CI.** This is the mechanism that makes the strategy real - a step that pulls the current production configuration and uses it as the test baseline. Without it, teams hardcode defaults, drift from production, and get exactly the surprise the strategy was meant to prevent.

**Both branches need coverage, and this is where teams quietly cheat.** The old path is still serving most traffic and must keep working; the new path is why you are here. A merge that only tests the new branch means the rollback path is untested - which you discover at the worst moment. Coverage reporting per branch, not just overall, is what catches this.

**Known interactions get explicit tests.** Some flag pairs genuinely interact - a new checkout flow and a new pricing engine, for example. Those combinations are worth naming in the registry and testing deliberately. The point is that this is a short, curated list derived from knowledge, not a generated matrix.

**Integration and end-to-end tests should run against the production configuration too**, with the new flag enabled in a dedicated run. A staging environment whose flag values differ from production is testing a system that does not exist, which is one of the most common sources of "it worked in staging".

**Verify the default is safe.** Every flag has a call-site default used when the provider is unreachable. There should be a test that evaluates with the provider unavailable and asserts the safe path is taken - because that behaviour will occur in production eventually and is usually never exercised.

**The platform's contribution.** Provide a test harness that fetches production flag values (on OpenFeature, an in-memory provider loaded with those values means unit tests need no network and no mocked vendor SDK), a fixture that runs a test body under both states of a named flag, coverage reporting per branch, and a CI gate requiring both. Otherwise each team invents its own approach and most will test only the happy path.

## Example

```python
# The strategy in code: production values as the baseline, one flag varied.
import pytest
from platform_flags.testing import production_flags, with_flag

@pytest.fixture
def prod_config():
    # Fetched from the provider in CI, not hardcoded. This is what stops the
    # test suite drifting away from the configuration production actually has.
    return production_flags(environment="production")

# Runs the whole test body twice - flag off and flag on - against production's
# values for every OTHER flag.
@with_flag("checkout-new-pricing-engine", states=[False, True])
def test_checkout_total(prod_config, flag_state):
    order = make_order(items=[("sku-1", 2), ("sku-2", 1)], region="eu")
    total = checkout.complete(order, user=beta_user())

    if flag_state:
        assert total == Decimal("41.97")      # new engine: rounds per line
    else:
        assert total == Decimal("41.98")      # legacy: rounds the sum

    # Invariants that must hold in BOTH states - the most valuable assertions,
    # because they are what a rollback depends on.
    assert total > 0
    assert order.audit_trail.pricing_version in (1, 2)
    assert order.currency == "EUR"
```

```python
# The default-safety test that is almost always missing.
def test_safe_default_when_provider_unreachable(monkeypatch):
    monkeypatch.setattr("platform_flags.provider", UnreachableProvider())

    order = make_order(items=[("sku-1", 1)], region="eu")
    total = checkout.complete(order, user=beta_user())

    # With no provider, evaluation must fall to the call-site default and take
    # the legacy path - never raise, never hang, never pick the new path.
    assert order.audit_trail.pricing_version == 1
    assert total == Decimal("13.99")
```

```text
The CI gate, and the arithmetic that justifies the strategy:

  $ platform flags test-plan --changed-flag checkout-new-pricing-engine

  flags currently ON in production ......... 14
  flags currently OFF in production ........ 23
  total flags .............................. 37
  exhaustive combinations .................. 137,438,953,472     <- not a plan

  TEST PLAN (2 runs + 1 + 1)
    run 1  production config, checkout-new-pricing-engine = OFF   [rollback path]
    run 2  production config, checkout-new-pricing-engine = ON    [new path]
    run 3  provider unreachable -> assert safe default
    run 4  declared interaction: + checkout-new-flow = ON
             (from the registry's `interacts_with` field - a curated list,
              not a generated matrix)

  BRANCH COVERAGE
    new path ....... 94%   ✓
    legacy path .... 41%   ✗ FAIL - the rollback path is under-tested.
                            This is the check that catches the common cheat of
                            testing only the branch you just wrote.
```

## Interview tips

- Give the arithmetic. Saying "twenty flags is over a million combinations, so the matrix is not a strategy" immediately establishes that you have thought about this properly.
- The rule to state plainly: production values for everything else, both states for the flag under change.
- Fetching production flag values into CI is the mechanism that makes it real, and it is what most candidates omit.
- Insisting on coverage for the old branch, because that is the rollback path, is the highest-value practical point.
- The unreachable-provider default-safety test is a strong detail - that code path will run in production and is almost never exercised.
- Mention that invariants holding in both states are the most valuable assertions, since they are precisely what a rollback relies on.

---

[⬅ Back to Progressive Delivery and Feature Flags](./README.md) · [All topics](../README.md)
